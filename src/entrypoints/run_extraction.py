"""Trích xuất tri thức từ các chunk PENDING trong staging_chunks.db rồi ghi vào Neo4j (hỗ trợ đa luồng).

Chạy: python -m src.entrypoints.run_extraction
"""
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import threading
import time

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


def main(
    provider: str = "ollama",
    model: str | None = "beam:cloud",
    limit: int | None = None,
    max_workers: int = 2,
    max_retries: int = 3,
    sleep_time: float = 0.0,
    relation_classes: Sequence[type[BaseRelation]] | None = None,
) -> None:
    """Chạy quy trình trích xuất đồ thị tri thức từ SQLite staging sang Neo4j.

    Args:
        provider: "openai" | "groq" | "ollama" | "google"
        model: Tên model cụ thể (None để dùng model mặc định của provider)
        limit: Số lượng chunk cần xử lý (None để chạy hết các chunk PENDING)
        max_workers: Số luồng chạy song song
        max_retries: Số lần thử lại tối đa trước khi đánh dấu chunk là FAILED
        sleep_time: Thời gian nghỉ (giây) giữa các lần xử lý của mỗi worker
        relation_classes: Danh sách các lớp quan hệ cần trích xuất (mặc định lấy DEFAULT_RELATION_CLASSES)
    """
    if relation_classes is None:
        relation_classes = DEFAULT_RELATION_CLASSES

    repo = build_chunk_repository()
    usecase = build_usecase(provider, model)
    actual_model = model or getattr(getattr(usecase, "_extractor", None), "_model", None) or "unknown"

    try:
        chunks = repo.fetch_pending(limit)
        total = len(chunks)
        print(f"[*] Có {total} chunk cần xử lý với {max_workers} workers (provider={provider}, model={actual_model}).")
        if total == 0:
            return

        ok_count = 0
        fail_count = 0
        done_counter = 0
        counter_lock = threading.Lock()

        def process_chunk(chunk_id: str, text: str) -> None:
            nonlocal ok_count, fail_count, done_counter
            try:
                result = usecase.execute(text, relation_classes, chunk_id=chunk_id)
                # Cập nhật nhà cung cấp, model và kết quả trích xuất vào SQLite
                repo.update_provider(chunk_id, provider)
                repo.update_model(chunk_id, actual_model)
                repo.mark_completed(chunk_id, result.model_dump(mode="json"))
                with counter_lock:
                    ok_count += 1
                    done_counter += 1
                    idx = done_counter
                print(f"[{idx}/{total}] OK {chunk_id}: {len(result.relations)} quan hệ")
            except Exception as e:
                repo.update_provider(chunk_id, provider)
                repo.update_model(chunk_id, actual_model)
                status = repo.mark_failed(chunk_id, max_retries)
                with counter_lock:
                    fail_count += 1
                    done_counter += 1
                    idx = done_counter
                print(f"[{idx}/{total}] LỖI {chunk_id} -> {status}: {e}")
            if sleep_time > 0:
                time.sleep(sleep_time)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_chunk, cid, txt) for cid, txt in chunks]
            try:
                for f in as_completed(futures):
                    f.result()
            except KeyboardInterrupt:
                print("\n[!] Nhận tín hiệu dừng từ người dùng (Ctrl+C). Đang hủy các tác vụ còn lại...")
                executor.shutdown(wait=False, cancel_futures=True)
                raise

        print(f"\n[HOÀN TẤT] Thành công={ok_count}, Lỗi={fail_count} / Tổng={total}")
    finally:
        usecase.close()


if __name__ == "__main__":
    main()
