import sys
from typing import Optional

# CHỈ import từ Application/Domain, TUYỆT ĐỐI KHÔNG import Bootstrap hay Infrastructure
from src.application.usecases.extract import InformationExtractionUseCase


class CLIApp:
    """
    Giao diện dòng lệnh (Command Line Interface).
    Nhận Use Case từ bên ngoài thông qua Constructor Injection.
    """

    def __init__(self, extraction_usecase: InformationExtractionUseCase):
        self._usecase = extraction_usecase

    def run(self) -> None:
        """Vòng lặp tương tác chính với người dùng"""
        print("=" * 60)
        print(" CHƯƠNG TRÌNH TRÍCH XUẤT ĐỒ THỊ TRI THỨC LỊCH SỬ (CLI)")
        print("=" * 60)

        while True:
            try:
                print("\n[Lựa chọn mô hình LLM]")
                print("1. gpt-4o-mini (Nhanh, tiết kiệm - Mặc định)")
                print("2. gpt-4o (Phân tích sâu, chính xác cao)")
                print("3. Tự nhập model khác")
                print("0. Thoát chương trình")

                choice = input("Mời bạn chọn (0-3) [1]: ").strip() or "1"

                if choice == "0":
                    print("\nĐang thoát chương trình. Tạm biệt!")
                    break

                selected_model = self._resolve_model(choice)
                print(f"-> Đã chọn model: [{selected_model}]")

                # Nhập thông tin đoạn văn bản
                chunk_id = input("\nNhập mã Chunk ID (bỏ trống để tự sinh hash): ").strip() or None
                print("Nhập đoạn văn bản lịch sử (Nhấn Enter hai lần hoặc gõ 'END' ở dòng mới để hoàn tất):")

                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    if not line and lines and not lines[-1]:  # Nhấn Enter 2 lần liên tiếp
                        lines.pop()
                        break
                    lines.append(line)

                text = "\n".join(lines).strip()
                if not text:
                    print("[!] Lỗi: Nội dung văn bản không được để trống. Vui lòng nhập lại.")
                    continue

                # Thực thi Use Case và truyền model người dùng chọn từ CLI
                print(f"\n[*] Đang gửi văn bản tới LLM ({selected_model}) và nạp vào Neo4j...")
                result = self._usecase.execute(
                    text=text,
                    chunk_id=chunk_id,
                    model_name=selected_model
                )

                # Hiển thị kết quả trích xuất
                self._display_result(result)

            except KeyboardInterrupt:
                print("\n\nĐã nhận lệnh ngắt từ bàn phím. Đang thoát...")
                break
            except Exception as e:
                print(f"\n[X] Đã xảy ra lỗi: {e}")

    def _resolve_model(self, choice: str) -> str:
        if choice == "1":
            return "gpt-4o-mini"
        elif choice == "2":
            return "gpt-4o"
        elif choice == "3":
            custom = input("Nhập tên model chính xác (VD: gpt-3.5-turbo): ").strip()
            return custom if custom else "gpt-4o-mini"
        return "gpt-4o-mini"

    def _display_result(self, result) -> None:
        print("\n" + "-" * 50)
        print(f"KẾT QUẢ TRÍCH XUẤT CHO CHUNK: {result.chunk_id}")
        print("-" * 50)

        print(f"\n[+] Danh sách Thực thể ({len(result.entities)} entities):")
        for idx, e in enumerate(result.entities, 1):
            print(f"  {idx}. [{e.type}] {e.name}: {e.description}")

        print(f"\n[+] Danh sách Quan hệ ({len(result.relationships)} relationships):")
        for idx, r in enumerate(result.relationships, 1):
            print(f"  {idx}. ({r.source}) --[{r.relation}]--> ({r.target})")
            if hasattr(r, 'evidence') and r.evidence:
                print(f"      Dẫn chứng: \"{r.evidence}\"")

        print("\n[OK] Đã hoàn tất ghi dữ liệu vào cơ sở dữ liệu Neo4j!")