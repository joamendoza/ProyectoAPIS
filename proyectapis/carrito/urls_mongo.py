"""
URLs para el carrito con MongoDB
"""
from django.urls import path
from . import views_mongo

urlpatterns = [
    path('productos/', views_mongo.lista_productos_mongo, name='lista_productos_mongo'),
    path('agregar/<str:producto_id>/', views_mongo.agregar_al_carrito_mongo, name='agregar_al_carrito_mongo'),
    path('', views_mongo.ver_carrito_mongo, name='ver_carrito_mongo'),
    path('actualizar/<str:item_id>/', views_mongo.actualizar_cantidad_mongo, name='actualizar_cantidad_mongo'),
    path('eliminar/<str:item_id>/', views_mongo.eliminar_del_carrito_mongo, name='eliminar_del_carrito_mongo'),
    path('procesar-compra/', views_mongo.procesar_compra_mongo, name='procesar_compra_mongo'),
    path('pagar/', views_mongo.iniciar_pago_webpay_mongo, name='iniciar_pago_webpay_mongo'),
    path('webpay/respuesta/', views_mongo.webpay_respuesta_mongo, name='webpay_respuesta_mongo'),
    path('webpay/debug/', views_mongo.debug_webpay_mongo, name='debug_webpay_mongo'),
    path('webpay/test/', views_mongo.test_webpay_response_mongo, name='test_webpay_response_mongo'),
    path('boleta/pdf/<str:codigo_boleta>/', views_mongo.descargar_boleta_pdf_mongo, name='descargar_boleta_pdf_mongo'),
    path('count/', views_mongo.contar_carrito_mongo, name='contar_carrito_mongo'),
    path('estado/', views_mongo.estado_carrito_mongo, name='estado_carrito_mongo'),
]
