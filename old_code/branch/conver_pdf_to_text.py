import pymupdf
from src.old_code.config import Config
from src.old_code.helper_file import FileHelper

# Hằng số đầu vào
input_json = Config.PROJECT_DIR / 'input.json'
output_path = Config.DATA_DIR / 'books_data.json'

# Logic xử lý
history_dir = FileHelper.read_json(input_json).get('history_dir')
history_book_files = FileHelper.list_files(history_dir)


def extract_words_with_metadata(page):
    words = []

    for word in page.get_text_words():
        x0, y0, x1, y1, text, block_no, line_no, word_no = word

        words.append({
            "text": text,
            "bbox": {
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1
            },
            "block_no": block_no,
            "line_no": line_no,
            "word_no": word_no
        })

    return words


def extract_books_data():
    books_data = {}
    for book_file in history_book_files:
        doc = pymupdf.open(book_file)
        book_data = {
            'book_name': book_file.name,
            'page_count': doc.page_count,
            'metadata': doc.metadata,
            'toc': doc.get_toc(),
            'pages': {}
        }
        for page in doc:
            print(book_file.name, page.number)
            book_data['pages'][page.number] = {
                'page_number': page.number,
                'text': page.get_text(),
                # 'words': extract_words_with_metadata(page),
                # 'images': page.get_images(),
                # 'links': page.get_links()
            }
            # break
        books_data[book_file.name] = book_data
        doc.close()
        # break

    # Lưu kết quả
    FileHelper.write_json(
        path=output_path,
        data=books_data
    )

extract_books_data()
