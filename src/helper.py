import json
import time


def read_text(path: str, **kwargs):
    '''
    Đọc text từ file, format thông tin nếu cần
    :param path:
    :param kwargs:
    :return:
    '''
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    return data.format(**kwargs)

def write_text(path: str, data: str):
    '''
    Lưu dữ liệu ra file
    :param path:
    :param data:
    :return:
    '''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)

def json_save(path: str, data: dict):
    '''
    Lưu dict ra json
    :param path:
    :param data:
    :return:
    '''
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def json_load(path: str):
    '''
    Đọc file json thành dict
    :param path:
    :return:
    '''
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def print_dict(data: dict):
    '''
    In dict dễ nhìn
    :param data:
    :return:
    '''
    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )

def timer(func):
    '''
    Đo thời gian chạy hàm
    :param func:
    :return:
    '''
    def wrapper(*args, **kwargs):
        start = time.time()

        result = func(*args, **kwargs)

        end = time.time()

        print(
            f"{func.__name__}: {end - start:.4f}s"
        )

        return result

    return wrapper