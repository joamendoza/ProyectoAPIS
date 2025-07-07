from django.urls import path, include

urlpatterns = [
    # URLs para carrito con MongoDB
    path('', include('carrito.urls_mongo')),
]