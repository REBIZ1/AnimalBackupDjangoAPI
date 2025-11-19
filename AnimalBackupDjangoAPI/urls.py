"""
URL configuration for AnimalBackupDjangoAPI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from animals.views import index, save_token, cats_page, get_cat_image, upload_cat_to_disk, dogs_page, get_dog_image, upload_dog_to_disk
urlpatterns = [
    path("", index, name="index"),
    path("save-token/", save_token, name="save_token"),
    path("cats/", cats_page, name="cats_page"),
    path("cats/get/", get_cat_image, name="get_cat_image"),
    path("cats/upload/", upload_cat_to_disk, name="upload_cat_to_disk"),
    path("dogs/", dogs_page, name="dogs_page"),
    path("dogs/get/", get_dog_image, name="get_dog_image"),
    path("dogs/upload/", upload_dog_to_disk, name="upload_dog_to_disk"),
]
