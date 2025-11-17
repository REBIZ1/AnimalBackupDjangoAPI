import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)


class Cats:
    """Класс для работы с API cataas.com"""
    base_url = 'https://cataas.com'

    @staticmethod
    async def get_cat_with_text(text: str):
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
        logger.info(f'Запрос картинки с текстом: {text}')
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(f'{Cats.base_url}/cat/says/{text}', timeout=timeout) as response:
                    image = await response.read()
                    result = {
                        'filename': text,
                        'size_bytes': len(image),
                        'image': image
                    }
                    logger.info(f'Получена картинка с текстом: {text}')
                    return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f'Ошибка при получении картинки с текстом: {e}')
            return None


