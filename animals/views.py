import base64
import aiohttp
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from animals.services.cats import Cats
from animals.services.dogs import Dogs
from animals.services.yandex_disk import YandexDiskFileManager
from asgiref.sync import async_to_sync


def index(request):
    """
    Главная страница.
    - Показывает поле ввода токена
    - После ввода сохраняет токен в сессии и показывает кнопки 'Коты' и 'Собаки'
    """
    token = request.session.get('yadisk_token')

    return render(request, 'animals/index.html', {
        'token': token,
        'token_exists': bool(token)
    })


@csrf_exempt
def save_token(request):
    """
    Обработчик формы сохранения токена
    """
    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        if token:
            request.session['yadisk_token'] = token

        return redirect('index')

    return redirect('index')

def cats_page(request):
    """
    Показывает форму:
    - текст для картинки
    - путь на Яндекс Диск
    - кнопки: получить картинку, загрузить
    """

    saved_cat = request.session.get('cat_image')   # bytes в base64
    saved_text = request.session.get('cat_text', '')
    saved_path = request.session.get('cat_path', 'pd-fpy_138/Cats')

    return render(request, 'animals/cats.html', {
        'image_b64': saved_cat,
        'text_value': saved_text,
        'path_value': saved_path
    })

@csrf_exempt
def get_cat_image(request):
    """
    Принимает текст, запрашивает кота у API cataas.com,
    """
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        path = request.POST.get('path', 'pd-fpy_138/Cats').strip()

        request.session['cat_text'] = text
        request.session['cat_path'] = path

        if not text:
            return redirect('cats_page')

        result = async_to_sync(Cats.get_cat_with_text)(text)
        if result is None:
            return redirect('cats_page')

        image_b64 = base64.b64encode(result['image']).decode('utf-8')
        request.session['cat_image'] = image_b64
        request.session['cat_image_b64_for_upload'] = image_b64
        request.session['cat_filename'] = result['filename']

    return redirect('cats_page')

@csrf_exempt
def upload_cat_to_disk(request):
    """
    Загружает сохраненную картинку на Яндекс Диск
    """
    if request.method == 'POST':

        token = request.session.get('yadisk_token')
        image_b64 = request.session.get('cat_image_b64_for_upload')
        filename = request.session.get('cat_filename')
        path = request.session.get('cat_path', 'pd-fpy_138/Cats')

        if not (token and image_b64 and filename):
            return redirect('cats_page')

        image_bytes = base64.b64decode(image_b64)
        data = {
            'filename': filename,
            'size_bytes': len(image_bytes),
            'image': image_bytes,
        }

        async def upload_task():
            async with YandexDiskFileManager(token) as yd:
                await yd.create_folder(path)
                await yd.upload_data(path, data)

        async_to_sync(upload_task)()

    return redirect('cats_page')

def dogs_page(request):
    """
    Форма для собак
    """
    breeds = async_to_sync(Dogs.get_all_breeds)() or []

    saved_breed = request.session.get('dog_breed', '')
    saved_path = request.session.get('dog_path', 'pd-fpy_138/Dogs')
    main_b64 = request.session.get('dog_main_image')
    sub_images = request.session.get('dog_sub_images', {})

    return render(request, 'animals/dogs.html', {
        'breeds': breeds,
        'selected_breed': saved_breed,
        'image_b64': main_b64,
        'path_value': saved_path,
        'sub_images': sub_images,
    })

@csrf_exempt
def get_dog_image(request):
    """
    Получает картинки основной породы и подпород
    """
    if request.method == 'POST':
        breed = request.POST.get('breed')
        if not breed:
            return redirect('dogs_page')

        path = f'pd-fpy_138/Dogs/{breed}'
        request.session['dog_breed'] = breed
        request.session['dog_path'] = path

        async def fetch_dog_data():
            async with aiohttp.ClientSession() as session:
                return await Dogs.get_dog(breed, session)

        data = async_to_sync(fetch_dog_data)()
        if data is None:
            return redirect('dogs_page')

        # Основная порода
        main_data = data[breed]
        main_b64 = base64.b64encode(main_data['image']).decode('utf-8')
        request.session['dog_main_image'] = main_b64
        request.session['dog_main_bytes_for_upload'] = main_b64
        request.session['dog_main_filename'] = main_data['filename']

        # Подпороды
        sub_images = {}
        if 'sub_breeds' in main_data:
            for subname, subdata in main_data['sub_breeds'].items():
                sub_b64 = base64.b64encode(subdata['image']).decode('utf-8')
                sub_images[subname] = sub_b64
        request.session['dog_sub_images'] = sub_images

        # Сохраняем весь словарь данных в base64 для загрузки
        dog_raw_data = {}
        for k, v in data.items():
            dog_raw_data[k] = {'filename': v['filename'],
                               'size_bytes': len(v['image']),
                               'image': base64.b64encode(v['image']).decode('utf-8')}
            if 'sub_breeds' in v:
                dog_raw_data[k]['sub_breeds'] = {}
                for sk, sv in v['sub_breeds'].items():
                    dog_raw_data[k]['sub_breeds'][sk] = {
                        'filename': sv['filename'],
                        'size_bytes': len(sv['image']),
                        'image': base64.b64encode(sv['image']).decode('utf-8')
                    }

        request.session['dog_raw_data_for_upload'] = dog_raw_data

    return redirect('dogs_page')

@csrf_exempt
def upload_dog_to_disk(request):
    """
    Загружает основную породу и подпороды на Яндекс Диск.
    """
    if request.method == 'POST':
        token = request.session.get('yadisk_token')
        path = request.session.get('dog_path', 'pd-fpy_138/Dogs')
        raw_data_b64 = request.session.get('dog_raw_data_for_upload')

        if not (token and raw_data_b64):
            return redirect('dogs_page')

        raw_data_bytes = {}
        for k, v in raw_data_b64.items():
            raw_data_bytes[k] = {'filename': v['filename'],
                                 'size_bytes': v['size_bytes'],
                                 'image': base64.b64decode(v['image'])}
            if 'sub_breeds' in v:
                raw_data_bytes[k]['sub_breeds'] = {}
                for sk, sv in v['sub_breeds'].items():
                    raw_data_bytes[k]['sub_breeds'][sk] = {
                        'filename': sv['filename'],
                        'size_bytes': sv['size_bytes'],
                        'image': base64.b64decode(sv['image'])
                    }

        async def upload_task():
            async with YandexDiskFileManager(token) as yd:
                await yd.create_folder(path)
                await yd.upload_data(path, raw_data_bytes)

        async_to_sync(upload_task)()

    return redirect('dogs_page')