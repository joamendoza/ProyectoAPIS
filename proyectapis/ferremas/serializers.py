from rest_framework import serializers
from inventario.models import Producto, PrecioProducto, InventarioProducto, Sucursal
from .models import Administrador
from datetime import datetime


class PrecioProductoSerializer(serializers.ModelSerializer):
    """Serializer para los precios de productos"""
    
    class Meta:
        model = PrecioProducto
        fields = ['fecha', 'valor']


class InventarioProductoSerializer(serializers.ModelSerializer):
    """Serializer para el inventario de productos"""
    
    class Meta:
        model = InventarioProducto
        fields = ['sucursal', 'cantidad', 'ultima_actualizacion']
        
    def to_representation(self, instance):
        """Personalizar la representación del inventario"""
        data = super().to_representation(instance)
        data['sucursal'] = instance.sucursal.id
        return data


class ProductoFerremasSerializer(serializers.ModelSerializer):
    """Serializer principal para los productos de Ferremas"""
    precio = PrecioProductoSerializer(source='precios', many=True, read_only=True)
    inventario = InventarioProductoSerializer(source='inventarios', many=True, read_only=True)
    
    class Meta:
        model = Producto
        fields = ['id_producto', 'marca', 'modelo', 'nombre', 'precio', 'inventario']
        
    def to_representation(self, instance):
        """Personalizar la representación para que coincida con la estructura de MongoDB"""
        data = super().to_representation(instance)
        # Cambiar el nombre del campo para que coincida con la API original
        data['_id'] = data.pop('id_producto')
        return data


class ProductoInvSerializer(serializers.Serializer):
    """Serializer para crear productos con inventario simplificado"""
    _id = serializers.CharField(max_length=50)
    marca = serializers.CharField(max_length=100)
    modelo = serializers.CharField(max_length=100)
    nombre = serializers.CharField(max_length=200)
    precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad = serializers.IntegerField()
    
    def create(self, validated_data):
        """Crear un producto con su precio e inventario inicial"""
        # Extraer datos
        id_producto = validated_data.pop('_id')
        precio_valor = validated_data.pop('precio')
        cantidad = validated_data.pop('cantidad')
        sucursal_id = self.context.get('sucursal_id')
        
        # Crear el producto
        producto = Producto.objects.create(
            id_producto=id_producto,
            **validated_data
        )
        
        # Crear el precio inicial
        PrecioProducto.objects.create(
            producto=producto,
            valor=precio_valor,
            fecha=datetime.now()
        )
        
        # Crear el inventario inicial
        sucursal = Sucursal.objects.get(id=sucursal_id)
        InventarioProducto.objects.create(
            producto=producto,
            sucursal=sucursal,
            cantidad=cantidad,
            ultima_actualizacion=datetime.now()
        )
        
        return producto


class SucursalSerializer(serializers.ModelSerializer):
    """Serializer para las sucursales"""
    
    class Meta:
        model = Sucursal
        fields = ['id', 'nombre', 'password', 'calle', 'numeracion', 'comuna', 'region']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class AdministradorSerializer(serializers.ModelSerializer):
    """Serializer para los administradores"""
    
    class Meta:
        model = Administrador
        fields = ['id', 'usuario', 'password_admin']
        extra_kwargs = {
            'password_admin': {'write_only': True}
        }
