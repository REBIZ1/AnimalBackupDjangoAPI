import requests
from functools import wraps
from pprint import pprint


def add_all_sub_breed(func):
    """
    Декоратор для функции get_dog.
    После получения основной породы автоматически получает подпороды
    и добавляет их в словарь с изображениями.
    """
    @wraps(func)
    def wrapper(breed: str):
        result = func(breed)
        try:
            response = requests.get(f'{Dogs.base_url}/breed/{breed}/list', timeout=10)
            response.raise_for_status()
            data = response.json()
            sub_breeds = data.get('message', [])

            if sub_breeds:
                result[breed]['sub_breeds'] = {}
                for sub in sub_breeds:
                    sub_image = Dogs._get_image(f"{breed}/{sub}")
                    result[breed]['sub_breeds'][sub] = {
                        'filename': f'{breed}_{sub}',
                        'size_bytes': len(sub_image) if sub_image else 0,
                        'image': sub_image
                    }
        except requests.exceptions.RequestException as e:
            print('Ошибка при получении подпород:', e)

        return result
    return wrapper


class Dogs:
    """
    Класс для работы с изображениями собак через API dog.ceo
    """
    base_url = 'https://dog.ceo/api'

    @staticmethod
    def _get_image(breed: str):
        """
        Загружает изображение для указанной породы или подпороды.
        Args:
            breed (str): название породы или подпороды
        Returns:
            bytes или None: байты изображения или None при ошибке
        """
        try:
            # Получаем JSON с ссылкой на картинку
            response = requests.get(f'{Dogs.base_url}/breed/{breed}/images/random', timeout=10)
            response.raise_for_status()
            data = response.json()
            image_url = data['message']
            if not image_url:
                return None

            # Загружаем картинку
            image_res = requests.get(image_url, timeout=10)
            image_res.raise_for_status()
            return image_res.content
        except requests.exceptions.RequestException as e:
            print('Ошибка при получении картинки:', e)
            return None


    @staticmethod
    @add_all_sub_breed
    def get_dog(breed: str):
        """
        Получает изображение для основной породы
        Args:
            breed (str): название породы
        Returns:
            dict или None: словарь с информацией о породе
        """
        image = Dogs._get_image(breed)
        if not image:
            return None
        return {
            breed: {
                'filename': breed,
                'size_bytes': len(image),
                'image': image
            }
        }


result = Dogs.get_dog('hound')
pprint(result)
