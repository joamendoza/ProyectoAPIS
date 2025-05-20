from django.urls import path
from .views import ProductoListView, ProductoCreateView, ProductoUpdateView, ProductoDeleteView, ProductoListAPIView, ProductoDetailAPIView

urlpatterns = [
    path('', ProductoListView.as_view(), name='producto_list'),
    path('nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('<int:pk>/editar/', ProductoUpdateView.as_view(), name='producto_update'),
    path('<int:pk>/eliminar/', ProductoDeleteView.as_view(), name='producto_delete'),
    path('api/productos/', ProductoListAPIView.as_view(), name='api_productos_list'),
    path('api/productos/<int:pk>/', ProductoDetailAPIView.as_view(), name='api_productos_detail'),
]