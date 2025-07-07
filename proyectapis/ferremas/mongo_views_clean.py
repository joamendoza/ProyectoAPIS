"""
Vistas para MongoDB - Ferremas API
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
import uuid
import random
import time
import hashlib
import logging
from reportlab.pdfgen import canvas
from bson import ObjectId

from .mongo_config import configure_mongoengine, get_database
from .mongo_models import ProductoMongo, SucursalMongo, AdministradorMongo, Precio, Inventario
from .mongo_serializers import (
    ProductoMongoSerializer,
    ProductoFerremasMongoSerializer,
    ProductoCreateSerializer,
    ProductoVentaSerializer,
    SucursalMongoSerializer,
    AdministradorMongoSerializer
)

# Importar integraciones originales
import bcchapi
import pandas as pd
import os

# Importar Transbank
try:
    from transbank.common.options import WebpayOptions
    from transbank.webpay.webpay_plus.transaction import Transaction
    from transbank.common.integration_type import IntegrationType
    from transbank.error.transbank_error import TransbankError
    WEBPAY_AVAILABLE = True
    print("✅ Transbank importado correctamente")
except ImportError as e:
    print(f"⚠️  Warning: Could not import Transbank: {e}")
    WEBPAY_AVAILABLE = False

# Importar BCCH API
try:
    import bcchapi
    BCCH_AVAILABLE = True
    print("✅ BCCH API importado correctamente")
except ImportError as e:
    print(f"⚠️  Warning: Could not import BCCH API: {e}")
    BCCH_AVAILABLE = False

# Importar integraciones personalizadas (fallback)
try:
    from .webpay_integration import WebpayIntegration, iniciar_pago_webpay
    WEBPAY_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import webpay integration: {e}")
    WEBPAY_INTEGRATION_AVAILABLE = False

try:
    from .bcch_integration import BCCHIntegration, bcch_integration, obtener_tipo_cambio_api, convertir_moneda_api, obtener_indicadores_api
    BCCH_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import BCCH integration: {e}")
    BCCH_INTEGRATION_AVAILABLE = False

# Constantes
CACHE_FILE = "moneda_cache.json"

# Configurar MongoEngine al importar
configure_mongoengine()

def validar_credenciales_sucursal_mongo(sucursal_id, password):
    """Valida las credenciales de una sucursal en MongoDB"""
    try:
        sucursal = SucursalMongo.objects.get(_id=sucursal_id, password=password)
        return sucursal
    except SucursalMongo.DoesNotExist:
        return None

def validar_credenciales_admin_mongo(admin_password):
    """Valida las credenciales de administrador en MongoDB"""
    try:
        admin = AdministradorMongo.objects.get(password=admin_password)
        return admin
    except AdministradorMongo.DoesNotExist:
        return None

@api_view(['GET'])
def root_mongo(request):
    """Endpoint raíz de la API de Ferremas con MongoDB"""
    return Response({"message": "API de Ferremas con MongoDB Atlas"})

@api_view(['GET'])
def read_productos_mongo(request):
    """
    Endpoint para consultar productos en MongoDB
    Opciones:
    1. Sin parámetros: Todos los productos sin inventario
    2. Solo productoid: Documento completo del producto
    3. Solo sucursalid: Inventario de la sucursal especificada
    4. Ambos: Inventario del producto en la sucursal especificada
    """
    sucursal_id = request.GET.get('sucursalid')
    producto_id = request.GET.get('productoid')
    
    try:
        # Opción 1: Todos los productos con inventario completo
        if not sucursal_id and not producto_id:
            productos = ProductoMongo.objects.all()
            productos_data = []
            for producto in productos:
                productos_data.append({
                    'marca': producto.marca,
                    'modelo': producto.modelo,
                    'nombre': producto.nombre,
                    'categoria': producto.categoria,
                    'descripcion': producto.descripcion,
                    'precio': [{'fecha': p.fecha, 'valor': str(p.valor)} for p in producto.precio],
                    'inventario': [{
                        'sucursal': inv.sucursal,
                        'nombre_sucursal': inv.nombre_sucursal,
                        'cantidad': inv.cantidad,
                        'ultima_actualizacion': inv.ultima_actualizacion
                    } for inv in producto.inventario],
                    '_id': producto._id
                })
            return Response(productos_data)
        
        # Opción 2: Producto específico
        elif producto_id and not sucursal_id:
            try:
                producto = ProductoMongo.objects.get(_id=producto_id)
                producto_data = {
                    'marca': producto.marca,
                    'modelo': producto.modelo,
                    'nombre': producto.nombre,
                    'precio': [{'fecha': p.fecha, 'valor': str(p.valor)} for p in producto.precio],
                    'inventario': [{
                        'sucursal': inv.sucursal,
                        'nombre_sucursal': inv.nombre_sucursal,
                        'cantidad': inv.cantidad,
                        'ultima_actualizacion': inv.ultima_actualizacion
                    } for inv in producto.inventario],
                    '_id': producto._id
                }
                return Response(producto_data)
            except ProductoMongo.DoesNotExist:
                return Response(
                    {"detail": "Producto no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Opción 3: Inventario de sucursal
        elif sucursal_id and not producto_id:
            try:
                sucursal_id = int(sucursal_id)
                sucursal = SucursalMongo.objects.get(_id=sucursal_id)
                
                # Buscar productos que tengan inventario en esta sucursal
                productos_con_inventario = []
                productos = ProductoMongo.objects.all()
                
                for producto in productos:
                    for inv in producto.inventario:
                        if inv.sucursal == sucursal_id:
                            productos_con_inventario.append({
                                "productoid": producto._id,
                                "nombre": producto.nombre,
                                "cantidad": inv.cantidad,
                                "precio": str(producto.get_precio_actual()),
                                "ultima_actualizacion": inv.ultima_actualizacion
                            })
                
                return Response({
                    "sucursal": sucursal_id,
                    "productos": productos_con_inventario
                })
            except SucursalMongo.DoesNotExist:
                return Response(
                    {"detail": "Sucursal no encontrada"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Opción 4: Inventario específico
        else:
            try:
                sucursal_id = int(sucursal_id)
                producto = ProductoMongo.objects.get(_id=producto_id)
                
                # Buscar inventario específico
                for inv in producto.inventario:
                    if inv.sucursal == sucursal_id:
                        return Response({
                            "productoid": producto._id,
                            "nombre": producto.nombre,
                            "sucursal": sucursal_id,
                            "cantidad": inv.cantidad,
                            "precio": str(producto.get_precio_actual()),
                            "ultima_actualizacion": inv.ultima_actualizacion
                        })
                
                return Response(
                    {"detail": "Producto no encontrado en esta sucursal"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ProductoMongo.DoesNotExist:
                return Response(
                    {"detail": "Producto no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
    
    except Exception as e:
        return Response(
            {"detail": f"Error interno: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def create_producto_mongo(request, sucursal_id):
    """Crear nuevo producto en MongoDB"""
    try:
        # Validar credenciales
        password = request.headers.get('password')
        admin_password = request.headers.get('adminpassword')
        
        if not password or not admin_password:
            return Response(
                {"detail": "Credenciales requeridas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        sucursal = validar_credenciales_sucursal_mongo(sucursal_id, password)
        admin = validar_credenciales_admin_mongo(admin_password)
        
        if not sucursal or not admin:
            return Response(
                {"detail": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Validar datos
        serializer = ProductoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Verificar si el producto ya existe
        if ProductoMongo.objects.filter(_id=data['_id']).first():
            return Response(
                {"detail": "Producto ya existe"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear producto
        producto = ProductoMongo(
            _id=data['_id'],
            marca=data['marca'],
            modelo=data['modelo'],
            nombre=data['nombre'],
            categoria=data.get('categoria', ''),
            descripcion=data.get('descripcion', ''),
            precio=[Precio(valor=data['precio'])],
            inventario=[Inventario(
                sucursal=sucursal_id,
                nombre_sucursal=sucursal.nombre,
                cantidad=data.get('cantidad', 0)
            )]
        )
        producto.save()
        
        return Response(
            {"message": "Producto creado exitosamente", "productoid": producto._id},
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return Response(
            {"detail": f"Error al crear producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def read_sucursales_mongo(request):
    """Consultar todas las sucursales en MongoDB"""
    try:
        sucursales = SucursalMongo.objects.all()
        sucursales_data = []
        for sucursal in sucursales:
            sucursales_data.append({
                '_id': sucursal._id,
                'nombre': sucursal.nombre,
                'calle': sucursal.calle,
                'numeracion': sucursal.numeracion,
                'comuna': sucursal.comuna,
                'region': sucursal.region,
                'created_at': sucursal.created_at
            })
        return Response(sucursales_data)
    except Exception as e:
        return Response(
            {"detail": f"Error al consultar sucursales: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def productos_venta_view(request):
    """Vista para mostrar productos en página de venta"""
    try:
        productos = ProductoMongo.objects.all()
        productos_data = []
        
        for producto in productos:
            productos_data.append({
                'id': producto._id,
                'marca': producto.marca,
                'modelo': producto.modelo,
                'nombre': producto.nombre,
                'categoria': producto.categoria or 'Sin categoría',
                'descripcion': producto.descripcion or 'Sin descripción',
                'precio_actual': float(producto.get_precio_actual()),
                'stock_total': producto.get_stock_total(),
                'imagen_url': f"https://via.placeholder.com/300x200?text={producto.marca}+{producto.modelo}".replace(' ', '+')
            })
        
        return render(request, 'productos_venta.html', {'productos': productos_data})
    except Exception as e:
        return render(request, 'productos_venta.html', {'productos': [], 'error': str(e)})

@api_view(['GET'])
def productos_venta_api(request):
    """API para obtener productos para la página de venta"""
    try:
        # Configurar MongoEngine si no está configurado
        configure_mongoengine()
        
        # Intentar obtener productos
        productos = ProductoMongo.objects.all()
        productos_data = []
        
        for producto in productos:
            try:
                precio_actual = producto.get_precio_actual()
                stock_total = producto.get_stock_total()
                
                productos_data.append({
                    '_id': producto._id,
                    'marca': producto.marca,
                    'modelo': producto.modelo,
                    'nombre': producto.nombre,
                    'categoria': producto.categoria or 'Sin categoría',
                    'descripcion': producto.descripcion or 'Sin descripción',
                    'precio_actual': float(precio_actual) if precio_actual else 0.0,
                    'stock_total': stock_total,
                    'imagen_url': f"https://via.placeholder.com/300x200?text={producto.marca}+{producto.modelo}".replace(' ', '+')
                })
            except Exception as producto_error:
                print(f"Error procesando producto {producto._id}: {producto_error}")
                continue
        
        return Response(productos_data)
        
    except Exception as e:
        print(f"Error en productos_venta_api: {str(e)}")
        # En caso de error, devolver una respuesta con productos de ejemplo
        productos_ejemplo = [
            {
                '_id': 'EJEMPLO-001',
                'marca': 'Bosch',
                'modelo': 'GSB 13 RE',
                'nombre': 'Taladro Percutor 13mm 600W',
                'categoria': 'herramientas',
                'descripcion': 'Taladro percutor profesional con motor de 600W',
                'precio_actual': 89990.0,
                'stock_total': 15,
                'imagen_url': 'https://via.placeholder.com/300x200?text=Bosch+GSB+13+RE'
            },
            {
                '_id': 'EJEMPLO-002',
                'marca': 'DeWalt',
                'modelo': 'DWE575',
                'nombre': 'Sierra Circular 7-1/4" 1600W',
                'categoria': 'herramientas',
                'descripcion': 'Sierra circular de 7-1/4" con motor de 1600W',
                'precio_actual': 125990.0,
                'stock_total': 8,
                'imagen_url': 'https://via.placeholder.com/300x200?text=DeWalt+DWE575'
            }
        ]
        return Response(productos_ejemplo)

@api_view(['GET'])
def inventario_por_sucursal(request, sucursal_id):
    """
    Endpoint para consultar el inventario completo de una sucursal específica
    """
    try:
        # Verificar que la sucursal existe
        try:
            sucursal = SucursalMongo.objects.get(_id=sucursal_id)
        except SucursalMongo.DoesNotExist:
            return Response(
                {"detail": "Sucursal no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Buscar todos los productos que tienen inventario en esta sucursal
        productos_en_sucursal = []
        productos = ProductoMongo.objects.all()
        
        for producto in productos:
            for inv in producto.inventario:
                if inv.sucursal == sucursal_id:
                    productos_en_sucursal.append({
                        "_id": producto._id,
                        "marca": producto.marca,
                        "modelo": producto.modelo,
                        "nombre": producto.nombre,
                        "categoria": producto.categoria,
                        "descripcion": producto.descripcion,
                        "precio_actual": float(producto.get_precio_actual()) if producto.get_precio_actual() else 0.0,
                        "cantidad_disponible": inv.cantidad,
                        "ultima_actualizacion": inv.ultima_actualizacion,
                        "sucursal_info": {
                            "id": sucursal._id,
                            "nombre": sucursal.nombre,
                            "comuna": sucursal.comuna
                        }
                    })
                    break
        
        return Response({
            "sucursal": {
                "id": sucursal._id,
                "nombre": sucursal.nombre,
                "calle": sucursal.calle,
                "numeracion": sucursal.numeracion,
                "comuna": sucursal.comuna,
                "region": sucursal.region
            },
            "total_productos": len(productos_en_sucursal),
            "productos": productos_en_sucursal
        })
        
    except Exception as e:
        return Response(
            {"detail": f"Error al consultar inventario: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def producto_en_sucursales(request, producto_id):
    """
    Endpoint para consultar la disponibilidad de un producto en todas las sucursales
    """
    try:
        # Verificar que el producto existe
        try:
            producto = ProductoMongo.objects.get(_id=producto_id)
        except ProductoMongo.DoesNotExist:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener información de sucursales
        sucursales = {s._id: s for s in SucursalMongo.objects.all()}
        
        # Crear respuesta con inventario por sucursal
        inventario_sucursales = []
        for inv in producto.inventario:
            sucursal = sucursales.get(inv.sucursal)
            if sucursal:
                inventario_sucursales.append({
                    "sucursal_id": inv.sucursal,
                    "sucursal_nombre": inv.nombre_sucursal,
                    "sucursal_comuna": sucursal.comuna,
                    "cantidad_disponible": inv.cantidad,
                    "ultima_actualizacion": inv.ultima_actualizacion,
                    "estado_stock": "Disponible" if inv.cantidad > 0 else "Sin stock"
                })
        
        return Response({
            "producto": {
                "_id": producto._id,
                "marca": producto.marca,
                "modelo": producto.modelo,
                "nombre": producto.nombre,
                "categoria": producto.categoria,
                "descripcion": producto.descripcion,
                "precio_actual": float(producto.get_precio_actual()) if producto.get_precio_actual() else 0.0
            },
            "stock_total": producto.get_stock_total(),
            "disponibilidad_sucursales": inventario_sucursales
        })
        
    except Exception as e:
        return Response(
            {"detail": f"Error al consultar producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
def actualizar_stock_sucursal(request, sucursal_id, producto_id):
    """
    Endpoint para actualizar el stock de un producto en una sucursal específica
    """
    try:
        # Validar credenciales de sucursal
        password = request.headers.get('password')
        if not password:
            return Response(
                {"detail": "Password de sucursal requerido"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        sucursal = validar_credenciales_sucursal_mongo(sucursal_id, password)
        if not sucursal:
            return Response(
                {"detail": "Credenciales de sucursal inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar que el producto existe
        try:
            producto = ProductoMongo.objects.get(_id=producto_id)
        except ProductoMongo.DoesNotExist:
            return Response(
                {"detail": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener nueva cantidad del request
        nueva_cantidad = request.data.get('cantidad')
        if nueva_cantidad is None:
            return Response(
                {"detail": "Campo 'cantidad' requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            nueva_cantidad = int(nueva_cantidad)
            if nueva_cantidad < 0:
                return Response(
                    {"detail": "La cantidad no puede ser negativa"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"detail": "La cantidad debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar el inventario en la sucursal
        inventario_actualizado = False
        for inv in producto.inventario:
            if inv.sucursal == sucursal_id:
                cantidad_anterior = inv.cantidad
                inv.cantidad = nueva_cantidad
                inv.ultima_actualizacion = datetime.now()
                inventario_actualizado = True
                break
        
        # Si no existe inventario para esta sucursal, crearlo
        if not inventario_actualizado:
            nuevo_inventario = Inventario(
                sucursal=sucursal_id,
                nombre_sucursal=sucursal.nombre,
                cantidad=nueva_cantidad,
                ultima_actualizacion=datetime.now()
            )
            producto.inventario.append(nuevo_inventario)
            cantidad_anterior = 0
        
        # Actualizar fecha de modificación del producto
        producto.updated_at = datetime.now()
        producto.save()
        
        return Response({
            "message": "Stock actualizado exitosamente",
            "producto": {
                "_id": producto._id,
                "nombre": producto.nombre
            },
            "sucursal": {
                "id": sucursal_id,
                "nombre": sucursal.nombre
            },
            "stock_anterior": cantidad_anterior,
            "stock_nuevo": nueva_cantidad,
            "fecha_actualizacion": datetime.now()
        })
        
    except Exception as e:
        return Response(
            {"detail": f"Error al actualizar stock: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def inventario_sucursales_view(request):
    """Vista para mostrar inventario por sucursales"""
    try:
        # Obtener todas las sucursales
        sucursales = SucursalMongo.objects.all()
        sucursales_data = []
        
        for sucursal in sucursales:
            # Obtener productos de esta sucursal
            productos_sucursal = []
            productos = ProductoMongo.objects.all()
            
            for producto in productos:
                for inv in producto.inventario:
                    if inv.sucursal == sucursal._id:
                        productos_sucursal.append({
                            'id': producto._id,
                            'nombre': producto.nombre,
                            'marca': producto.marca,
                            'modelo': producto.modelo,
                            'categoria': producto.categoria or 'Sin categoría',
                            'precio_actual': float(producto.get_precio_actual()),
                            'cantidad': inv.cantidad,
                            'ultima_actualizacion': inv.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if inv.ultima_actualizacion else 'N/A'
                        })
                        break
            
            sucursales_data.append({
                'id': sucursal._id,
                'nombre': sucursal.nombre,
                'direccion': f"{sucursal.calle} {sucursal.numeracion}, {sucursal.comuna}, {sucursal.region}",
                'total_productos': len(productos_sucursal),
                'productos': productos_sucursal
            })
        
        return render(request, 'inventario_sucursales.html', {'sucursales': sucursales_data})
    except Exception as e:
        return render(request, 'inventario_sucursales.html', {'sucursales': [], 'error': str(e)})

def crear_producto_form_view(request):
    """Vista para mostrar formulario de creación de productos"""
    try:
        sucursales = SucursalMongo.objects.all()
        
        if request.method == 'POST':
            # Procesar el formulario
            try:
                sucursal_id = int(request.POST.get('sucursal_id'))
                password = request.POST.get('password')
                admin_password = request.POST.get('admin_password')
                
                # Validar credenciales
                sucursal = validar_credenciales_sucursal_mongo(sucursal_id, password)
                admin = validar_credenciales_admin_mongo(admin_password)
                
                if not sucursal or not admin:
                    return render(request, 'crear_producto_form.html', {
                        'sucursales': sucursales,
                        'error': 'Credenciales inválidas'
                    })
                
                # Crear producto
                producto_data = {
                    '_id': request.POST.get('producto_id'),
                    'marca': request.POST.get('marca'),
                    'modelo': request.POST.get('modelo'),
                    'nombre': request.POST.get('nombre'),
                    'categoria': request.POST.get('categoria'),
                    'descripcion': request.POST.get('descripcion'),
                    'precio': float(request.POST.get('precio')),
                    'cantidad': int(request.POST.get('cantidad', 0))
                }
                
                # Verificar si el producto ya existe
                if ProductoMongo.objects.filter(_id=producto_data['_id']).first():
                    return render(request, 'crear_producto_form.html', {
                        'sucursales': sucursales,
                        'error': 'El producto ya existe'
                    })
                
                # Crear producto
                producto = ProductoMongo(
                    _id=producto_data['_id'],
                    marca=producto_data['marca'],
                    modelo=producto_data['modelo'],
                    nombre=producto_data['nombre'],
                    categoria=producto_data['categoria'],
                    descripcion=producto_data['descripcion'],
                    precio=[Precio(valor=producto_data['precio'])],
                    inventario=[Inventario(
                        sucursal=sucursal_id,
                        nombre_sucursal=sucursal.nombre,
                        cantidad=producto_data['cantidad']
                    )]
                )
                producto.save()
                
                return render(request, 'crear_producto_form.html', {
                    'sucursales': sucursales,
                    'success': f'Producto {producto._id} creado exitosamente'
                })
                
            except Exception as e:
                return render(request, 'crear_producto_form.html', {
                    'sucursales': sucursales,
                    'error': f'Error al crear producto: {str(e)}'
                })
        
        return render(request, 'crear_producto_form.html', {'sucursales': sucursales})
    except Exception as e:
        return render(request, 'crear_producto_form.html', {'sucursales': [], 'error': str(e)})

def actualizar_stock_form_view(request):
    """Vista para mostrar formulario de actualización de stock"""
    try:
        sucursales = SucursalMongo.objects.all()
        productos = ProductoMongo.objects.all()
        
        if request.method == 'POST':
            try:
                sucursal_id = int(request.POST.get('sucursal_id'))
                producto_id = request.POST.get('producto_id')
                password = request.POST.get('password')
                nueva_cantidad = int(request.POST.get('cantidad'))
                
                # Validar credenciales
                sucursal = validar_credenciales_sucursal_mongo(sucursal_id, password)
                if not sucursal:
                    return render(request, 'actualizar_stock_form.html', {
                        'sucursales': sucursales,
                        'productos': productos,
                        'error': 'Credenciales de sucursal inválidas'
                    })
                
                # Obtener producto
                producto = ProductoMongo.objects.get(_id=producto_id)
                
                # Actualizar stock
                inventario_actualizado = False
                for inv in producto.inventario:
                    if inv.sucursal == sucursal_id:
                        cantidad_anterior = inv.cantidad
                        inv.cantidad = nueva_cantidad
                        inv.ultima_actualizacion = datetime.now()
                        inventario_actualizado = True
                        break
                
                if not inventario_actualizado:
                    nuevo_inventario = Inventario(
                        sucursal=sucursal_id,
                        nombre_sucursal=sucursal.nombre,
                        cantidad=nueva_cantidad,
                        ultima_actualizacion=datetime.now()
                    )
                    producto.inventario.append(nuevo_inventario)
                    cantidad_anterior = 0
                
                producto.updated_at = datetime.now()
                producto.save()
                
                return render(request, 'actualizar_stock_form.html', {
                    'sucursales': sucursales,
                    'productos': productos,
                    'success': f'Stock de {producto.nombre} actualizado de {cantidad_anterior} a {nueva_cantidad} unidades'
                })
                
            except Exception as e:
                return render(request, 'actualizar_stock_form.html', {
                    'sucursales': sucursales,
                    'productos': productos,
                    'error': f'Error al actualizar stock: {str(e)}'
                })
        
        return render(request, 'actualizar_stock_form.html', {
            'sucursales': sucursales,
            'productos': productos
        })
    except Exception as e:
        return render(request, 'actualizar_stock_form.html', {
            'sucursales': [],
            'productos': [],
            'error': str(e)
        })

# ================================
# BCCH API FALLBACK ENDPOINTS
# ================================

# Fallback functions for BCCH integration if import fails
if not BCCH_INTEGRATION_AVAILABLE:
    @api_view(['GET'])
    def obtener_tipo_cambio_api(request):
        """Fallback API endpoint para obtener tipos de cambio"""
        return Response({
            'error': 'BCCH integration not available',
            'success': False,
            'tipo_cambio': 800,  # Default fallback rate
            'fecha': datetime.now().isoformat(),
            'moneda_origen': 'USD',
            'moneda_destino': 'CLP'
        }, status=503)

    @api_view(['GET', 'POST'])
    def convertir_moneda_api(request):
        """Fallback API endpoint para convertir monedas"""
        return Response({
            'error': 'BCCH integration not available',
            'success': False,
            'monto_convertido': 0,
            'fecha': datetime.now().isoformat()
        }, status=503)

    @api_view(['GET'])
    def obtener_indicadores_api(request):
        """Fallback API endpoint para obtener indicadores económicos"""
        return Response({
            'error': 'BCCH integration not available',
            'success': False,
            'indicadores': {},
            'fecha': datetime.now().isoformat()
        }, status=503)
