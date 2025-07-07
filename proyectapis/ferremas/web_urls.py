from django.urls import path
from . import mongo_views

app_name = 'ferremas_web'

urlpatterns = [
    # Página principal/raíz
    path('', mongo_views.productos_venta_view, name='home'),
    
    # Páginas web para la interfaz de usuario
    path('venta/', mongo_views.productos_venta_view, name='productos_venta_view'),
    path('inventario/', mongo_views.inventario_sucursales_view, name='inventario_sucursales_view'),
    path('crear-producto/', mongo_views.crear_producto_form_view, name='crear_producto_form'),
    path('actualizar-stock/', mongo_views.actualizar_stock_form_view, name='actualizar_stock_form'),
    
    # Carrito de compras - Vista web
    path('carrito/', mongo_views.ver_carrito_view, name='ver_carrito'),
    
    # Confirmación de compra
    path('compra-exitosa/', mongo_views.compra_exitosa_view, name='compra_exitosa'),
    path('compra-rechazada/', mongo_views.compra_rechazada_view, name='compra_rechazada'),
    path('boleta/<str:boleta_codigo>/', mongo_views.ver_boleta_view, name='ver_boleta'),
    
    # Webpay integration
    path('webpay/return/', mongo_views.webpay_return_view, name='webpay_return'),
]
