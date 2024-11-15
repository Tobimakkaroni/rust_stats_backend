from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from api.api import router

api = NinjaAPI()

api.add_router("/steam/", router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]