import requests
import json
import logging

logger = logging.getLogger(__name__)


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
            if response.status_code == 409 and method == "PUT" and endpoint == "resources":
                return {}

            response.raise_for_status()
            logger.info(f"Запрос {method} {endpoint} выполнен успешно!")
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе {method} {endpoint}: {e}")
            return None

    def _create_folder(self, folder_path: str):
        """Создание папки"""
        params = {'path': folder_path}
        self._make_request('PUT', 'resources', params=params)
        logger.info(f"Папка создана: {folder_path}")

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
            logger.info(f"Файл {filename} успешно загружен в {folder_path}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при загрузке {filename}: {e}")
            return False

    def upload_data(self, folder_path: str, image_data: dict):
        """
        Универсальная загрузка данных:
        - Если передан один файл (api cataas.com), загружает 1 .jpg и 1 .json
        - Если передан словарь с подпородами (api dog.ceo) загружает все .jpg и общий .json
        """
        result = []

        def upload_single_image(image_data: dict):
            """
            Вспомогательная функция для загрузки одного изображения и возврата json
            """
            try:
                filename = image_data['filename']
                size_bytes = image_data['size_bytes']
                image = image_data['image']
                self._upload_bytes(folder_path, f'{filename}.jpg', image)
                result.append({
                    'filename': filename,
                    'size_bytes': size_bytes
                })
            except Exception as e:
                logger.error(f"Ошибка при загрузке файла {filename}.jpg: {e}")

        # С одной картинкой (cataas.com)
        if 'image' in image_data:
            upload_single_image(image_data)
        # С несколькими картинками (dog.ceo)
        else:
            for breed_data in image_data.values():
                upload_single_image(breed_data)
                # если есть подпороды
                if 'sub_breeds' in breed_data:
                    for sub_data in breed_data['sub_breeds'].values():
                        upload_single_image(sub_data)

        try:
            json_bytes = json.dumps(result, indent=4, ensure_ascii=False).encode('utf-8')
            self._upload_bytes(folder_path, "result.json", json_bytes)
            logger.info("JSON файл с результатами успешно загружен!")
        except Exception as e:
            logger.error(f"Ошибка при загрузке JSON: {e}")


