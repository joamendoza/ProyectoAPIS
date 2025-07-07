from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import Http404
from django.db.models import Q
from datetime import datetime

from inventario.models import Producto, PrecioProducto, InventarioProducto, Sucursal
from carrito.models import Administrador
from .serializers import (
    ProductoFerremasSerializer, 
    ProductoInvSerializer,
    SucursalSerializer,
    AdministradorSerializer
)


# Funciones auxiliares para validación
def validar_credenciales_sucursal(sucursal_id, password):
    """Valida las credenciales de una sucursal"""
    try:
        sucursal = Sucursal.objects.get(id=sucursal_id, password=password)
        return sucursal
    except Sucursal.DoesNotExist:
        return None


def validar_credenciales_admin(admin_password):
    """Valida las credenciales del administrador"""
    try:
        admin = Administrador.objects.get(password_admin=admin_password)
        return admin
    except Administrador.DoesNotExist:
        return None


@api_view(['GET'])
def root(request):
    """Endpoint raíz de la API de Ferremas"""
    return Response({"message": "API de Ferremas integrada en Django"})


@api_view(['GET'])
def read_productos_by_sucursal(request):
    """
    Endpoint flexible para consultar productos con 4 opciones:
    1. Sin parámetros: Todos los productos sin inventario
    2. Solo productoid: Documento completo del producto
    3. Solo sucursalid: Inventario de la sucursal especificada
    4. Ambos: Inventario del producto en la sucursal especificada
    """
    sucursal_id = request.GET.get('sucursalid')
    producto_id = request.GET.get('productoid')
    
    try:
        # Opción 1: Mostrar todos los productos sin inventario
        if not sucursal_id and not producto_id:
            productos = Producto.objects.prefetch_related('precios').all()
            # Serializar sin inventario
            serializer = ProductoFerremasSerializer(productos, many=True)
            data = serializer.data
            # Limpiar inventario
            for item in data:
                item['inventario'] = []
            return Response(data)
        
        # Opción 2: Solo productoid - Documento completo
        elif producto_id and not sucursal_id:
            try:
                producto = Producto.objects.prefetch_related(
                    'precios', 'inventarios__sucursal'
                ).get(id_producto=producto_id)
                serializer = ProductoFerremasSerializer(producto)
                return Response([serializer.data])
            except Producto.DoesNotExist:
                return Response(
                    {"detail": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Opción 3: Solo sucursalid - Inventario de esa sucursal
        elif sucursal_id and not producto_id:
            try:
                sucursal = Sucursal.objects.get(id=sucursal_id)
                productos = Producto.objects.prefetch_related(
                    'precios', 'inventarios__sucursal'
                ).filter(inventarios__sucursal=sucursal)
                
                serializer = ProductoFerremasSerializer(productos, many=True)
                data = serializer.data
                
                # Filtrar inventario solo para la sucursal especificada
                for item in data:
                    item['inventario'] = [
                        inv for inv in item['inventario'] 
                        if inv['sucursal'] == int(sucursal_id)
                    ]
                
                return Response(data)
            except Sucursal.DoesNotExist:
                return Response(
                    {"detail": "Sucursal no encontrada"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Opción 4: Ambos - Inventario del producto en la sucursal
        else:
            try:
                sucursal = Sucursal.objects.get(id=sucursal_id)
                producto = Producto.objects.prefetch_related(
                    'precios', 'inventarios__sucursal'
                ).get(
                    id_producto=producto_id,
                    inventarios__sucursal=sucursal
                )
                
                serializer = ProductoFerremasSerializer(producto)
                data = serializer.data
                
                # Filtrar inventario solo para la sucursal especificada
                data['inventario'] = [
                    inv for inv in data['inventario'] 
                    if inv['sucursal'] == int(sucursal_id)
                ]
                
                return Response([data])
            except (Sucursal.DoesNotExist, Producto.DoesNotExist):
                return Response(
                    {"detail": "Producto no encontrado en la sucursal especificada"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
    except Exception as e:
        return Response(
            {"detail": f"Error en la consulta: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_producto(request, sucursal_id):
    """
    Crea un nuevo producto asociado a una sucursal específica.
    Requiere contraseña de administrador general.
    """
    # Obtener contraseñas de los headers
    password = request.headers.get('password')
    admin_password = request.headers.get('adminpassword')
    
    if not password or not admin_password:
        return Response(
            {"detail": "Se requieren los headers 'password' y 'adminpassword'"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar credenciales
    sucursal = validar_credenciales_sucursal(sucursal_id, password)
    if not sucursal:
        return Response(
            {"detail": "Credenciales de sucursal inválidas"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    admin = validar_credenciales_admin(admin_password)
    if not admin:
        return Response(
            {"detail": "Credenciales de administrador inválidas"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Crear el producto
    serializer = ProductoInvSerializer(
        data=request.data,
        context={'sucursal_id': sucursal_id}
    )
    
    if serializer.is_valid():
        try:
            producto = serializer.save()
            # Retornar el producto creado con el formato completo
            response_serializer = ProductoFerremasSerializer(producto)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"detail": f"Error al crear producto: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_inventario(request, sucursal_id):
    """
    Crea un nuevo inventario para un producto en una sucursal específica.
    """
    # Obtener contraseña del header
    password = request.headers.get('password')
    if not password:
        return Response(
            {"detail": "Se requiere el header 'password'"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar credenciales de sucursal
    sucursal = validar_credenciales_sucursal(sucursal_id, password)
    if not sucursal:
        return Response(
            {"detail": "Credenciales de sucursal inválidas"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Obtener datos del request
    producto_id = request.data.get('productoid')
    cantidad = request.data.get('cantidad')
    
    if not producto_id or cantidad is None:
        return Response(
            {"detail": "Se requieren 'productoid' y 'cantidad'"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verificar que el producto existe
        producto = Producto.objects.get(id_producto=producto_id)
        
        # Verificar que no existe ya inventario para este producto en esta sucursal
        if InventarioProducto.objects.filter(producto=producto, sucursal=sucursal).exists():
            return Response(
                {"detail": "Ya existe inventario para este producto en esta sucursal"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el inventario
        InventarioProducto.objects.create(
            producto=producto,
            sucursal=sucursal,
            cantidad=cantidad,
            ultima_actualizacion=datetime.now()
        )
        
        # Retornar el producto actualizado
        response_serializer = ProductoFerremasSerializer(producto)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except Producto.DoesNotExist:
        return Response(
            {"detail": "Producto no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": f"Error al crear inventario: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def update_inventario(request, sucursal_id, producto_id):
    """
    Actualiza el inventario de un producto en una sucursal específica.
    """
    # Obtener contraseña del header
    password = request.headers.get('password')
    if not password:
        return Response(
            {"detail": "Se requiere el header 'password'"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar credenciales de sucursal
    sucursal = validar_credenciales_sucursal(sucursal_id, password)
    if not sucursal:
        return Response(
            {"detail": "Credenciales de sucursal inválidas"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Obtener cantidad del request
    cantidad = request.data.get('cantidad')
    if cantidad is None:
        return Response(
            {"detail": "Se requiere 'cantidad'"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Buscar el inventario específico
        inventario = InventarioProducto.objects.get(
            producto__id_producto=producto_id,
            sucursal=sucursal
        )
        
        # Actualizar el inventario
        inventario.cantidad = cantidad
        inventario.ultima_actualizacion = datetime.now()
        inventario.save()
        
        # Retornar el producto actualizado
        response_serializer = ProductoFerremasSerializer(inventario.producto)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except InventarioProducto.DoesNotExist:
        return Response(
            {"detail": "Producto o sucursal no encontrados"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": f"Error al actualizar inventario: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_producto(request, producto_id):
    """
    Elimina un producto de la base de datos.
    Requiere contraseña de administrador general.
    """
    # Obtener contraseña del header
    admin_password = request.headers.get('adminpassword')
    if not admin_password:
        return Response(
            {"detail": "Se requiere el header 'adminpassword'"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar credenciales de administrador
    admin = validar_credenciales_admin(admin_password)
    if not admin:
        return Response(
            {"detail": "Credenciales de administrador inválidas"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Buscar y eliminar el producto
        producto = Producto.objects.get(id_producto=producto_id)
        producto.delete()
        
        return Response(
            {"message": "Producto eliminado exitosamente"},
            status=status.HTTP_200_OK
        )
        
    except Producto.DoesNotExist:
        return Response(
            {"detail": "Producto no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": f"Error al eliminar producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def read_sucursales(request):
    """
    Endpoint para consultar todas las sucursales disponibles
    """
    try:
        sucursales = Sucursal.objects.all()
        serializer = SucursalSerializer(sucursales, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {"detail": f"Error al consultar sucursales: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
