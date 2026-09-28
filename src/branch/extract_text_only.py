from src.helper_file import FileHelper
from src.config import Config

history_text_folder = Config.DATA_DIR / 'history_text'
history_text_folder.mkdir(exist_ok=True, parents=True)

historical_knowledge_folder = Config.DATA_DIR / 'historical_knowledge'

json_files = FileHelper.list_files(historical_knowledge_folder)
# print(json_files)
for file in json_files:
    json_data = FileHelper.read_json(file)
    # print(data.keys()) # dict_keys(['book_name', 'page_count', 'volume', 'period', 'author', 'publication_year', 'toc', 'pages'])
    # break

    # Chuỗi nối để đem lưu
    text_data_to_save = ''
    pages = json_data.get('pages')
    for number_page, page in pages.items():
        # print(number_page)
        # print(page.keys()) # dict_keys(['page_number', 'text', 'sentences', 'words'])
        text = page.get('text')
        # print(text)
        # break

        # Công vào chuỗi nối
        text_data_to_save += text
    # print(text_data_to_save)

    # Lưu file chỉ text
    FileHelper.write_text(
        path=history_text_folder / f'{file.stem}.txt',
        content=text_data_to_save
    )
    # break
