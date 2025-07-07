"""
URL configuration for proyectapis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # API de Ferremas con MongoDB
    path('api/', include('ferremas.mongo_urls')),
    
    # Interfaz web de Ferremas (páginas HTML)
    path('', include('ferremas.web_urls')),
    
    # URLs del carrito con Webpay (comentado para usar solo MongoDB)
    # path('carrito/', include('carrito.urls')),
    
    # URLs del carrito con MongoDB
    path('carrito/', include('carrito.urls_mongo')),
    
    # Endpoints SQLite originales (comentados)
    # path('api/', include('ferremas.urls')),  # Ferremas API con SQLite
    # path('inventario/', include('inventario.urls')),
    # path('producto/', include('carrito.urls')),
]
