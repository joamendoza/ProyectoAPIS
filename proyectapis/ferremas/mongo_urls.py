from django.urls import path
from . import mongo_views

app_name = 'ferremas_mongo'

urlpatterns = [
    # Endpoint raíz para MongoDB
    path('', mongo_views.root_mongo, name='root_mongo'),
    
    # Endpoint para leer productos desde MongoDB
    path('productos/', mongo_views.read_productos_mongo, name='read_productos_mongo'),
    
    # Endpoint para crear productos (Administrador) en MongoDB
    path('productos/<int:sucursal_id>/', mongo_views.create_producto_mongo, name='create_producto_mongo'),
    
    # Endpoint para consultar sucursales en MongoDB
    path('sucursales/', mongo_views.read_sucursales_mongo, name='read_sucursales_mongo'),
    
    # API para productos de venta
    path('productos/venta/', mongo_views.productos_venta_api, name='productos_venta_api'),
    
    # Endpoints específicos para inventario por sucursal
    path('sucursales/<int:sucursal_id>/inventario/', mongo_views.inventario_por_sucursal, name='inventario_por_sucursal'),
    path('productos/<str:producto_id>/sucursales/', mongo_views.producto_en_sucursales, name='producto_en_sucursales'),
    path('sucursales/<int:sucursal_id>/productos/<str:producto_id>/stock/', mongo_views.actualizar_stock_sucursal, name='actualizar_stock_sucursal'),
    
    # Vista de página de productos
    path('venta/', mongo_views.productos_venta_view, name='productos_venta_view'),
    
    # Vista de página de inventario por sucursales
    path('inventario/', mongo_views.inventario_sucursales_view, name='inventario_sucursales_view'),
    
    # Formularios para operaciones POST
    path('crear-producto/', mongo_views.crear_producto_form_view, name='crear_producto_form'),
    path('actualizar-stock/', mongo_views.actualizar_stock_form_view, name='actualizar_stock_form'),
    
    # Carrito de compras - API endpoints
    path('carrito/agregar/', mongo_views.agregar_al_carrito_mongo, name='agregar_al_carrito'),
    path('carrito/ver/', mongo_views.ver_carrito_mongo, name='ver_carrito_api'),
    path('carrito/actualizar/<str:item_id>/', mongo_views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),
    path('carrito/eliminar/<str:item_id>/', mongo_views.eliminar_del_carrito_mongo, name='eliminar_del_carrito'),
    path('carrito/cambiar-sucursal/<str:item_id>/', mongo_views.cambiar_sucursal_carrito, name='cambiar_sucursal_carrito'),
    path('carrito/count/', mongo_views.carrito_count_mongo, name='carrito_count'),
    path('carrito/procesar/', mongo_views.procesar_compra_mongo, name='procesar_compra'),
    
    # Vistas de confirmación de compra
    path('compra/exitosa/', mongo_views.compra_exitosa_view, name='compra_exitosa'),
    path('compra/rechazada/', mongo_views.compra_rechazada_view, name='compra_rechazada'),
    path('boleta/<str:boleta_codigo>/', mongo_views.ver_boleta_view, name='ver_boleta'),
    path('carrito/boleta/<str:boleta_id>/pdf/', mongo_views.generar_boleta_pdf_view, name='generar_boleta_pdf'),

    # API de Boletas - Consultas de boletas (orden importante)
    path('boletas/estadisticas/', mongo_views.boletas_estadisticas_api, name='boletas_estadisticas_api'),
    path('boletas/', mongo_views.boletas_api, name='boletas_api'),
    path('boletas/<str:boleta_codigo>/', mongo_views.boleta_detalle_api, name='boleta_detalle_api'),

    
    # Webpay integration
    path('webpay/return/', mongo_views.webpay_return_view, name='webpay_return'),
    
    # BCCH integration
    path('api/tipo-cambio/', mongo_views.obtener_tipo_cambio_api, name='obtener_tipo_cambio_api'),
    path('api/convertir-moneda/', mongo_views.convertir_moneda_api, name='convertir_moneda_api'),
    path('api/indicadores/', mongo_views.obtener_indicadores_api, name='obtener_indicadores_api'),
]
