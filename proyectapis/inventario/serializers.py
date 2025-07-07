from rest_framework import serializers
from .models import Producto, PrecioProducto, InventarioProducto, Sucursal


class ProductoSerializer(serializers.ModelSerializer):
    """Serializer para productos con formato Ferremas"""
    precio_actual = serializers.ReadOnlyField(source='get_precio_actual')
    stock_total = serializers.ReadOnlyField(source='get_stock_total')
    
    class Meta:
        model = Producto
        fields = [
            'id_producto', 'marca', 'modelo', 'nombre', 
            'categoria', 'descripcion', 'precio_actual', 
            'stock_total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PrecioSerializer(serializers.ModelSerializer):
    """Serializer para precios de productos"""
    
    class Meta:
        model = PrecioProducto
        fields = ['id', 'producto', 'valor', 'fecha', 'created_at']
        read_only_fields = ['created_at']


class InventarioSerializer(serializers.ModelSerializer):
    """Serializer para inventario de productos"""
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    sucursal_nombre = serializers.ReadOnlyField(source='sucursal.nombre')
    
    class Meta:
        model = InventarioProducto
        fields = [
            'id', 'producto', 'sucursal', 'cantidad', 
            'ultima_actualizacion', 'created_at',
            'producto_nombre', 'sucursal_nombre'
        ]
        read_only_fields = ['created_at']


class SucursalSerializer(serializers.ModelSerializer):
    """Serializer para sucursales"""
    
    class Meta:
        model = Sucursal
        fields = [
            'id', 'nombre', 'calle', 'numeracion', 
            'comuna', 'region', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }