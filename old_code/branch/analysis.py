import pandas as pd
from src.old_code.helper_file import FileHelper
from src.old_code.config import Config

WORDS_PATH = Config.DATA_DIR / 'words.csv'
ENTITIES_PATH = Config.DATA_DIR / 'entities.csv'


def extract_and_export_words():
    historical_knowledge_folder = Config.DATA_DIR / 'historical_knowledge'

    json_files = FileHelper.list_files(historical_knowledge_folder)
    # print(json_files)

    all_word = []
    for file in json_files:
        json_data = FileHelper.read_json(file)
        book_name = json_data.get('book_name')
        pages = json_data.get('pages')
        all_word_in_book = []
        for number_page, page in pages.items():
            # print(number_page)
            # print(page.keys()) # dict_keys(['page_number', 'text', 'sentences', 'words'])
            words = page.get('words')
            # print(words)
            # break
            if words is None:
                print(f'{book_name} page {number_page} has no word')
            else:
                for word in words:
                    word['number_page'] = number_page
                    word['book_name'] = book_name
                all_word_in_book.extend(words)
        # print(all_word_in_book)
        all_word.extend(all_word_in_book)

    df = pd.DataFrame(all_word)
    df.to_csv(
        WORDS_PATH,
        index=False,
        encoding='utf-8-sig'
    )


def filter_by_entity(df, entity_type):
    return df[df["entity"] == entity_type]


def build_entity_dataset(df):
    entities = []

    current_entity = []
    current_type = None

    current_index = []
    current_start = None
    current_end = None
    current_page = None
    current_book = None

    for _, row in df.iterrows():
        label = row["entity"]
        word = row["word"]

        if label.startswith("B-"):

            # Lưu entity cũ
            if current_entity:
                entities.append({
                    "entity": " ".join(current_entity),
                    "entity_type": current_type,
                    "index": current_index,
                    "start": current_start,
                    "end": current_end,
                    "number_page": current_page,
                    "book_name": current_book
                })

            # Bắt đầu entity mới
            current_entity = [word]
            current_type = label[2:]

            current_index = [row["index"]]
            current_start = row["start"]
            current_end = row["end"]
            current_page = row["number_page"]
            current_book = row["book_name"]

        elif label.startswith("I-"):

            # Nối từ vào entity hiện tại
            current_entity.append(str(word))

            current_index.append(row["index"])
            current_end = row["end"]

    # Lưu entity cuối cùng
    if current_entity:
        entities.append({
            "entity": " ".join(current_entity),
            "entity_type": current_type,
            "index": current_index,
            "start": current_start,
            "end": current_end,
            "number_page": current_page,
            "book_name": current_book
        })

    df_entities = pd.DataFrame(entities)
    df_entities.to_csv(
        ENTITIES_PATH,
        index=False,
        encoding='utf-8-sig'
    )


def analysis():
    df = pd.read_csv(ENTITIES_PATH)
    # print(df.info())
    # build_entity_dataset(df)

    # Lấy cột entity và đếm số lần xuất hiện
    # entity_counts = df["entity"].value_counts()
    #
    # # print(entity_counts)
    # FileHelper.write_text(
    #     path=Config.DATA_DIR / 'view_entities.txt',
    #     content=entity_counts.to_string()
    # )

if __name__ == '__main__':
    # extract_and_export_words()
    analysis()
    ...
