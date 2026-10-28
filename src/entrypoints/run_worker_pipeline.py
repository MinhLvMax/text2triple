"""Pipeline trích xuất động theo cơ chế Claim-and-Process (Task Leasing) đa nền tảng.

Mỗi worker sẽ:
1. Lấy đúng 1 chunk đang ở trạng thái PENDING và lập tức chuyển thành PROCESSING.
2. Gọi UseCase trích xuất quan hệ và nạp vào Neo4j.
3. Cập nhật provider, model và đánh dấu COMPLETED (hoặc FAILED / quay lại PENDING nếu lỗi).
4. Nghỉ sleep_time theo giới hạn rate limit riêng của từng model/nhà cung cấp.

Hàm `main()` bên dưới khởi chạy song song 2 worker trên 2 nền tảng khác nhau cùng lúc
(ví dụ: Google AI Studio và Groq), cùng nhau rút cạn hàng đợi SQLite staging_chunks.db
mà không lo bị trùng lặp chunk hay nghẽn rate limit.

Chạy trực tiếp:
    python -m src.entrypoints.run_worker_pipeline
"""
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import threading
import time
from typing import Optional, Dict, Any

# Đảm bảo in tiếng Việt chuẩn trên Windows terminal (tránh lỗi CP1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.bootstrap import build_chunk_repository, build_usecase
from src.domain.extraction_schema.relations import (
    BaseRelation,
    BanHanhRelation, DanDenRelation, DienRaTaiRelation, DienRaVaoRelation, KeViRelation,
    LanhDaoRelation, SuDungRelation, ThamGiaRelation, ThanhLapRelation, ThuocVeRelation,
)

DEFAULT_RELATION_CLASSES: list[type[BaseRelation]] = [
    LanhDaoRelation, SuDungRelation, DienRaTaiRelation, ThamGiaRelation,
    ThanhLapRelation, BanHanhRelation, KeViRelation, ThuocVeRelation,
    DanDenRelation, DienRaVaoRelation,
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("worker_pipeline")


def run_pipeline(
        provider: str = "google",
        model: Optional[str] = None,
        limit: Optional[int] = None,
        max_workers: int = 1,
        max_retries: int = 3,
        sleep_time: float = 0.0,
        reset_stale: bool = False,
        worker_name: Optional[str] = None,
        relation_classes: Optional[Sequence[type[BaseRelation]]] = None,
        repo: Optional[Any] = None,
) -> Dict[str, int]:
    """Hàm chạy pipeline trích xuất tri thức với cơ chế Claim-and-Process.

    Args:
        provider: "google" | "groq" | "ollama" | "openai"
        model: Tên model cụ thể (None để dùng model mặc định của provider)
        limit: Giới hạn tổng số chunk mà worker này sẽ xử lý (None = chạy đến khi hết chunk PENDING)
        max_workers: Số luồng worker song song cho riêng cấu hình này
        max_retries: Số lần thử lại tối đa trước khi đánh dấu chunk là FAILED
        sleep_time: Thời gian nghỉ (giây) giữa 2 lần xử lý của mỗi worker (kiểm soát Rate Limit)
        reset_stale: Nếu True, sẽ khôi phục tất cả các chunk đang kẹt ở PROCESSING về PENDING trước khi chạy
        worker_name: Tên định danh hiển thị trên console (mặc định lấy theo provider:model)
        relation_classes: Danh sách các lớp quan hệ cần trích xuất (mặc định lấy DEFAULT_RELATION_CLASSES)
        repo: ChunkRepository dùng chung (nếu None sẽ tự khởi tạo)

    Returns:
        dict: Thống kê số lượng {"completed": ok_count, "failed": fail_count, "processed": total}
    """
    if relation_classes is None:
        relation_classes = DEFAULT_RELATION_CLASSES

    if repo is None:
        repo = build_chunk_repository()

    # Khôi phục các chunk bị kẹt từ phiên chạy trước nếu yêu cầu
    if reset_stale:
        stale_count = repo.reset_processing_to_pending()
        if stale_count > 0:
            print(f"[*] Đã khôi phục {stale_count} chunk đang kẹt 'PROCESSING' về 'PENDING'.")

    usecase = build_usecase(provider, model)
    actual_model = model or getattr(getattr(usecase, "_extractor", None), "_model", None) or "unknown"
    tag = worker_name or f"{provider}:{actual_model}"

    print(
        f"[*] Khởi động [{tag}]: limit={limit if limit is not None else 'Không giới hạn'}, "
        f"workers={max_workers}, sleep={sleep_time}s"
    )

    processed_counter = 0
    ok_count = 0
    fail_count = 0
    counter_lock = threading.Lock()
    stop_signal = threading.Event()

    def worker_loop(sub_id: int) -> None:
        nonlocal processed_counter, ok_count, fail_count
        worker_label = f"{tag}#{sub_id}" if max_workers > 1 else tag

        while not stop_signal.is_set():
            # Kiểm tra xem đã đạt giới hạn limit chưa
            with counter_lock:
                if limit is not None and processed_counter >= limit:
                    break

            # 1. Bốc đúng 1 chunk PENDING và chuyển ngay sang PROCESSING (Atomic)
            claimed = repo.claim_next_pending()
            if not claimed:
                # Không còn chunk nào PENDING trong CSDL
                break

            chunk_id, text = claimed

            with counter_lock:
                processed_counter += 1
                curr_idx = processed_counter

            print(f"[{worker_label}][#{curr_idx}] Nhận {chunk_id} -> Đang xử lý (PROCESSING)...")

            # 2. Thực hiện trích xuất qua UseCase
            try:
                result = usecase.execute(text, relation_classes, chunk_id=chunk_id)
                # 3. Thành công: Cập nhật thông tin và đổi trạng thái COMPLETED
                repo.update_provider(chunk_id, provider)
                repo.update_model(chunk_id, actual_model)
                repo.mark_completed(chunk_id, result.model_dump(mode="json"))

                with counter_lock:
                    ok_count += 1
                print(f"[{worker_label}][#{curr_idx}] OK {chunk_id}: {len(result.relations)} quan hệ -> COMPLETED")
            except Exception as e:
                # 4. Thất bại: Cập nhật thông tin và tăng retry_count (PENDING hoặc FAILED)
                repo.update_provider(chunk_id, provider)
                repo.update_model(chunk_id, actual_model)
                status = repo.mark_failed(chunk_id, max_retries)

                with counter_lock:
                    fail_count += 1
                print(f"[{worker_label}][#{curr_idx}] LỖI {chunk_id} -> {status}: {e}")

            # 5. Nghỉ theo rate limit
            if sleep_time > 0 and not stop_signal.is_set():
                time.sleep(sleep_time)

    try:
        if max_workers <= 1:
            worker_loop(sub_id=1)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(worker_loop, wid) for wid in range(1, max_workers + 1)]
                for f in as_completed(futures):
                    f.result()
    except KeyboardInterrupt:
        print(f"\n[!] Nhận tín hiệu dừng từ người dùng (Ctrl+C). Đang dừng [{tag}]...")
        stop_signal.set()
    finally:
        usecase.close()

    print(
        f"[KẾT THÚC {tag}] -> Hoàn thành={ok_count}, Lỗi={fail_count}, Tổng xử lý={processed_counter}"
    )
    return {"completed": ok_count, "failed": fail_count, "processed": processed_counter}


