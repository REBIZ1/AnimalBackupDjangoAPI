import requests
import logging

logger = logging.getLogger(__name__)


class Cats:
    """Класс для работы с API cataas.com"""
    base_url = 'https://cataas.com'

    @staticmethod
    def get_cat_with_text(text: str):
        """
        Получает картинку кота с текстом и возвращает словарь с данными.
        входные данные:
        - text: Текст для картинки
        Выходные данные:
        - Словарь:
            - filename: имя файла
            - size_bytes: размер картинки
            - image: байтовое содержимое картинки
        """
        try:
            response = requests.get(f'{Cats.base_url}/cat/says/{text}', timeout=10)
            response.raise_for_status()
            image = response.content
            result = {
                'filename': text,
                'size_bytes': len(image),
                'image': image
            }
            logger.info(f'Получена картинка с текстом: {text}')
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f'Ошибка при получении картинки с текстом: {e}')
            return None


