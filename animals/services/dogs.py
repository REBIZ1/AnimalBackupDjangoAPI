import asyncio
import aiohttp
from functools import wraps
import logging

logger = logging.getLogger(__name__)
timeout = aiohttp.ClientTimeout(total=10)

def add_all_sub_breed(func):
    """
    Декоратор для функции get_dog.
    После получения основной породы автоматически получает подпороды
    и добавляет их в словарь с изображениями.
    """
    @wraps(func)
    async def wrapper(breed: str, session: aiohttp.ClientSession):
        async with aiohttp.ClientSession() as session:
            result = await func(breed, session)
            if result is None:
                return None
            try:
                async with session.get(f'{Dogs.base_url}/breed/{breed}/list', timeout=timeout) as response:
                    response.raise_for_status()
                    data = await response.json()
                    sub_breeds = data.get('message', [])

                if sub_breeds:
                    result[breed]['sub_breeds'] = {}
                    # Создаем список корутин для подпород
                    coroutines = [Dogs._get_image(f"{breed}/{sub}", session) for sub in sub_breeds]
                    sub_images = await asyncio.gather(*coroutines)
                    for sub, img in zip(sub_breeds, sub_images):
                        if img:
                            result[breed]['sub_breeds'][sub] = {
                                'filename': f'{breed}_{sub}',
                                'size_bytes': len(img),
                                'image': img
                            }
                            logger.info(f"Картинка подпороды {breed}_{sub} получена")
                        else:
                            logger.warning(f"Не удалось получить картинку подпороды {breed}_{sub}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"Ошибка при получении подпород {breed}: {e}")
            return result
    return wrapper


class Dogs:
    """
    Класс для работы с изображениями собак через API dog.ceo
    """
    base_url = 'https://dog.ceo/api'

    @staticmethod
    async def _get_image(breed: str, session: aiohttp.ClientSession):
        """
        Получает изображение (bytes) для указанной породы или подпороды.
        Args:
            breed (str): название породы или подпороды
        Returns:
            bytes или None: байты изображения или None при ошибке
        """
        try:
            # Получаем JSON с ссылкой на картинку
            async with session.get(f'{Dogs.base_url}/breed/{breed}/images/random', timeout=timeout) as response:
                response.raise_for_status()
                data = await response.json()
                image_url = data['message']
                if not image_url:
                    logger.warning(f"Нет изображения для {breed}")
                    return None

            # Получает картинку
            async with session.get(image_url, timeout=timeout) as image_res:
                image_res.raise_for_status()
                return await image_res.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Ошибка при получении картинки для {breed}: {e}")
            return None


    @staticmethod
    @add_all_sub_breed
    async def get_dog(breed: str, session: aiohttp.ClientSession):
        """
        Получает изображение для основной породы
        Args:
            breed (str): название породы
        Returns:
            dict или None: словарь с информацией о породе
        """
        image = await Dogs._get_image(breed, session)
        if not image:
            logger.error(f"Не удалось получить изображение для основной породы: {breed}")
            return None

        logger.info(f"Изображение основной породы {breed} получено успешно")
        return {
            breed: {
                'filename': breed,
                'size_bytes': len(image),
                'image': image
            }
        }

    @staticmethod
    async def get_all_breeds():
        """
        Получает список всех пород собак.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{Dogs.base_url}/breeds/list/all", timeout=timeout) as response:
                    response.raise_for_status()
                    data = await response.json()
                    breeds_dict = data.get("message", {})
                    return list(breeds_dict.keys())

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Ошибка при получении списка пород: {e}")
            return None