def main() -> None:
    """Khởi chạy đồng thời khoảng 2 worker trên 2 nền tảng khác nhau."""
    repo = build_chunk_repository()

    # 1. Tự động khôi phục các chunk bị kẹt ở PROCESSING từ lần chạy trước về PENDING
    stale_count = repo.reset_processing_to_pending()
    if stale_count > 0:
        print(f"[*] Đã khôi phục {stale_count} chunk bị kẹt 'PROCESSING' về 'PENDING'.")

    # 2. Định nghĩa cấu hình 2 Worker chạy song song với model và nền tảng khác nhau:
    worker_configs = [
        # {
        #     "worker_name": "Worker-Google",
        #     "provider": "google",
        #     "model": "gemini-3.1-flash-lite",
        #     "sleep_time": 20.0,  # Khoảng 15 RPM để nằm trong Free Tier an toàn
        #     "limit": None,      # None = chạy đến khi hết việc
        #     "max_workers": 1,
        # },
        # {
        #     "worker_name": "Worker-Groq",
        #     "provider": "groq",
        #     "model": "openai/gpt-oss-120b",
        #     "sleep_time": 5.0,  # Groq xử lý rất nhanh, nghỉ ngắn
        #     "limit": None,
        #     "max_workers": 1,
        # },
        {
            "worker_name": "Worker-Ollama",
            "provider": "ollama",
            "model": "beam:cloud",
            "sleep_time": 0.0,
            "limit": None,
            "max_workers": 1,
        },
        # {
        #     "worker_name": "Worker-Ollama-1",
        #     "provider": "ollama",
        #     "model": "nemotron-3-super",
        #     "sleep_time": 0.0,
        #     "limit": None,
        #     "max_workers": 1,
        # },
        # {
        #     "worker_name": "Worker-Ollama-2",
        #     "provider": "ollama",
        #     "model": "deepseek-v4.1-flash:cloud",
        #     "sleep_time": 0.0,
        #     "limit": None,
        #     "max_workers": 1,
        # },
        # {
        #     "worker_name": "Worker-Openai",
        #     "provider": "openai",
        #     "model": "gpt-5.6-luna",
        #     "sleep_time": 1.0,
        #     "limit": None,
        #     "max_workers": 1,
        # },
    ]

    print(f"[*] Bắt đầu chạy song song {len(worker_configs)} worker đa nền tảng...")

    threads: list[threading.Thread] = []
    for cfg in worker_configs:
        t = threading.Thread(
            target=run_pipeline,
            kwargs={
                "provider": cfg["provider"],
                "model": cfg.get("model"),
                "limit": cfg.get("limit"),
                "max_workers": cfg.get("max_workers", 1),
                "sleep_time": cfg.get("sleep_time", 0.0),
                "reset_stale": False,
                "worker_name": cfg.get("worker_name"),
                "repo": repo,
            },
            name=cfg["worker_name"],
            daemon=True,
        )
        threads.append(t)
        t.start()

    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(timeout=0.5)
    except KeyboardInterrupt:
        print("\n[!] Nhận tín hiệu dừng từ người dùng (Ctrl+C). Đang dừng các worker...")

    print("[*] Hoàn tất toàn bộ các luồng worker.")


if __name__ == "__main__":
    main()
