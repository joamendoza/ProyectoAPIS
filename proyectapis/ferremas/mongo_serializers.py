"""
Serializers para MongoDB usando serializers normales de DRF
"""
from rest_framework import serializers
from datetime import datetime

class PrecioSerializer(serializers.Serializer):
    """Serializer para precios"""
    fecha = serializers.DateTimeField()
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)

class InventarioSerializer(serializers.Serializer):
    """Serializer para inventario"""
    sucursal = serializers.IntegerField()
    nombre_sucursal = serializers.CharField(max_length=100)
    cantidad = serializers.IntegerField()
    ultima_actualizacion = serializers.DateTimeField()

class ProductoMongoSerializer(serializers.Serializer):
    """Serializer para productos de MongoDB"""
    _id = serializers.CharField(max_length=50)
    marca = serializers.CharField(max_length=100)
    modelo = serializers.CharField(max_length=100)
    nombre = serializers.CharField(max_length=200)
    categoria = serializers.CharField(max_length=50)
    descripcion = serializers.CharField()
    precio = PrecioSerializer(many=True, read_only=True)
    inventario = InventarioSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

class ProductoFerremasMongoSerializer(serializers.Serializer):
    """Serializer para productos con formato Ferremas original"""
    marca = serializers.CharField(max_length=100)
    modelo = serializers.CharField(max_length=100)
    nombre = serializers.CharField(max_length=200)
    precio = PrecioSerializer(many=True, read_only=True)
    inventario = InventarioSerializer(many=True, read_only=True)
    _id = serializers.CharField(max_length=50)

class ProductoCreateSerializer(serializers.Serializer):
    """Serializer para crear productos"""
    _id = serializers.CharField(max_length=50)
    marca = serializers.CharField(max_length=100)
    modelo = serializers.CharField(max_length=100)
    nombre = serializers.CharField(max_length=200)
    categoria = serializers.CharField(max_length=50, required=False)
    descripcion = serializers.CharField(required=False)
    precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad = serializers.IntegerField(default=0)

class ProductoVentaSerializer(serializers.Serializer):
    """Serializer para mostrar productos en página de venta"""
    _id = serializers.CharField(max_length=50)
    marca = serializers.CharField(max_length=100)
    modelo = serializers.CharField(max_length=100)
    nombre = serializers.CharField(max_length=200)
    categoria = serializers.CharField(max_length=50)
    descripcion = serializers.CharField()
    precio_actual = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_total = serializers.IntegerField()
    imagen_url = serializers.URLField()

class SucursalMongoSerializer(serializers.Serializer):
    """Serializer para sucursales"""
    _id = serializers.IntegerField()
    nombre = serializers.CharField(max_length=100)
    calle = serializers.CharField(max_length=200)
    numeracion = serializers.CharField(max_length=20)
    comuna = serializers.CharField(max_length=100)
    region = serializers.CharField(max_length=100)
    created_at = serializers.DateTimeField()

class AdministradorMongoSerializer(serializers.Serializer):
    """Serializer para administradores"""
    nombre = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    created_at = serializers.DateTimeField()
