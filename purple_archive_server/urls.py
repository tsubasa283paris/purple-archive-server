from django.contrib import admin
from django.urls import path, include

from server.urls import router as server_router

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(server_router.urls)),
]
