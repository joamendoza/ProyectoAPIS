from django.urls import path
from .views import lista_productos, agregar_al_carrito, ver_carrito, pagar, iniciar_pago_webpay, webpay_respuesta, eliminar_del_carrito, descargar_boleta_pdf

urlpatterns = [
    path('', lista_productos, name='lista_productos'),
    path('agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', ver_carrito, name='ver_carrito'),
    path('pagar/', pagar, name='pagar'),
    path('pagar_webpay/', iniciar_pago_webpay, name='pagar_webpay'),
    path('webpay_respuesta/', webpay_respuesta, name='webpay_respuesta'),
    path('carrito/eliminar/<int:item_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('boleta/pdf/<str:codigo_boleta>/', descargar_boleta_pdf, name='descargar_boleta_pdf'),
]