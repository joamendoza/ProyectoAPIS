from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Producto
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductoSerializer

class ProductoListView(ListView):
    model = Producto
    template_name = 'inventario/producto_list.html'

class ProductoCreateView(CreateView):
    model = Producto
    fields = ['nombre', 'categoria', 'descripcion', 'precio', 'stock']
    template_name = 'inventario/producto_form.html'
    success_url = reverse_lazy('producto_list')

class ProductoUpdateView(UpdateView):
    model = Producto
    fields = ['nombre', 'categoria', 'descripcion', 'precio', 'stock']
    template_name = 'inventario/producto_form.html'
    success_url = reverse_lazy('producto_list')

class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'inventario/producto_confirm_delete.html'
    success_url = reverse_lazy('producto_list')

class ProductoListAPIView(APIView):
    """
    API para listar todos los productos.
    """
    def get(self, request):
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductoDetailAPIView(APIView):
    """
    API para obtener detalles de un producto específico.
    """
    def get(self, request, pk):
        try:
            producto = Producto.objects.get(pk=pk)
            serializer = ProductoSerializer(producto)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Producto.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=status.HTTP_404_NOT_FOUND)
