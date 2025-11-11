import os
import requests
import json
from dotenv import load_dotenv

from cats import Cats
from dogs import Dogs


load_dotenv()


class YandexDisk:
    """
    Базовый класс для работы с яндекс диском
    """
    def __init__(self, token: str):
        self.token = token
        self.base_url = 'https://cloud-api.yandex.net/v1/disk'
        self.headers = {
            'Authorization': f'OAuth {self.token}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Метод для выполнения запросов"""
        url = f'{self.base_url}/{endpoint}'
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            print(f'Запрос {method} {endpoint} выполнен успешно!')
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            print(f'Ошибка при запросе {method} {endpoint}: {e}')
            return None

    def _create_folder(self, folder_path: str):
        """Создание папки"""
        params = {'path': folder_path}
        result = self._make_request('PUT', 'resources', params=params)

        print(f'Папка {folder_path} создана!')
        if result is None:
            return True
        return True

    def create_folder(self, folder_path: str):
        """Создает папку или вложенную папку"""
        parts = folder_path.split('/')
        path = ''
        for part in parts:
            path = f'{path}/{part}' if path else part
            self._create_folder(path)


class YandexDiskFileManager(YandexDisk):
    """Класс для загрузки файлов в яндекс диск"""
    def _upload_bytes(self, folder_path: str, filename: str, data: bytes) -> bool:
        """Загрузка файла на яндекс диск"""
        try:
            # Получает ссылку для загрузки
            url = f'{self.base_url}/resources/upload'
            params= {
                'path': f'{folder_path}/{filename}',
                'overwrite': 'true'
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            href = response.json().get('href')

            # Загружает файл
            put_response = requests.put(href, data=data)
            put_response.raise_for_status()
            print(f'Файл {filename} успешно загружен!')
            return True
        except requests.exceptions.RequestException as e:
            print(f'Ошибка при загрузке {filename}:', e)
            return False

    def upload_pair(self, folder_path: str, image_data: dict):
        """Загружает jpg и json файлы в яндекс диск"""
        filename = image_data['filename']
        json_data = {
            'filename': image_data['filename'],
            'size_bytes': image_data['size_bytes']
        }

        json_bytes = json.dumps(json_data, indent=4).encode('utf-8')

        self._upload_bytes(folder_path, f'{filename}.jpg', image_data['image'])
        self._upload_bytes(folder_path, f'{filename}.json', json_bytes)
