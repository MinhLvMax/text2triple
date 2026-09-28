import pymupdf
import json
import os
import tempfile
from pathlib import Path
from underthesea import word_tokenize, ner, sent_tokenize
from src.config import Config
import pandas as pd
import numpy as np

HISTORICAL_KNOWLEDGE_PATH = Config.DATA_DIR / 'historical_knowledge'


def read_json(file_path, encoding="utf-8"):
    with open(file_path, "r", encoding=encoding) as f:
        return json.load(f)


def list_file_paths(folder_path, recursive=False):
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Thư mục không tồn tại: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Đường dẫn không phải thư mục: {folder}")

    paths = folder.rglob("*") if recursive else folder.glob("*")
    return [path for path in paths if path.is_file()]


def _json_default(obj):
    '''Chuyển kiểu numpy sang kiểu Python thuần cho json'''
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Không serialize được kiểu {type(obj).__name__}")


def write_json(data, file_path, encoding="utf-8", indent=2):
    file_path = Path(file_path)
    fd, tmp_path = tempfile.mkstemp(dir=file_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False,
                      indent=indent, default=_json_default)
        os.replace(tmp_path, file_path)  # atomic: chỉ thay khi ghi xong
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def sentence_statistics(folder_path):
    '''Thống kê độ dài câu bằng pandas'''
    book_files = list_file_paths(folder_path)

    records = []
    for file in book_files:
        book_data = read_json(file_path=file)
        pages = book_data.get('pages', {})
        for number, page in pages.items():
            for sentence in page.get('sentences', []):
                if not sentence.strip():
                    continue
                records.append({
                    'file': file.name,
                    'page': number,
                    'sentence': sentence,
                    'word_count': len(sentence.split()),
                    'char_count': len(sentence),
                })

    df = pd.DataFrame(records)
    if df.empty:
        print("Không có câu nào để thống kê.")
        return df

    # Thống kê tổng quan
    print(df[['word_count', 'char_count']].describe())

    # Câu ngắn nhất / dài nhất theo số từ
    shortest = df.loc[df['word_count'].idxmin()]
    longest = df.loc[df['word_count'].idxmax()]

    print(f"\nCâu ngắn nhất: {shortest['word_count']} từ "
          f"(file: {shortest['file']}, trang {shortest['page']})")
    print(f"  → {shortest['sentence']}")
    print(f"\nCâu dài nhất: {longest['word_count']} từ "
          f"(file: {longest['file']}, trang {longest['page']})")
    print(f"  → {longest['sentence'][:200]}...")

    # Cảnh báo câu có nguy cơ vượt giới hạn 512 token của BERT
    MODEL_TOKEN_LIMIT = 512
    WORD_WARN_THRESHOLD = 300  # ngưỡng an toàn (số token thật > số từ)
    over_threshold = df[df['word_count'] > WORD_WARN_THRESHOLD]
    print(f"\nSố câu > {WORD_WARN_THRESHOLD} từ "
          f"(nguy cơ vượt {MODEL_TOKEN_LIMIT} token): {len(over_threshold)}")
    if not over_threshold.empty:
        print(over_threshold[['file', 'page', 'word_count']]
              .sort_values('word_count', ascending=False))

    return df


def ocr_page(pdf_path, json_path):
    '''ORC tài liệu pdf scan'''
    book_data = read_json(json_path)
    json_pages = book_data.get("pages", {})

    with pymupdf.open(pdf_path) as doc:
        for page_key, page_json in json_pages.items():
            # Bỏ qua trang đã có text.
            if page_json.get("text", "").strip():
                continue

            page_number = int(page_json.get("page_number", page_key))
            print(f'Đang OCR trang {page_number}/{doc.page_count}')
            pdf_page_index = page_number - 1
            page_pdf = doc.load_page(pdf_page_index)
            text_page = page_pdf.get_textpage_ocr(
                language='vie',
                dpi=400
            )
            text_string = page_pdf.get_text(textpage=text_page)
            page_json['text'] = text_string
    write_json(
        data=book_data,
        file_path=json_path
    )


def word_segmentation(json_path):
    '''Cắt từ update thuộc tính word của page cho 1 sách'''
    print(json_path)
    book_data = read_json(json_path)
    pages: dict = book_data.get('pages', {})

    skipped = 0  # đếm số câu bị bỏ qua do lỗi
    for number, page in pages.items():
        print(f'{number}/{len(pages)}')

        if 'words' in page:
            print(f"Bỏ qua trang {number}: đã tách từ rồi")
            continue

        text_of_page = page.get('text', '')
        if not text_of_page.strip():
            page["words"] = []
            print(f"Bỏ qua trang {number}: text rỗng")
            continue

        page_entities = []
        for sentence in page['sentences']:
            if not sentence.strip():
                continue
            try:
                page_entities.extend(ner(sentence, format='json', deep=True))
            except Exception as e:
                skipped += 1
                print(f"  Lỗi NER (trang {number}), bỏ qua câu: {e}")
                print(f"    → {sentence[:100]}...")
                continue
        page['words'] = page_entities
        write_json(
            data=book_data,
            file_path=json_path
        )
    if skipped:
        print(f"Tổng số câu bị bỏ qua trong {Path(json_path).name}: {skipped}")


