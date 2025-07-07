from django.urls import path
from . import views

app_name = 'ferremas'

urlpatterns = [
    # Endpoint raíz
    path('', views.root, name='root'),
    
    # Endpoint para leer productos
    path('productos/', views.read_productos_by_sucursal, name='read_productos'),
    
    # Endpoint para crear productos (Administrador)
    path('productos/<int:sucursal_id>/', views.create_producto, name='create_producto'),
    
    # Endpoint para crear inventario de productos (sucursal)
    path('productos/inventario/<int:sucursal_id>/', views.create_inventario, name='create_inventario'),
    
    # Endpoint para actualizar inventario de productos (sucursal)
    path('productos/<int:sucursal_id>/<str:producto_id>/', views.update_inventario, name='update_inventario'),
    
    # Endpoint para eliminar productos (Administrador)
    path('productos/<str:producto_id>/', views.delete_producto, name='delete_producto'),
    
    # Endpoint para consultar sucursales
    path('sucursales/', views.read_sucursales, name='read_sucursales'),
]
