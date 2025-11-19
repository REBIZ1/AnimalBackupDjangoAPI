import asyncio
import aiohttp
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
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def _make_request(self, method: str, endpoint: str, **kwargs):
        """Метод для выполнения запросов"""
        url = f'{self.base_url}/{endpoint}'
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            ) as response:
                if response.status == 409:
                    return {}
                response.raise_for_status()
                logger.info(f"Запрос {method} {endpoint} выполнен успешно!")
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при запросе {method} {endpoint}: {e}")
            return None

    async def _create_folder(self, folder_path: str):
        """Создание папки"""
        params = {'path': folder_path}
        await self._make_request('PUT', 'resources', params=params)
        logger.info(f"Создана папка: {folder_path}")

    async def create_folder(self, folder_path: str):
        """Создает папку или вложенную папку"""
        await self._ensure_session()

        parts = folder_path.split('/')
        path = ''
        for part in parts:
            path = f'{path}/{part}' if path else part
            await self._create_folder(path)


class YandexDiskFileManager(YandexDisk):
    """Класс для загрузки файлов в яндекс диск"""
    async def _upload_bytes(self, folder_path: str, filename: str, data: bytes) -> bool:
        """Загрузка файла на яндекс диск"""
        try:
            # Получает ссылку для загрузки
            url = f'{self.base_url}/resources/upload'
            params= {
                'path': f'{folder_path}/{filename}',
                'overwrite': 'true'
            }
            async with self.session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                href = (await response.json()).get('href')
                if not href:
                    return False

            # Загружает файл
            async with self.session.put(href, data=data) as put_response:
                put_response.raise_for_status()
                logger.info(f"Файл {filename} успешно загружен в {folder_path}")
                return True
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при загрузке {filename}: {e}")
            return False

    async def upload_data(self, folder_path: str, image_data: dict):
        """
        Универсальная загрузка данных:
        - Если передан один файл (api cataas.com), загружает 1 .jpg и 1 .json
        - Если передан словарь с подпородами (api dog.ceo) загружает все .jpg и общий .json
        """
        await self._ensure_session()

        result = []

        async def _upload_single_image(image_data: dict):
            """
            Вспомогательная функция для загрузки одного изображения и возврата json
            """
            try:
                filename = image_data['filename']
                size_bytes = image_data['size_bytes']
                image = image_data['image']
                await self._upload_bytes(folder_path, f'{filename}.jpg', image)
                result.append({
                    'filename': filename,
                    'size_bytes': size_bytes
                })
            except Exception as e:
                logger.error(f"Ошибка при загрузке файла {filename}.jpg: {e}")

        async def _upload_json(filename: str):
            try:
                json_bytes = json.dumps(result, indent=4, ensure_ascii=False).encode('utf-8')
                await self._upload_bytes(folder_path, f"{filename}.json", json_bytes)
                logger.info(f"Файл {filename}.json успешно загружен!")
            except Exception as e:
                logger.error(f"Ошибка при загрузке JSON: {e}")

        tasks = []

        # С одной картинкой (cataas.com)
        if 'image' in image_data:
            tasks.append(_upload_single_image(image_data))
            await asyncio.gather(*tasks)
            await _upload_json(image_data['filename'])
            # С несколькими картинками (dog.ceo)
        else:
            for breed_data in image_data.values():
                tasks.append(_upload_single_image(breed_data))
                # если есть подпороды
                if 'sub_breeds' in breed_data:
                    for sub_data in breed_data['sub_breeds'].values():
                        tasks.append(_upload_single_image(sub_data))
            await asyncio.gather(*tasks)
            await _upload_json('result')