def word_segmentation_folder(folder_path):
    '''Cắt từ update thuộc tính word của page cho 15 sách'''
    book_paths = list_file_paths(folder_path)
    for book_path in book_paths:
        word_segmentation(
            json_path=book_path
        )


def sentence_segmentation(folder_path):
    '''Chia đoạn thành các câu'''
    book_files = list_file_paths(folder_path)
    for file in book_files:
        print(f'Đang xử lý tách câu {file}')
        book_data = read_json(
            file_path=file
        )

        pages = book_data.get('pages', {})
        for number, page in pages.items():
            text: str = page.get('text', '')
            if not text.strip():
                page['sentences'] = []
                continue
            sentences = sent_tokenize(text.replace('\n', ' '))
            page['sentences'] = sentences if sentences else []

        write_json(
            file_path=file,
            data=book_data
        )


def clean_words_key(json_path, key='words'):
    '''Xóa key thừa (mặc định 'words') khỏi mọi page của 1 sách'''
    json_path = Path(json_path)
    book_data = read_json(json_path)
    pages: dict = book_data.get('pages', {})

    removed = 0
    for number, page in pages.items():
        if key in page:
            del page[key]
            removed += 1

    if removed:
        write_json(data=book_data, file_path=json_path)
        print(f"{json_path.name}: đã xóa '{key}' ở {removed} trang")
    else:
        print(f"{json_path.name}: không có key '{key}' nào để xóa")
    return removed


def clean_words_key_folder(folder_path, key='words'):
    '''Xóa key thừa khỏi mọi page của cả 15 tập trong folder'''
    book_paths = list_file_paths(folder_path)
    total = 0
    for book_path in book_paths:
        total += clean_words_key(json_path=book_path, key=key)
    print(f"Tổng cộng đã xóa '{key}' ở {total} trang trên {len(book_paths)} sách")


if __name__ == '__main__':
    '''Gọi các hàm trong script'''

    # Đoạn mã tạo code tên biến các path sách
    # book_paths = list_file_paths(HISTORICAL_KNOWLEDGE_PATH)
    # i = 1
    # for path in book_paths:
    #     path = Path(path)
    #     print(f'tap_{i}_json_path = HISTORICAL_KNOWLEDGE_PATH / "{path.name}"')
    #     i += 1

    # Các path của từng tập
    tap_1_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 01 Từ khởi thủy đến thế kỷ X-Cao Duy Mến-2013.json"
    tap_2_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 02 Từ thế kỷ X đến thế kỷ XIV-Trần Thị Vinh-2014.json"
    tap_3_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 03 Từ thế kỷ XV đến thế kỷ XVI-Tạ Ngọc Liễn-2017.json"
    tap_4_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 04 Từ thế kỷ XVII đến thế kỷ XVIII-Trần Thị Vinh-2017.json"
    tap_5_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 05 Từ năm 1802 đến năm 1858-Trương Thị Yến-2017.json"
    tap_6_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 06 Từ năm 1858 đến năm 1896-Võ Kim Cương-2017.json"
    tap_7_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 07 Từ năm 1897 đến năm 1918-Tạ Thị Thúy-2017.json"
    tap_8_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 08 Từ năm 1919 đến năm 1930-Tạ Thị Thúy-2017.json"
    tap_9_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 09 Từ năm 1930 đến năm 1945-Tạ Thị Thúy-2017.json"
    tap_10_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 10 Từ năm 1945 đến năm 1950-Đinh Thị Thu Cúc-2017.json"
    tap_11_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 11 Từ năm 1951 đến năm 1954-Nguyễn Văn Nhật-2017.json"
    tap_12_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 12 Từ năm 1954 đến năm 1965-Trần Đức Cường-2017.json"
    tap_13_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 13 Từ năm 1965 đến năm 1975-Nguyễn Văn Nhật-2017.json"
    tap_14_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 14 Từ năm 1975 đến năm 1986-Trần Đức Cường-2017.json"
    tap_15_json_path = HISTORICAL_KNOWLEDGE_PATH / "Lịch sử Việt Nam tập 15 Từ năm 1986 đến năm 2000-Nguyễn Ngọc Mão-2017.json"

    # Gọi hàm ocr 1 tập cụ thể
    # ocr_page(
    #     pdf_path=tap_7,
    #     json_path=tap7_json
    # )

    # Gọi hàm tách câu cho cả folder sách
    # sentence_segmentation(HISTORICAL_KNOWLEDGE_PATH)

    # Gọi hàm thống kê câu
    # sentence_statistics(HISTORICAL_KNOWLEDGE_PATH)

    # Gọi hàm clean khóa word cho 1 tập
    # clean_words_key(tap_4_json_path)

    # Gọi hàm clean khóa word cho cả folder
    # clean_words_key_folder(HISTORICAL_KNOWLEDGE_PATH)

    # Gọi hàm tách từ cho 1 sách
    # word_segmentation(tap_4_json_path)

    # Gọi hàm tách từ cho cả folder sách
    word_segmentation_folder(HISTORICAL_KNOWLEDGE_PATH)
