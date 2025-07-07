"""
Vistas para MongoDB - Ferremas API
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
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

# Configurar logger
logger = logging.getLogger(__name__)

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

# =================================
# FUNCIONES AUXILIARES BCCH Y WEBPAY
# =================================

def obtener_moneda(series_code):
    """Obtener valor de moneda desde BCCH API con caché"""
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    # Leer caché si existe
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    # Buscar en caché
    if series_code in cache and hoy in cache[series_code]:
        return cache[series_code][hoy]["valor"], None

    # Si no está en caché, consultar API
    try:
        siete = bcchapi.Siete(file="credenciales.txt")
        df = siete.cuadro(series=[series_code], nombres=["moneda"])
        if df.empty or df["moneda"].dropna().empty:
            return None, "No se encontraron datos de la moneda."
        valor = float(df["moneda"].dropna().iloc[-1])
        
        # Guardar en caché
        if series_code not in cache:
            cache[series_code] = {}
        cache[series_code][hoy] = {"valor": valor}
        
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
            
        return valor, None
    except Exception as e:
        if "credencial" in str(e).lower() or "login" in str(e).lower() or "usuario" in str(e).lower():
            return None, "Credenciales inválidas para el Banco Central de Chile."
        return None, f"Error al consultar el valor de la moneda: {str(e)}"

def generar_usuario_invitado_unico():
    """Generar un ID único para usuario invitado"""
    from .mongo_models import BoletaMongo
    while True:
        invitado_id = f"invitado{random.randint(100000, 999999)}"
        if not BoletaMongo.objects(usuario_id_unico=invitado_id):
            return invitado_id

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
                
                # Obtener información de stock por sucursal
                stock_por_sucursal = []
                for inv in producto.inventario:
                    stock_por_sucursal.append({
                        'sucursal_id': inv.sucursal,
                        'sucursal_nombre': inv.nombre_sucursal or f'Sucursal {inv.sucursal}',
                        'cantidad': inv.cantidad
                    })
                productos_data.append({
                    '_id': producto._id,
                    'marca': producto.marca,
                    'modelo': producto.modelo,
                    'nombre': producto.nombre,
                    'categoria': producto.categoria or 'Sin categoría',
                    'descripcion': producto.descripcion or 'Sin descripción',
                    'precio_actual': float(precio_actual) if precio_actual else 0.0,
                    'stock_total': stock_total,
                    'stock_por_sucursal': stock_por_sucursal,
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
        
        return render(request, 'inventario_sucursales.html', {
            'sucursales': sucursales_data,
            'sucursales_json': json.dumps(sucursales_data, ensure_ascii=False)
        })
    except Exception as e:
        return render(request, 'inventario_sucursales.html', {
            'sucursales': [],
            'sucursales_json': json.dumps([], ensure_ascii=False),
            'error': str(e)
        })

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

@api_view(['GET', 'POST'])
def webpay_return_view(request):
    """Vista para manejar el retorno de Webpay"""
    try:
        # Obtener los parámetros de retorno
        token = request.GET.get('token_ws') or request.POST.get('token_ws')
        
        if not token:
            return Response({
                'error': 'Token no proporcionado',
                'success': False
            }, status=400)
        
        # Aquí se procesaría el retorno de Webpay
        # Por ahora, solo devolvemos una respuesta básica
        return Response({
            'success': True,
            'token': token,
            'message': 'Retorno de Webpay procesado'
        })
        
    except Exception as e:
        logger.error(f"Error procesando retorno de Webpay: {str(e)}")
        return Response({
            'error': f'Error procesando retorno de Webpay: {str(e)}',
            'success': False
        }, status=500)

# ================================
# SISTEMA DE CARRITO DE COMPRAS
# ================================

def generar_usuario_id_unico(request):
    """Genera o recupera un ID único para el usuario basado en session"""
    if 'usuario_id_unico' not in request.session:
        request.session['usuario_id_unico'] = str(uuid.uuid4())
        request.session.save()
    return request.session['usuario_id_unico']

@api_view(['POST'])
def agregar_al_carrito_mongo(request):
    """Agregar producto al carrito de compras"""
    try:
        from .mongo_models import CarritoMongo
        
        # Obtener datos del request
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))
        sucursal_id = int(request.data.get('sucursal_id', 1))
        
        if not producto_id:
            return Response({
                'error': 'producto_id es requerido',
                'success': False
            }, status=400)
        
        # Generar ID único del usuario
        usuario_id_unico = generar_usuario_id_unico(request)
        
        # Verificar que el producto existe
        try:
            producto = ProductoMongo.objects.get(_id=producto_id)
        except ProductoMongo.DoesNotExist:
            return Response({
                'error': 'Producto no encontrado',
                'success': False
            }, status=404)
        
        # Verificar stock disponible en la sucursal
        stock_disponible = 0
        sucursal_nombre = "Sucursal Principal"
        
        for inv in producto.inventario:
            if inv.sucursal == sucursal_id:
                stock_disponible = inv.cantidad
                sucursal_nombre = inv.nombre_sucursal
                break
        
        if stock_disponible < cantidad:
            return Response({
                'error': f'Stock insuficiente. Disponible: {stock_disponible}',
                'success': False,
                'stock_disponible': stock_disponible
            }, status=400)
        
        # Verificar si el producto ya está en el carrito
        carrito_existente = CarritoMongo.objects(
            usuario_id_unico=usuario_id_unico,
            producto_id=producto_id,
            sucursal_id=sucursal_id
        ).first()
        
        if carrito_existente:
            # Actualizar cantidad
            nueva_cantidad = carrito_existente.cantidad + cantidad
            if nueva_cantidad > stock_disponible:
                return Response({
                    'error': f'Stock insuficiente. Máximo disponible: {stock_disponible}',
                    'success': False,
                    'stock_disponible': stock_disponible
                }, status=400)
            
            carrito_existente.cantidad = nueva_cantidad
            carrito_existente.save()
            
            return Response({
                'success': True,
                'message': f'Cantidad actualizada a {nueva_cantidad}',
                'item_id': str(carrito_existente.id),
                'cantidad_total': nueva_cantidad
            })
        else:
            # Crear nuevo item en el carrito
            carrito_item = CarritoMongo(
                producto_id=producto_id,
                producto_nombre=producto.nombre,
                producto_marca=producto.marca,
                producto_modelo=producto.modelo,
                precio_unitario=producto.get_precio_actual(),
                cantidad=cantidad,
                usuario_id_unico=usuario_id_unico,
                sucursal_id=sucursal_id,
                sucursal_nombre=sucursal_nombre
            )
            carrito_item.save()
            
            return Response({
                'success': True,
                'message': 'Producto agregado al carrito',
                'item_id': str(carrito_item.id),
                'cantidad': cantidad
            })
            
    except Exception as e:
        logger.error(f"Error agregando al carrito: {str(e)}")
        return Response({
            'error': f'Error interno: {str(e)}',
            'success': False
        }, status=500)

@api_view(['GET'])
def ver_carrito_mongo(request):
    """Ver contenido del carrito"""
    try:
        from .mongo_models import CarritoMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        
        # Obtener items del carrito
        carrito_items = CarritoMongo.objects(usuario_id_unico=usuario_id_unico)
        
        items_data = []
        total_precio = 0
        total_items = 0
        
        for item in carrito_items:
            subtotal = item.subtotal()
            items_data.append({
                'id': str(item.id),
                'producto_id': item.producto_id,
                'producto_nombre': item.producto_nombre,
                'producto_marca': item.producto_marca,
                'producto_modelo': item.producto_modelo,
                'precio_unitario': float(item.precio_unitario),
                'cantidad': item.cantidad,
                'subtotal': subtotal,
                'sucursal_id': item.sucursal_id,
                'sucursal_nombre': item.sucursal_nombre,
                'created_at': item.created_at.isoformat() if item.created_at else None
            })
            total_precio += subtotal
            total_items += item.cantidad
        
        return Response({
            'success': True,
            'carrito': {
                'items': items_data,
                'total_items': total_items,
                'total_precio': total_precio,
                'usuario_id': usuario_id_unico
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo carrito: {str(e)}")
        return Response({
            'error': f'Error interno: {str(e)}',
            'success': False
        }, status=500)

@api_view(['PUT'])
def actualizar_cantidad_carrito(request, item_id):
    """Actualizar cantidad de un item en el carrito"""
    try:
        from .mongo_models import CarritoMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        nueva_cantidad = int(request.data.get('cantidad', 1))
        
        if nueva_cantidad < 1:
            return Response({
                'error': 'La cantidad debe ser mayor a 0',
                'success': False
            }, status=400)
        
        # Obtener el item del carrito
        try:
            carrito_item = CarritoMongo.objects.get(
                id=item_id,
                usuario_id_unico=usuario_id_unico
            )
        except CarritoMongo.DoesNotExist:
            return Response({
                'error': 'Item no encontrado en el carrito',
                'success': False
            }, status=404)
        
        # Verificar stock disponible
        try:
            producto = ProductoMongo.objects.get(_id=carrito_item.producto_id)
            stock_disponible = 0
            
            for inv in producto.inventario:
                if inv.sucursal == carrito_item.sucursal_id:
                    stock_disponible = inv.cantidad
                    break
            
            if nueva_cantidad > stock_disponible:
                return Response({
                    'error': f'Stock insuficiente. Disponible: {stock_disponible}',
                    'success': False,
                    'stock_disponible': stock_disponible
                }, status=400)
            
            # Actualizar cantidad
            carrito_item.cantidad = nueva_cantidad
            carrito_item.save()
            
            return Response({
                'success': True,
                'message': 'Cantidad actualizada',
                'nueva_cantidad': nueva_cantidad,
                'nuevo_subtotal': carrito_item.subtotal()
            })
            
        except ProductoMongo.DoesNotExist:
            return Response({
                'error': 'Producto no encontrado',
                'success': False
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error actualizando cantidad: {str(e)}")
        return Response({
            'error': f'Error interno: {str(e)}',
            'success': False
        }, status=500)

@api_view(['DELETE'])
def eliminar_del_carrito_mongo(request, item_id):
    """Eliminar un item del carrito"""
    try:
        from .mongo_models import CarritoMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        
        # Obtener y eliminar el item
        try:
            carrito_item = CarritoMongo.objects.get(
                id=item_id,
                usuario_id_unico=usuario_id_unico
            )
            producto_nombre = carrito_item.producto_nombre
            carrito_item.delete()
            
            return Response({
                'success': True,
                'message': f'{producto_nombre} eliminado del carrito'
            })
            
        except CarritoMongo.DoesNotExist:
            return Response({
                'error': 'Item no encontrado en el carrito',
                'success': False
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error eliminando del carrito: {str(e)}")
        return Response({
            'error': f'Error interno: {str(e)}',
            'success': False
        }, status=500)

@api_view(['GET'])
def carrito_count_mongo(request):
    """Obtener el número de items en el carrito"""
    try:
        from .mongo_models import CarritoMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        
        # Contar items en el carrito
        total_items = 0
        carrito_items = CarritoMongo.objects(usuario_id_unico=usuario_id_unico)
        
        for item in carrito_items:
            total_items += item.cantidad
        
        return Response({
            'success': True,
            'count': total_items
        })
        
    except Exception as e:
        logger.error(f"Error contando items del carrito: {str(e)}")
        return Response({
            'error': f'Error interno: {str(e)}',
            'success': False,
            'count': 0
        }, status=500)

@api_view(['POST'])
def procesar_compra_mongo(request):
    """Procesar la compra y descontar del inventario"""
    try:
        from .mongo_models import CarritoMongo, BoletaMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        
        # Obtener items del carrito
        carrito_items = CarritoMongo.objects(usuario_id_unico=usuario_id_unico)
        
        if not carrito_items:
            return Response({
                'error': 'El carrito está vacío',
                'success': False
            }, status=400)
        
        # Validar stock antes de procesar
        productos_a_descontar = []
        total_compra = 0
        
        for item in carrito_items:
            try:
                producto = ProductoMongo.objects.get(_id=item.producto_id)
                
                # Buscar inventario en la sucursal
                inventario_encontrado = False
                for inv in producto.inventario:
                    if inv.sucursal == item.sucursal_id:
                        if inv.cantidad < item.cantidad:
                            return Response({
                                'error': f'Stock insuficiente para {item.producto_nombre}. Disponible: {inv.cantidad}',
                                'success': False
                            }, status=400)
                        
                        productos_a_descontar.append({
                            'producto': producto,
                            'inventario': inv,
                            'cantidad_descontar': item.cantidad,
                            'item_carrito': item
                        })
                        inventario_encontrado = True
                        break
                
                if not inventario_encontrado:
                    return Response({
                        'error': f'Producto {item.producto_nombre} no disponible en la sucursal',
                        'success': False
                    }, status=400)
                
                total_compra += item.subtotal()
                
            except ProductoMongo.DoesNotExist:
                return Response({
                    'error': f'Producto {item.producto_nombre} no encontrado',
                    'success': False
                }, status=404)
        
        # Procesar la compra: descontar del inventario
        detalles_boleta = []
        
        for item_data in productos_a_descontar:
            producto = item_data['producto']
            inventario = item_data['inventario']
            cantidad_descontar = item_data['cantidad_descontar']
            item_carrito = item_data['item_carrito']
            
            # Descontar del inventario
            inventario.cantidad -= cantidad_descontar
            inventario.ultima_actualizacion = datetime.now()
            
            # Preparar detalle de boleta
            detalles_boleta.append({
                'producto_id': item_carrito.producto_id,
                'producto_nombre': item_carrito.producto_nombre,
                'producto_marca': item_carrito.producto_marca,
                'producto_modelo': item_carrito.producto_modelo,
                'cantidad': cantidad_descontar,
                'precio': item_carrito.precio_unitario,
                'sucursal_id': item_carrito.sucursal_id,
                'sucursal_nombre': item_carrito.sucursal_nombre
            })
            
            # Guardar cambios en el producto
            producto.save()
        
        # Generar boleta
        codigo_boleta = f"BOL-{int(time.time())}-{random.randint(1000, 9999)}"
        numero_boleta = f"#{random.randint(10000, 99999)}"
        
        # Obtener la primera sucursal para la boleta (o podríamos manejar múltiples sucursales)
        primera_sucursal_id = productos_a_descontar[0]['item_carrito'].sucursal_id if productos_a_descontar else 1
        primera_sucursal_nombre = productos_a_descontar[0]['item_carrito'].sucursal_nombre if productos_a_descontar else "Sucursal Principal"
        
        # Calcular totales
        subtotal = total_compra
        iva = subtotal * 0.19
        total_con_iva = subtotal + iva
        
        # Crear detalles de boleta con el modelo correcto
        from .mongo_models import DetalleBoletaMongo
        detalles_objetos = []
        
        for detalle in detalles_boleta:
            detalle_obj = DetalleBoletaMongo(
                producto_id=detalle['producto_id'],
                producto_nombre=detalle['producto_nombre'],
                producto_marca=detalle['producto_marca'],
                producto_modelo=detalle['producto_modelo'],
                cantidad=detalle['cantidad'],
                precio=detalle['precio'],  # Usar 'precio' no 'precio_unitario'
                sucursal_id=detalle['sucursal_id'],
                sucursal_nombre=detalle['sucursal_nombre']
                # No incluir 'subtotal' porque es una propiedad calculada
            )
            detalles_objetos.append(detalle_obj)
        
        boleta = BoletaMongo(
            codigo=codigo_boleta,
            usuario_id_unico=usuario_id_unico,  # Usar usuario_id_unico, no usuario_id
            detalles=detalles_objetos,
            total=total_con_iva,  # Total con IVA incluido
            fecha=datetime.now(),
            sucursal_id=primera_sucursal_id,
            sucursal_nombre=primera_sucursal_nombre
        )
        boleta.save()
        
        # Limpiar el carrito
        CarritoMongo.objects(usuario_id_unico=usuario_id_unico).delete()
        
        # Si es una petición AJAX, devolver JSON con redirect
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
            return Response({
                'success': True,
                'message': 'Compra procesada exitosamente',
                'redirect_url': f'/api/compra/exitosa/?boleta={str(boleta.id)}&total={total_con_iva}&fecha={boleta.fecha.isoformat()}',
                'boleta': {
                    'id': str(boleta.id),
                    'codigo': codigo_boleta,
                    'total': total_con_iva,
                    'fecha': boleta.fecha.isoformat(),
                    'detalles_count': len(detalles_boleta)
                }
            })
        else:
            # Si es una petición directa, redirigir
            return redirect(f'/api/compra/exitosa/?boleta={str(boleta.id)}&total={total_con_iva}&fecha={boleta.fecha.isoformat()}')
        
    except Exception as e:
        logger.error(f"Error procesando compra: {str(e)}")
        return Response({
            'error': f'Error procesando compra: {str(e)}',
            'success': False
        }, status=500)

def ver_carrito_view(request):
    """Vista web para mostrar el carrito de compras"""
    try:
        from .mongo_models import CarritoMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        
        # Obtener items del carrito
        carrito_items = CarritoMongo.objects(usuario_id_unico=usuario_id_unico)
        
        items_data = []
        total_precio = 0
        total_items = 0
        items_por_sucursal = {}
        
        for item in carrito_items:
            subtotal = item.subtotal()
            
            # Obtener stock disponible para este producto en esta sucursal
            stock_disponible = 0
            try:
                producto = ProductoMongo.objects.get(_id=item.producto_id)
                for inv in producto.inventario:
                    if inv.sucursal == item.sucursal_id:
                        stock_disponible = inv.cantidad
                        break
            except ProductoMongo.DoesNotExist:
                stock_disponible = 0
                
            item_data = {
                'id': str(item.id),
                'producto_id': item.producto_id,
                'producto_nombre': item.producto_nombre,
                'producto_marca': item.producto_marca,
                'producto_modelo': item.producto_modelo,
                'precio_unitario': float(item.precio_unitario),
                'cantidad': item.cantidad,
                'subtotal': subtotal,
                'sucursal_id': item.sucursal_id,
                'sucursal_nombre': item.sucursal_nombre,
                'stock_disponible': stock_disponible
            }
            
            items_data.append(item_data)
            
            # Agrupar por sucursal
            if item.sucursal_nombre not in items_por_sucursal:
                items_por_sucursal[item.sucursal_nombre] = []
            items_por_sucursal[item.sucursal_nombre].append(item_data)
            
            total_precio += subtotal
            total_items += item.cantidad
        
        # Calcular IVA y total con IVA
        iva = total_precio * 0.19
        total_con_iva = total_precio + iva
        
        # Conversión de monedas
        valor_dolar = valor_euro = total_usd = total_eur = error_dolar = error_euro = None

        if request.GET.get("convertir") == "dolar":
            valor_dolar, error_dolar = obtener_moneda("F073.TCO.PRE.Z.D")
            if valor_dolar and total_con_iva:
                total_usd = float(total_con_iva) / float(valor_dolar)
        elif request.GET.get("convertir") == "euro":
            valor_euro, error_euro = obtener_moneda("F072.CLP.EUR.N.O.D")
            if valor_euro and total_con_iva:
                total_eur = float(total_con_iva) / float(valor_euro)
        
        context = {
            'carrito_items': items_data,
            'items_por_sucursal': items_por_sucursal,
            'total_items': total_items,
            'total_precio': total_precio,
            'iva': iva,
            'total_con_iva': total_con_iva,
            'valor_dolar': valor_dolar,
            'total_usd': total_usd,
            'error_dolar': error_dolar,
            'valor_euro': valor_euro,
            'total_eur': total_eur,
            'error_euro': error_euro,
            'usuario_id': usuario_id_unico
        }
        
        return render(request, 'carrito_mongo.html', context)
        
    except Exception as e:
        return render(request, 'carrito_mongo.html', {
            'carrito_items': [],
            'total_items': 0,
            'total_precio': 0,
            'error': str(e)
        })

@api_view(['PUT'])
def cambiar_sucursal_carrito(request, item_id):
    """Cambiar sucursal de un item del carrito"""
    try:
        from .mongo_models import CarritoMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        nueva_sucursal_id = int(request.data.get('sucursal_id'))
        
        # Obtener el item del carrito
        try:
            carrito_item = CarritoMongo.objects.get(
                id=item_id,
                usuario_id_unico=usuario_id_unico
            )
        except CarritoMongo.DoesNotExist:
            return Response({
                'error': 'Item no encontrado en el carrito',
                'success': False
            }, status=404)
        
        # Verificar que la sucursal existe
        try:
            sucursal = SucursalMongo.objects.get(_id=nueva_sucursal_id)
        except SucursalMongo.DoesNotExist:
            return Response({
                'error': 'Sucursal no encontrada',
                'success': False
            }, status=404)
        
        # Verificar stock disponible en la nueva sucursal
        try:
            producto = ProductoMongo.objects.get(_id=carrito_item.producto_id)
            stock_disponible = 0
            
            for inv in producto.inventario:
                if inv.sucursal == nueva_sucursal_id:
                    stock_disponible = inv.cantidad
                    break
            
            if stock_disponible < carrito_item.cantidad:
                return Response({
                    'error': f'Stock insuficiente en {sucursal.nombre}. Disponible: {stock_disponible}',
                    'success': False,
                    'stock_disponible': stock_disponible
                }, status=400)
            
            # Actualizar sucursal del item
            carrito_item.sucursal_id = nueva_sucursal_id
            carrito_item.sucursal_nombre = sucursal.nombre
            carrito_item.save()
            
            return Response({
                'success': True,
                'message': f'Sucursal cambiada a {sucursal.nombre}',
                'nueva_sucursal': {
                    'id': nueva_sucursal_id,
                    'nombre': sucursal.nombre
                }
            })
            
        except ProductoMongo.DoesNotExist:
            return Response({
                'error': 'Producto no encontrado',
                'success': False
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error cambiando sucursal: {str(e)}")
        return Response({
            'error': f'Error interno: {str(e)}',
            'success': False
        }, status=500)

def compra_exitosa_view(request):
    """Vista para mostrar confirmación de compra exitosa"""
    try:
        from .mongo_models import BoletaMongo
        
        # Obtener ID de la boleta desde parámetros GET
        boleta_id = request.GET.get('boleta', '')
        
        if not boleta_id:
            return render(request, 'compra_rechazada.html', {
                'error_mensaje': 'No se encontró información de la boleta',
                'mensaje': 'Error al cargar la confirmación de compra'
            })
        
        try:
            boleta = BoletaMongo.objects.get(id=boleta_id)
            
            context = {
                'boleta': boleta,
                'mensaje': 'Tu compra ha sido procesada exitosamente'
            }
            
            return render(request, 'compra_exitosa.html', context)
            
        except BoletaMongo.DoesNotExist:
            return render(request, 'compra_rechazada.html', {
                'error_mensaje': 'Boleta no encontrada',
                'mensaje': 'La boleta solicitada no existe'
            })
            
    except Exception as e:
        logger.error(f"Error en compra_exitosa_view: {str(e)}")
        return render(request, 'compra_rechazada.html', {
            'error_mensaje': 'Error al cargar la confirmación',
            'mensaje': 'Ha ocurrido un error al mostrar la confirmación de compra'
        })

def compra_rechazada_view(request):
    """Vista para mostrar compra rechazada"""
    error_mensaje = request.GET.get('error', 'Ha ocurrido un error al procesar tu compra')
    
    context = {
        'error_mensaje': error_mensaje,
        'mensaje': 'Tu compra no pudo ser procesada'
    }
    
    return render(request, 'compra_rechazada.html', context)

def ver_boleta_view(request, boleta_codigo):
    """Vista para mostrar los detalles de una boleta"""
    try:
        from .mongo_models import BoletaMongo
        
        boleta = BoletaMongo.objects.get(codigo=boleta_codigo)
        
        context = {
            'boleta': boleta,
            'detalles': boleta.detalles
        }
        
        return render(request, 'ver_boleta.html', context)
        
    except BoletaMongo.DoesNotExist:
        return render(request, 'compra_rechazada.html', {
            'error_mensaje': 'Boleta no encontrada',
            'mensaje': 'La boleta solicitada no existe'
        })
    except Exception as e:
        logger.error(f"Error mostrando boleta: {str(e)}")
        return render(request, 'compra_rechazada.html', {
            'error_mensaje': 'Error al cargar la boleta',
            'mensaje': 'Ha ocurrido un error al mostrar la boleta'
        })

def generar_boleta_pdf_view(request, boleta_id):
    """Vista para generar y descargar PDF de boleta compacto"""
    try:
        from .mongo_models import BoletaMongo
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from io import BytesIO
        from django.http import HttpResponse
        
        # Obtener la boleta
        boleta = BoletaMongo.objects.get(id=boleta_id)
        
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF compacto
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=30, leftMargin=30,
                              topMargin=30, bottomMargin=30)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        normal_style = styles['Normal']
        
        # Contenido del PDF
        story = []
        
        # Título
        title = Paragraph("BOLETA DE VENTA", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Información de la empresa
        empresa_info = Paragraph("<b>FERREMAS</b><br/>Tu ferretería de confianza<br/>Desde 1985", normal_style)
        story.append(empresa_info)
        story.append(Spacer(1, 12))
        
        # Información de la boleta
        boleta_info = [
            ['Número de Boleta:', boleta.codigo],
            ['Fecha:', boleta.fecha.strftime('%d/%m/%Y %H:%M')],
            ['Cliente:', boleta.usuario_id_unico],
            ['Sucursal:', boleta.sucursal_nombre]
        ]
        
        boleta_table = Table(boleta_info, colWidths=[2*inch, 3*inch])
        boleta_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(boleta_table)
        story.append(Spacer(1, 20))
        
        # Tabla de productos
        productos_data = [['Producto', 'Cant.', 'Precio Unit.', 'Total']]
        
        for detalle in boleta.detalles:
            productos_data.append([
                f"{detalle.producto_nombre}\n{detalle.producto_marca} {detalle.producto_modelo}",
                str(detalle.cantidad),
                f"${detalle.precio:,.0f}",
                f"${detalle.subtotal:,.0f}"
            ])
        
        productos_table = Table(productos_data, colWidths=[3*inch, 0.7*inch, 1*inch, 1*inch])
        productos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(productos_table)
        story.append(Spacer(1, 20))
        
        # Totales
        totales_data = [
            ['Subtotal:', f"${boleta.subtotal:,.0f}"],
            ['IVA (19%):', f"${boleta.iva:,.0f}"],
            ['TOTAL:', f"${boleta.total:,.0f}"]
        ]
        
        totales_table = Table(totales_data, colWidths=[3*inch, 1.5*inch])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 2), (-1, 2), 8),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
        ]))
        
        story.append(totales_table)
        story.append(Spacer(1, 30))
        
        # Mensaje de agradecimiento
        agradecimiento = Paragraph("<i>¡Gracias por su compra!</i><br/>Ferremas - Tu ferretería de confianza", normal_style)
        story.append(agradecimiento)
        
        # Generar el PDF
        doc.build(story)
        
        # Preparar respuesta HTTP
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="boleta_{boleta.codigo}.pdf"'
        
        return response
        
    except BoletaMongo.DoesNotExist:
        return HttpResponse("Boleta no encontrada", status=404)
    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        return HttpResponse(f"Error generando PDF: {str(e)}", status=500)

# =================================
# FUNCIONES DE WEBPAY
# =================================

def iniciar_pago_webpay(request):
    """Iniciar pago con Webpay"""
    try:
        from .mongo_models import CarritoMongo
        
        usuario_id_unico = generar_usuario_id_unico(request)
        carrito_items = CarritoMongo.objects(usuario_id_unico=usuario_id_unico)
        
        # Calcular total
        total = sum(item.subtotal() for item in carrito_items)
        total_con_iva = total * 1.19
        amount = int(total_con_iva)  # Webpay requiere entero
        
        if amount <= 0:
            return render(request, 'ferremas/pago_fallido_mongo.html', {
                'error': 'El carrito está vacío o el monto es inválido.'
            })

        buy_order = f"orden-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session_id = "test-session"
        return_url = request.build_absolute_uri(reverse('webpay_respuesta'))
        
        options = WebpayOptions(
            commerce_code="597055555532",
            api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
            integration_type=IntegrationType.TEST
        )
        
        tx = Transaction(options)
        
        try:
            response = tx.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=amount,
                return_url=return_url
            )
            return redirect(response['url'] + '?token_ws=' + response['token'])
            
        except TransbankError as e:
            logger.error(f"Error de Transbank al iniciar el pago: {e.message}")
            return render(request, 'ferremas/pago_fallido_mongo.html', {
                'error': str(e.message)
            })
        except Exception as e:
            logger.error(f"Error inesperado al iniciar el pago: {e}")
            return render(request, 'ferremas/pago_fallido_mongo.html', {
                'error': str(e)
            })
            
    except Exception as e:
        logger.error(f"Error general en iniciar_pago_webpay: {e}")
        return render(request, 'ferremas/pago_fallido_mongo.html', {
            'error': f'Error interno: {str(e)}'
        })

def webpay_respuesta(request):
    """Procesar respuesta de Webpay"""
    token = request.GET.get('token_ws')
    if not token:
        return render(request, 'ferremas/pago_fallido_mongo.html', {
            'error': 'No se recibió el token de Transbank.'
        })
    
    options = WebpayOptions(
        commerce_code="597055555532",
        api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
        integration_type=IntegrationType.TEST
    )
    
    tx = Transaction(options)
    
    try:
        response = tx.commit(token)
        
        if response and response.get('response_code') == 0:
            # Pago exitoso - procesar compra
            try:
                from .mongo_models import CarritoMongo, BoletaMongo, DetalleBoletaMongo
                
                usuario_id_unico = generar_usuario_id_unico(request)
                carrito_items = CarritoMongo.objects(usuario_id_unico=usuario_id_unico)
                
                if not carrito_items:
                    return render(request, 'ferremas/pago_fallido_mongo.html', {
                        'error': 'No hay items en el carrito'
                    })
                
                # Calcular totales
                total = sum(item.subtotal() for item in carrito_items)
                total_con_iva = total * 1.19
                
                # Generar código de boleta
                codigo_boleta = str(uuid.uuid4())[:8].upper()
                
                # Crear boleta
                boleta = BoletaMongo(
                    codigo=codigo_boleta,
                    usuario_id_unico=usuario_id_unico,
                    total=total_con_iva,
                    metodo_pago="webpay",
                    transbank_token=token,
                    transbank_response_code=response.get('response_code'),
                    fecha=datetime.now()
                )
                
                # Agregar detalles de la boleta
                detalles = []
                for item in carrito_items:
                    detalle = DetalleBoletaMongo(
                        producto_id=item.producto_id,
                        producto_nombre=item.producto_nombre,
                        producto_marca=item.producto_marca,
                        producto_modelo=item.producto_modelo,
                        cantidad=item.cantidad,
                        precio_unitario=item.precio_unitario,
                        subtotal=item.subtotal(),
                        sucursal_id=item.sucursal_id,
                        sucursal_nombre=item.sucursal_nombre
                    )
                    detalles.append(detalle)
                
                boleta.detalles = detalles
                boleta.save()
                
                # Actualizar inventario
                for item in carrito_items:
                    try:
                        producto = ProductoMongo.objects.get(_id=item.producto_id)
                        for inv in producto.inventario:
                            if inv.sucursal == item.sucursal_id:
                                inv.cantidad = max(inv.cantidad - item.cantidad, 0)
                                break
                        producto.save()
                    except ProductoMongo.DoesNotExist:
                        logger.warning(f"Producto {item.producto_id} no encontrado para actualizar stock")
                
                # Limpiar carrito
                carrito_items.delete()
                
                return render(request, 'ferremas/pago_exitoso_mongo.html', {
                    'response': response,
                    'boleta': boleta,
                    'detalles': detalles
                })
                
            except Exception as e:
                logger.error(f"Error procesando compra exitosa: {e}")
                return render(request, 'ferremas/pago_fallido_mongo.html', {
                    'error': f'Error procesando la compra: {str(e)}'
                })
        else:
            # Pago rechazado
            error_message = response.get('response_code_description', 'Pago rechazado o fallido.') if response else 'Respuesta vacía de Transbank.'
            return render(request, 'ferremas/pago_fallido_mongo.html', {
                'error': error_message,
                'response': response
            })

    except TransbankError as e:
        logger.error(f"Error Transbank al procesar la respuesta: {e.message}")
        return render(request, 'ferremas/pago_fallido_mongo.html', {
            'error': f"Error Transbank: {e.message}"
        })
    except Exception as e:
        logger.error(f"Error inesperado al procesar la respuesta de Transbank: {e}")
        return render(request, 'ferremas/pago_fallido_mongo.html', {
            'error': str(e)
        })

# ==============================
# BOLETAS API - Consultas de Boletas
# ==============================

@api_view(['GET'])
def boletas_api(request):
    """
    API para consultar boletas con filtros avanzados
    
    Parámetros de consulta:
    - codigo: Código específico de boleta
    - usuario_id: ID del usuario
    - fecha_desde: Fecha desde (YYYY-MM-DD)
    - fecha_hasta: Fecha hasta (YYYY-MM-DD)
    - estado: Estado de la boleta (completada, pendiente, cancelada)
    - sucursal_id: ID de sucursal
    - metodo_pago: Método de pago (webpay, efectivo, transferencia)
    - limit: Límite de resultados (default: 50)
    - offset: Offset para paginación (default: 0)
    """
    try:
        from .mongo_models import BoletaMongo
        from datetime import datetime
        
        # Parámetros de filtrado
        codigo = request.GET.get('codigo')
        usuario_id = request.GET.get('usuario_id')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        estado = request.GET.get('estado')
        sucursal_id = request.GET.get('sucursal_id')
        metodo_pago = request.GET.get('metodo_pago')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        # Construir query
        query = {}
        
        if codigo:
            query['codigo'] = codigo
        
        if usuario_id:
            query['usuario_id_unico'] = usuario_id
        
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query['fecha__gte'] = fecha_desde_obj
            except ValueError:
                return Response({
                    'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                # Agregar 23:59:59 para incluir todo el día
                fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
                query['fecha__lte'] = fecha_hasta_obj
            except ValueError:
                return Response({
                    'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if estado:
            if estado not in ['pendiente', 'completada', 'cancelada']:
                return Response({
                    'error': 'Estado inválido. Use: pendiente, completada, cancelada'
                }, status=status.HTTP_400_BAD_REQUEST)
            query['estado'] = estado
        
        if sucursal_id:
            try:
                query['sucursal_id'] = int(sucursal_id)
            except ValueError:
                return Response({
                    'error': 'sucursal_id debe ser un número'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if metodo_pago:
            if metodo_pago not in ['webpay', 'efectivo', 'transferencia']:
                return Response({
                    'error': 'Método de pago inválido. Use: webpay, efectivo, transferencia'
                }, status=status.HTTP_400_BAD_REQUEST)
            query['metodo_pago'] = metodo_pago
        
        # Validar límites
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1
        
        # Ejecutar consulta
        boletas_query = BoletaMongo.objects(**query).order_by('-fecha')
        total_count = boletas_query.count()
        boletas = boletas_query[offset:offset + limit]
        
        # Serializar resultados
        boletas_data = []
        for boleta in boletas:
            detalles_data = []
            try:
                for detalle in boleta.detalles:
                    detalles_data.append({
                        'producto_id': detalle.producto_id,
                        'producto_nombre': detalle.producto_nombre,
                        'producto_marca': detalle.producto_marca,
                        'producto_modelo': detalle.producto_modelo,
                        'cantidad': detalle.cantidad,
                        'precio_unitario': float(detalle.precio_final),
                        'subtotal': detalle.subtotal(),
                        'sucursal_id': detalle.sucursal_id,
                        'sucursal_nombre': detalle.sucursal_nombre
                    })
            except Exception as e:
                logger.error(f"Error procesando detalles de boleta {boleta.codigo}: {e}")
                # Continuar con detalles vacíos si hay error
                detalles_data = []
            
            boleta_data = {
                'id': str(boleta.id),
                'codigo': boleta.codigo,
                'usuario_id_unico': boleta.usuario_id_unico,
                'fecha': boleta.fecha.isoformat(),
                'total': float(boleta.total),
                'subtotal': round(boleta.subtotal, 2),
                'iva': round(boleta.iva, 2),
                'estado': boleta.estado,
                'metodo_pago': boleta.metodo_pago,
                'sucursal_id': boleta.sucursal_id,
                'sucursal_nombre': boleta.sucursal_nombre,
                'detalles': detalles_data,
                'webpay_info': {
                    'token': boleta.webpay_token,
                    'buy_order': boleta.webpay_buy_order,
                    'session_id': boleta.webpay_session_id,
                    'amount': float(boleta.webpay_amount) if boleta.webpay_amount else None,
                    'authorization_code': boleta.webpay_authorization_code
                } if boleta.webpay_token else None
            }
            boletas_data.append(boleta_data)
        
        # Respuesta con metadata
        response_data = {
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'next': offset + limit if offset + limit < total_count else None,
            'previous': offset - limit if offset > 0 else None,
            'results': boletas_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en boletas_api: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def boleta_detalle_api(request, boleta_codigo):
    """
    API para obtener detalles de una boleta específica
    """
    try:
        from .mongo_models import BoletaMongo
        
        boleta = BoletaMongo.objects.get(codigo=boleta_codigo)
        
        # Serializar detalles
        detalles_data = []
        try:
            for detalle in boleta.detalles:
                detalles_data.append({
                    'producto_id': detalle.producto_id,
                    'producto_nombre': detalle.producto_nombre,
                    'producto_marca': detalle.producto_marca,
                    'producto_modelo': detalle.producto_modelo,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_final),
                    'subtotal': detalle.subtotal(),
                    'sucursal_id': detalle.sucursal_id,
                    'sucursal_nombre': detalle.sucursal_nombre
                })
        except Exception as e:
            logger.error(f"Error procesando detalles de boleta {boleta.codigo}: {e}")
            # Continuar con detalles vacíos si hay error
            detalles_data = []
        
        boleta_data = {
            'id': str(boleta.id),
            'codigo': boleta.codigo,
            'usuario_id_unico': boleta.usuario_id_unico,
            'fecha': boleta.fecha.isoformat(),
            'total': float(boleta.total),
            'subtotal': round(boleta.subtotal, 2),
            'iva': round(boleta.iva, 2),
            'estado': boleta.estado,
            'metodo_pago': boleta.metodo_pago,
            'sucursal_id': boleta.sucursal_id,
            'sucursal_nombre': boleta.sucursal_nombre,
            'detalles': detalles_data,
            'webpay_info': {
                'token': boleta.webpay_token,
                'buy_order': boleta.webpay_buy_order,
                'session_id': boleta.webpay_session_id,
                'amount': float(boleta.webpay_amount) if boleta.webpay_amount else None,
                'authorization_code': boleta.webpay_authorization_code
            } if boleta.webpay_token else None
        }
        
        return Response(boleta_data, status=status.HTTP_200_OK)
        
    except BoletaMongo.DoesNotExist:
        return Response({
            'error': 'Boleta no encontrada',
            'codigo': boleta_codigo
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error en boleta_detalle_api: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def boletas_estadisticas_api(request):
    """
    API para obtener estadísticas de boletas
    """
    try:
        from .mongo_models import BoletaMongo
        from datetime import datetime, timedelta
        
        # Parámetros opcionales
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        sucursal_id = request.GET.get('sucursal_id')
        
        # Query base
        query = {}
        
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query['fecha__gte'] = fecha_desde_obj
            except ValueError:
                return Response({
                    'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
                query['fecha__lte'] = fecha_hasta_obj
            except ValueError:
                return Response({
                    'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if sucursal_id:
            try:
                query['sucursal_id'] = int(sucursal_id)
            except ValueError:
                return Response({
                    'error': 'sucursal_id debe ser un número'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener boletas
        boletas = BoletaMongo.objects(**query)
        
        # Calcular estadísticas
        total_boletas = boletas.count()
        total_ventas = 0
        
        # Calcular total de ventas de forma segura
        for boleta in boletas:
            try:
                total_ventas += float(boleta.total)
            except (ValueError, TypeError):
                logger.warning(f"Error procesando total de boleta {boleta.codigo}")
                continue
        
        # Estadísticas por estado
        estadisticas_estado = {}
        for estado in ['completada', 'pendiente', 'cancelada']:
            count = boletas.filter(estado=estado).count()
            estadisticas_estado[estado] = count
        
        # Estadísticas por método de pago
        estadisticas_metodo_pago = {}
        for metodo in ['webpay', 'efectivo', 'transferencia']:
            count = boletas.filter(metodo_pago=metodo).count()
            monto = 0
            for boleta in boletas.filter(metodo_pago=metodo):
                try:
                    monto += float(boleta.total)
                except (ValueError, TypeError):
                    continue
            estadisticas_metodo_pago[metodo] = {
                'cantidad': count,
                'monto_total': round(monto, 2)
            }
        
        # Estadísticas por sucursal
        estadisticas_sucursal = {}
        for boleta in boletas:
            try:
                sucursal_id = boleta.sucursal_id
                if sucursal_id not in estadisticas_sucursal:
                    estadisticas_sucursal[sucursal_id] = {
                        'nombre': boleta.sucursal_nombre,
                        'cantidad': 0,
                        'monto_total': 0
                    }
                estadisticas_sucursal[sucursal_id]['cantidad'] += 1
                estadisticas_sucursal[sucursal_id]['monto_total'] += float(boleta.total)
            except (ValueError, TypeError, AttributeError):
                continue
        
        # Redondear montos
        for sucursal_data in estadisticas_sucursal.values():
            sucursal_data['monto_total'] = round(sucursal_data['monto_total'], 2)
        
        # Promedio de venta
        promedio_venta = round(total_ventas / total_boletas, 2) if total_boletas > 0 else 0
        
        response_data = {
            'resumen': {
                'total_boletas': total_boletas,
                'total_ventas': round(total_ventas, 2),
                'promedio_venta': promedio_venta
            },
            'por_estado': estadisticas_estado,
            'por_metodo_pago': estadisticas_metodo_pago,
            'por_sucursal': estadisticas_sucursal,
            'filtros_aplicados': {
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'sucursal_id': sucursal_id
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en boletas_estadisticas_api: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
