"""
Vistas para el carrito usando MongoDB
"""
import random
import bcchapi
import pandas as pd
import json
import os
import logging
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import uuid

# Importar modelos de MongoDB
from ferremas.mongo_models import ProductoMongo, CarritoMongo, BoletaMongo, DetalleBoletaMongo, DetalleBoletaMongoDoc, SucursalMongo

##COMO TE ODIO TRANSBANK##
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType
from transbank.error.transbank_error import TransbankError

CACHE_FILE = "moneda_cache.json"

# Configurar logger
logger = logging.getLogger(__name__)

def obtener_moneda(series_code):
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
    """Genera un ID único para usuario invitado"""
    while True:
        invitado_id = f"invitado{random.randint(100000, 999999)}"
        if not BoletaMongo.objects(usuario_id_unico=invitado_id).first():
            return invitado_id

def get_usuario_id_unico(request):
    """Obtiene o genera un ID único para el usuario"""
    if 'usuario_id_unico' not in request.session:
        # Para testing, usar siempre el mismo ID de usuario de prueba
        test_user_id = 'test_user_template'
        request.session['usuario_id_unico'] = test_user_id
    return request.session['usuario_id_unico']

def lista_productos_mongo(request):
    """Lista productos y muestra resumen del carrito - MongoDB"""
    productos = ProductoMongo.objects.all()
    search_query = request.GET.get('search', '')
    
    if search_query:
        productos = productos.filter(
            nombre__icontains=search_query
        )
    
    # Información del carrito para Webpay
    usuario_id = get_usuario_id_unico(request)
    carrito = CarritoMongo.objects(usuario_id_unico=usuario_id)
    
    total = sum(item.subtotal() for item in carrito)
    total_items = sum(item.cantidad for item in carrito)
    
    context = {
        'productos': productos,
        'search_query': search_query,
        # Información del carrito para Webpay
        'carrito': carrito,
        'total': total,
        'total_precio': total,
        'total_items': total_items,
    }
    return render(request, 'carrito/lista_productos_mongo.html', context)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def agregar_al_carrito_mongo(request, producto_id):
    """Agregar producto al carrito - MongoDB"""
    print(f"=== DEBUG: agregar_al_carrito_mongo ===")
    print(f"Método: {request.method}")
    print(f"Producto ID: {producto_id}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Request body: {request.body}")
    
    try:
        producto = ProductoMongo.objects.get(_id=producto_id)
    except ProductoMongo.DoesNotExist:
        error_msg = "Producto no encontrado."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'success': False, 'error': error_msg}, status=404)
        messages.error(request, error_msg)
        return redirect('lista_productos_mongo')
    
    usuario_id = get_usuario_id_unico(request)
    
    # Obtener sucursal_id del cuerpo de la petición (si es POST) o buscar automáticamente
    sucursal_id_solicitado = None
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            sucursal_id_solicitado = data.get('sucursal_id')
            print(f"Sucursal ID solicitado desde POST: {sucursal_id_solicitado} (tipo: {type(sucursal_id_solicitado)})")
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error parseando JSON: {e}")
            print(f"Request body: {request.body}")
    else:
        print("Método GET - no hay sucursal_id específica solicitada")
    
    print(f"Inventario del producto:")
    for inv in producto.inventario:
        print(f"  Sucursal {inv.sucursal} ({inv.nombre_sucursal}): {inv.cantidad} unidades")
    
    # Buscar la sucursal específica solicitada o la primera con stock disponible
    sucursal_con_stock = None
    if sucursal_id_solicitado is not None:
        # Convertir sucursal_id_solicitado a entero para comparación
        try:
            sucursal_id_int = int(sucursal_id_solicitado)
            print(f"Buscando sucursal específica: {sucursal_id_solicitado} -> {sucursal_id_int}")
        except (ValueError, TypeError):
            print(f"Error convirtiendo sucursal_id a entero: {sucursal_id_solicitado}")
            sucursal_id_int = None
        
        if sucursal_id_int is not None:
            for inv in producto.inventario:
                print(f"  Comparando {inv.sucursal} (tipo: {type(inv.sucursal)}) == {sucursal_id_int} (tipo: {type(sucursal_id_int)}): {inv.sucursal == sucursal_id_int}")
                if inv.sucursal == sucursal_id_int and inv.cantidad > 0:
                    sucursal_con_stock = inv
                    print(f"  ✓ Encontrada sucursal solicitada: {inv.nombre_sucursal}")
                    break
        
        if not sucursal_con_stock:
            error_msg = f"{producto.nombre} no tiene stock disponible en la sucursal seleccionada."
            print(f"Error: {error_msg}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect('lista_productos_mongo')
    else:
        # Buscar la primera sucursal que tenga stock disponible (comportamiento original)
        print("Buscando primera sucursal con stock disponible")
        for inv in producto.inventario:
            if inv.cantidad > 0:
                sucursal_con_stock = inv
                print(f"  ✓ Usando sucursal automática: {inv.nombre_sucursal}")
                break
    
    if not sucursal_con_stock:
        error_msg = f"{producto.nombre} no tiene stock disponible en ninguna sucursal."
        print(f"Error: {error_msg}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('lista_productos_mongo')
    
    sucursal_id = sucursal_con_stock.sucursal
    sucursal_nombre = sucursal_con_stock.nombre_sucursal
    stock_sucursal = sucursal_con_stock.cantidad
    
    # Buscar si ya existe el item en el carrito para esta sucursal
    carrito_item = CarritoMongo.objects(
        usuario_id_unico=usuario_id,
        producto_id=producto_id,
        sucursal_id=sucursal_id
    ).first()
    
    if carrito_item:
        # Verificar stock de la sucursal específica
        if carrito_item.cantidad < stock_sucursal:
            carrito_item.cantidad += 1
            carrito_item.save()
            success_msg = f"¡{producto.nombre} añadido al carrito desde {sucursal_nombre}! (Stock: {stock_sucursal})"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
        else:
            error_msg = f"No puedes añadir más de {stock_sucursal} unidades de {producto.nombre} desde {sucursal_nombre}."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
    else:
        # Crear nuevo item
        CarritoMongo(
            producto_id=producto_id,
            producto_nombre=producto.nombre,
            producto_marca=producto.marca,
            producto_modelo=producto.modelo,
            precio_unitario=producto.get_precio_actual(),
            cantidad=1,
            usuario_id_unico=usuario_id,
            sucursal_id=sucursal_id,
            sucursal_nombre=sucursal_nombre
        ).save()
        success_msg = f"¡{producto.nombre} añadido al carrito desde {sucursal_nombre}! (Stock: {stock_sucursal})"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'success': True, 'message': success_msg})
        messages.success(request, success_msg)
    
    return redirect('ver_carrito_mongo')

def ver_carrito_mongo(request):
    """Ver carrito de compras - MongoDB"""
    usuario_id = get_usuario_id_unico(request)
    carrito = CarritoMongo.objects(usuario_id_unico=usuario_id)
    
    total = sum(item.subtotal() for item in carrito)
    total_items = sum(item.cantidad for item in carrito)
    
    # Preparar los datos del carrito para el template
    carrito_items = []
    items_por_sucursal = {}
    
    for item in carrito:
        # Obtener el stock real del producto en la sucursal
        stock_disponible = 0
        try:
            producto = ProductoMongo.objects(_id=item.producto_id).first()
            if producto:
                for inv in producto.inventario:
                    if inv.sucursal == item.sucursal_id:
                        stock_disponible = inv.cantidad
                        break
        except Exception as e:
            print(f"Error al obtener stock para {item.producto_nombre}: {e}")
            stock_disponible = 0
        
        item_data = {
            'id': str(item.id),
            'producto_nombre': item.producto_nombre,
            'producto_marca': item.producto_marca,
            'producto_modelo': item.producto_modelo,
            'precio_unitario': item.precio_unitario,
            'cantidad': item.cantidad,
            'subtotal': item.subtotal(),
            'stock_disponible': stock_disponible,  # Stock real de la sucursal
            'sucursal_nombre': item.sucursal_nombre,
            'sucursal_id': item.sucursal_id,
        }
        
        carrito_items.append(item_data)
        
        # Agrupar por sucursal
        sucursal_nombre = item.sucursal_nombre
        if sucursal_nombre not in items_por_sucursal:
            items_por_sucursal[sucursal_nombre] = []
        items_por_sucursal[sucursal_nombre].append(item_data)
    
    # Calcular totales sin IVA
    total_decimal = Decimal(str(total))
    
    valor_dolar = valor_euro = total_usd = total_eur = error_dolar = error_euro = None

    if request.GET.get("convertir") == "dolar":
        valor_dolar, error_dolar = obtener_moneda("F073.TCO.PRE.Z.D")
        if valor_dolar and total:
            total_usd = float(total_decimal) / float(valor_dolar)
    elif request.GET.get("convertir") == "euro":
        valor_euro, error_euro = obtener_moneda("F072.CLP.EUR.N.O.D")
        if valor_euro and total:
            total_eur = float(total_decimal) / float(valor_euro)

    return render(request, "carrito_mongo.html", {
        "carrito": carrito,
        "carrito_items": carrito_items,  # Datos estructurados para el template
        "items_por_sucursal": items_por_sucursal,  # Items agrupados por sucursal
        "total": total,
        "total_precio": total,  # Precio total
        "total_items": total_items,  # Cantidad total de items
        "valor_dolar": valor_dolar,
        "total_usd": total_usd,
        "error_dolar": error_dolar,
        "valor_euro": valor_euro,
        "total_eur": total_eur,
        "error_euro": error_euro,
    })

def actualizar_cantidad_mongo(request, item_id):
    """Actualizar cantidad de un item del carrito - MongoDB"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nueva_cantidad = int(data.get('cantidad', 1))
            
            usuario_id = get_usuario_id_unico(request)
            item = CarritoMongo.objects(id=item_id, usuario_id_unico=usuario_id).first()
            
            if not item:
                return JsonResponse({'error': 'Item no encontrado'}, status=404)
            
            # Validar cantidad
            if nueva_cantidad <= 0:
                item.delete()
                return JsonResponse({'success': True, 'message': 'Item eliminado del carrito'})
            
            # Validar stock disponible
            try:
                producto = ProductoMongo.objects(_id=item.producto_id).first()
                if producto:
                    stock_disponible = 0
                    for inv in producto.inventario:
                        if inv.sucursal == item.sucursal_id:
                            stock_disponible = inv.cantidad
                            break
                    
                    if nueva_cantidad > stock_disponible:
                        return JsonResponse({
                            'success': False,
                            'error': f'Stock insuficiente. Solo hay {stock_disponible} unidades disponibles en esta sucursal.'
                        }, status=400)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Producto no encontrado'
                    }, status=404)
            except Exception as e:
                print(f"Error al validar stock: {e}")
                # Si hay error al validar stock, permitir la actualización pero con warning
                pass
            
            # Actualizar cantidad
            item.cantidad = nueva_cantidad
            item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cantidad actualizada',
                'nuevo_subtotal': item.subtotal(),
                'nueva_cantidad': item.cantidad
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def eliminar_del_carrito_mongo(request, item_id):
    """Eliminar item del carrito - MongoDB"""
    if request.method == 'POST':
        try:
            usuario_id = get_usuario_id_unico(request)
            item = CarritoMongo.objects(id=item_id, usuario_id_unico=usuario_id).first()
            
            if not item:
                return JsonResponse({'success': False, 'error': 'Item no encontrado'}, status=404)
            
            item.delete()
            return JsonResponse({'success': True, 'message': 'Item eliminado del carrito'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def iniciar_pago_webpay_mongo(request):
    """Iniciar pago con Webpay - MongoDB"""
    usuario_id = get_usuario_id_unico(request)
    carrito = CarritoMongo.objects(usuario_id_unico=usuario_id)
    
    total = sum(item.subtotal() for item in carrito)
    amount = int(total)  # Total sin IVA para Webpay
    
    if amount <= 0:
        return render(request, 'pago_fallido_mongo.html', {'error': 'El carrito está vacío o el monto es inválido.'})

    buy_order = f"orden-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    session_id = usuario_id
    return_url = request.build_absolute_uri(reverse('webpay_respuesta_mongo'))
    
    options = WebpayOptions(
        commerce_code="597055555532",  # Cambiar por API key
        api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",  # Cambiar por API key real
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
        
        # Guardar información del pago en sesión
        request.session['webpay_buy_order'] = buy_order
        request.session['webpay_amount'] = amount
        
        return redirect(response['url'] + '?token_ws=' + response['token'])
        
    except TransbankError as e:
        print(f"Error de Transbank al iniciar el pago: {e.message}")
        return render(request, 'pago_fallido_mongo.html', {'error': str(e.message)})
    except Exception as e:
        print(f"Error inesperado al iniciar el pago: {e}")
        return render(request, 'pago_fallido_mongo.html', {'error': str(e)})

def webpay_respuesta_mongo(request):
    """Procesar respuesta de Webpay - MongoDB"""
    token = request.GET.get('token_ws')
    
    if not token:
        return render(request, 'pago_fallido_mongo.html', {'error': 'Token no recibido'})
    
    options = WebpayOptions(
        commerce_code="597055555532",
        api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
        integration_type=IntegrationType.TEST
    )
    
    tx = Transaction(options)
    
    try:
        response = tx.commit(token)
        
        # Debug: Imprimir la respuesta completa
        print(f"=== DEBUG WEBPAY RESPONSE ===")
        print(f"Respuesta completa: {response}")
        print(f"Tipo de respuesta: {type(response)}")
        print(f"Keys disponibles: {list(response.keys()) if hasattr(response, 'keys') else 'No keys'}")
        print(f"Status: {response.get('status')} (tipo: {type(response.get('status'))})")
        print(f"Response Code: {response.get('response_code')} (tipo: {type(response.get('response_code'))})")
        
        # Verificar múltiples condiciones para pago exitoso
        status = response.get('status', '')
        response_code = response.get('response_code', None)
        
        # Normalizar status (puede venir en mayúsculas o minúsculas)
        status_upper = str(status).upper() if status else ''
        status_lower = str(status).lower() if status else ''
        
        # Normalizar response_code (puede venir como string o int)
        try:
            response_code_int = int(response_code) if response_code is not None else -1
        except (ValueError, TypeError):
            response_code_int = -1
        
        # También verificar como string por si viene como '0'
        response_code_str = str(response_code) if response_code is not None else ''
        
        print(f"Status original: '{status}' (tipo: {type(status)})")
        print(f"Status normalizado: '{status_upper}'")
        print(f"Response Code original: '{response_code}' (tipo: {type(response_code)})")
        print(f"Response Code normalizado: {response_code_int}")
        print(f"Response Code como string: '{response_code_str}'")
        
        # Condiciones para pago exitoso - ser muy permisivo con diferentes formatos
        conditions = [
            status_upper == 'AUTHORIZED',
            status_lower == 'authorized',
            status_upper == 'APPROVED',
            status_lower == 'approved',
            status_upper == 'SUCCESS',
            status_lower == 'success',
            response_code_int == 0,
            response_code_str == '0',
            response_code_str.upper() == 'SUCCESS',
            response_code_str.upper() == 'APPROVED'
        ]
        
        is_success = any(conditions)
        
        print(f"Condiciones evaluadas:")
        condition_names = [
            'status_upper == AUTHORIZED',
            'status_lower == authorized',
            'status_upper == APPROVED',
            'status_lower == approved',
            'status_upper == SUCCESS',
            'status_lower == success',
            'response_code_int == 0',
            'response_code_str == "0"',
            'response_code_str.upper() == SUCCESS',
            'response_code_str.upper() == APPROVED'
        ]
        
        for i, condition in enumerate(conditions):
            print(f"  {condition_names[i]}: {condition}")
        
        print(f"¿Pago exitoso?: {is_success}")
        print(f"=== FIN DEBUG WEBPAY ===")
        
        if is_success:
            # Crear boleta en MongoDB
            usuario_id = get_usuario_id_unico(request)
            carrito = CarritoMongo.objects(usuario_id_unico=usuario_id)
            
            if not carrito:
                return render(request, 'pago_fallido_mongo.html', {'error': 'El carrito está vacío'})
            
            total = sum(item.subtotal() for item in carrito)
            total_decimal = Decimal(str(total))
            
            # Obtener la sucursal del primer producto del carrito
            primer_item = carrito.first()
            sucursal_id = primer_item.sucursal_id if primer_item else 1
            sucursal_nombre = primer_item.sucursal_nombre if primer_item else 'Sucursal Principal'
            
            # Crear boleta
            boleta = BoletaMongo(
                codigo=f"BOL{datetime.now().strftime('%y%m%d%H%M%S')}{random.randint(10, 99)}",
                usuario_id_unico=usuario_id,
                total=total_decimal,
                sucursal_id=sucursal_id,
                sucursal_nombre=sucursal_nombre,
                metodo_pago='webpay'
            )
            
            # Agregar información de Webpay si está disponible
            if 'buy_order' in response:
                boleta.webpay_buy_order = response['buy_order']
            if 'amount' in response:
                boleta.webpay_amount = response['amount']
            if 'authorization_code' in response:
                boleta.webpay_authorization_code = response['authorization_code']
            
            try:
                boleta.save()
                print(f"✅ Boleta creada exitosamente: {boleta.codigo}")
            except Exception as e:
                print(f"❌ Error al crear boleta: {e}")
                return render(request, 'pago_fallido_mongo.html', {
                    'error': f'Error al crear boleta: {str(e)}',
                    'response': response
                })
            
            # Crear detalles de boleta y descontar stock
            for item in carrito:
                # Crear detalle de boleta
                DetalleBoletaMongoDoc(
                    boleta_codigo=boleta.codigo,
                    producto_id=item.producto_id,
                    producto_nombre=item.producto_nombre,
                    producto_marca=item.producto_marca,
                    producto_modelo=item.producto_modelo,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    sucursal_id=item.sucursal_id,
                    sucursal_nombre=item.sucursal_nombre
                ).save()
                
                # Descontar stock del producto en la sucursal correspondiente
                actualizar_stock_producto(
                    producto_id=item.producto_id,
                    sucursal_id=item.sucursal_id,
                    cantidad=item.cantidad,
                    sucursal_nombre=item.sucursal_nombre,
                    producto_nombre=item.producto_nombre
                )
            
            # Limpiar carrito
            carrito.delete()
            
            # Obtener detalles para mostrar en el template
            detalles = DetalleBoletaMongoDoc.objects(boleta_codigo=boleta.codigo)
            
            # Obtener la sucursal para mostrar en el template
            sucursal = SucursalMongo.objects(_id=boleta.sucursal_id).first()
            
            return render(request, 'pago_exitoso_mongo.html', {
                'boleta': boleta,
                'detalles': detalles,
                'sucursal': sucursal,
                'response': response,
                'mensaje': 'Pago procesado exitosamente'
            })
        else:
            # Pago rechazado
            error_msg = f'Pago rechazado - Status: {status_upper}, Response Code: {response_code_int}'
            print(f"❌ PAGO RECHAZADO: {error_msg}")
            
            return render(request, 'pago_fallido_mongo.html', {
                'error': error_msg,
                'response': response,
                'debug_info': {
                    'status_raw': status,
                    'response_code_raw': response_code,
                    'status_normalized': status_upper,
                    'response_code_normalized': response_code_int,
                    'response_code_str': response_code_str,
                    'conditions_checked': condition_names,
                    'conditions_results': conditions
                }
            })
            
    except TransbankError as e:
        print(f"Error de Transbank al confirmar el pago: {e.message}")
        return render(request, 'pago_fallido_mongo.html', {'error': f'Error de Transbank: {e.message}'})
    except Exception as e:
        print(f"Error inesperado al confirmar el pago: {e}")
        return render(request, 'pago_fallido_mongo.html', {'error': f'Error inesperado: {str(e)}'})

def pagar_mongo(request):
    """Simular pago exitoso - MongoDB"""
    usuario_id = get_usuario_id_unico(request)
    CarritoMongo.objects(usuario_id_unico=usuario_id).delete()
    return render(request, 'carrito/pago_exitoso.html')

@require_POST
def procesar_compra_mongo(request):
    """
    Procesar compra sin pago - MongoDB
    """
    try:
        usuario_id = get_usuario_id_unico(request)
        carrito = CarritoMongo.objects(usuario_id_unico=usuario_id)
        
        if not carrito:
            return JsonResponse({
                'success': False,
                'error': 'No hay productos en el carrito'
            })
        
        # Calcular totales
        total = sum(item.subtotal() for item in carrito)
        total_decimal = Decimal(str(total))
        
        # Obtener la sucursal del primer producto del carrito
        primer_item = carrito.first()
        sucursal_id = primer_item.sucursal_id if primer_item else 1
        sucursal_nombre = primer_item.sucursal_nombre if primer_item else 'Sucursal Principal'
        
        # Crear boleta
        boleta = BoletaMongo(
            codigo=f"BOL{datetime.now().strftime('%y%m%d%H%M%S')}{random.randint(10, 99)}",
            usuario_id_unico=usuario_id,
            total=total_decimal,
            sucursal_id=sucursal_id,
            sucursal_nombre=sucursal_nombre,
            metodo_pago='efectivo'  # Cambiar a un valor válido
        )
        boleta.save()
        
        # Crear detalles de boleta y descontar stock
        for item in carrito:
            # Crear detalle de boleta
            DetalleBoletaMongoDoc(
                boleta_codigo=boleta.codigo,
                producto_id=item.producto_id,
                producto_nombre=item.producto_nombre,
                producto_marca=item.producto_marca,
                producto_modelo=item.producto_modelo,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                sucursal_id=item.sucursal_id,
                sucursal_nombre=item.sucursal_nombre
            ).save()
            
            # Descontar stock del producto en la sucursal correspondiente
            actualizar_stock_producto(
                producto_id=item.producto_id,
                sucursal_id=item.sucursal_id,
                cantidad=item.cantidad,
                sucursal_nombre=item.sucursal_nombre,
                producto_nombre=item.producto_nombre
            )
        
        # Limpiar carrito
        carrito.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Compra procesada exitosamente',
            'boleta_codigo': boleta.codigo,
            'total': float(total_decimal)
        })
        
    except Exception as e:
        print(f"Error al procesar compra: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error al procesar compra: {str(e)}'
        })

def contar_carrito_mongo(request):
    """Contar items en el carrito - MongoDB"""
    usuario_id = get_usuario_id_unico(request)
    carrito = CarritoMongo.objects(usuario_id_unico=usuario_id)
    total_items = sum(item.cantidad for item in carrito)
    
    return JsonResponse({
        'count': total_items,
        'usuario_id': usuario_id
    })

def estado_carrito_mongo(request):
    """Obtener estado completo del carrito - MongoDB"""
    try:
        usuario_id = get_usuario_id_unico(request)
        carrito = CarritoMongo.objects(usuario_id_unico=usuario_id)
        
        if not carrito:
            return JsonResponse({
                'success': True,
                'itemCount': 0,
                'totalAmount': 0,
                'items': []
            })
        
        total_items = sum(item.cantidad for item in carrito)
        total_amount = 0
        items_data = []
        
        for item in carrito:
            try:
                # Usar los campos correctos del modelo CarritoMongo
                precio_unitario = float(item.precio_unitario)
                subtotal = precio_unitario * item.cantidad
                total_amount += subtotal
                
                items_data.append({
                    'id': str(item.id),  # Usar item.id en lugar de item._id
                    'producto_id': item.producto_id,
                    'producto_nombre': item.producto_nombre,
                    'producto_marca': item.producto_marca,
                    'producto_modelo': item.producto_modelo,
                    'cantidad': item.cantidad,
                    'precio_unitario': precio_unitario,
                    'subtotal': subtotal,
                    'sucursal_id': item.sucursal_id,
                    'sucursal_nombre': item.sucursal_nombre,
                    'fecha_agregado': item.created_at.isoformat() if item.created_at else None
                })
            except Exception as e:
                logger.warning(f"Error procesando item del carrito: {e}")
                continue
        
        return JsonResponse({
            'success': True,
            'itemCount': total_items,
            'totalAmount': total_amount,
            'items': items_data
        })
        
    except Exception as e:
        logger.error(f"Error al obtener estado del carrito: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'itemCount': 0,
            'totalAmount': 0,
            'items': []
        })

def debug_webpay_mongo(request):
    """Endpoint de debug para Webpay - MongoDB"""
    token = request.GET.get('token_ws')
    
    if not token:
        return JsonResponse({'error': 'No token provided'})
    
    options = WebpayOptions(
        commerce_code="597055555532",
        api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
        integration_type=IntegrationType.TEST
    )
    
    tx = Transaction(options)
    
    try:
        response = tx.commit(token)
        
        debug_info = {
            'token': token,
            'full_response': dict(response),
            'status': response.get('status'),
            'response_code': response.get('response_code'),
            'authorization_code': response.get('authorization_code'),
            'buy_order': response.get('buy_order'),
            'amount': response.get('amount'),
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(debug_info, indent=2)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'token': token,
            'timestamp': datetime.now().isoformat()
        })

def test_webpay_response_mongo(request):
    """Endpoint para probar diferentes respuestas de Webpay - Solo para testing"""
    
    # Obtener tipo de respuesta a simular
    response_type = request.GET.get('type', 'success')
    
    # Respuestas simuladas
    simulated_responses = {
        'success': {
            'status': 'AUTHORIZED',
            'response_code': 0,
            'authorization_code': 'ABC123',
            'buy_order': 'test-order-123',
            'amount': 100000
        },
        'success_lower': {
            'status': 'authorized',
            'response_code': 0,
            'authorization_code': 'ABC123',
            'buy_order': 'test-order-123',
            'amount': 100000
        },
        'success_string': {
            'status': 'FAILED',  # Status malo pero response_code bueno
            'response_code': '0',
            'authorization_code': 'ABC123',
            'buy_order': 'test-order-123',
            'amount': 100000
        },
        'failed': {
            'status': 'FAILED',
            'response_code': -1,
            'buy_order': 'test-order-123',
            'amount': 100000
        },
        'rejected': {
            'status': 'REJECTED',
            'response_code': -6,
            'buy_order': 'test-order-123',
            'amount': 100000
        }
    }
    
    # Obtener respuesta simulada
    response = simulated_responses.get(response_type, simulated_responses['success'])
    
    # Simular el proceso de validación
    print(f"=== TEST WEBPAY RESPONSE - Tipo: {response_type} ===")
    print(f"Respuesta simulada: {response}")
    
    # Verificar múltiples condiciones para pago exitoso
    status = response.get('status', '')
    response_code = response.get('response_code', None)
    
    # Normalizar status (puede venir en mayúsculas o minúsculas)
    status_upper = str(status).upper() if status else ''
    status_lower = str(status).lower() if status else ''
    
    # Normalizar response_code (puede venir como string o int)
    try:
        response_code_int = int(response_code) if response_code is not None else -1
    except (ValueError, TypeError):
        response_code_int = -1
    
    # También verificar como string por si viene como '0'
    response_code_str = str(response_code) if response_code is not None else ''
    
    print(f"Status original: '{status}' (tipo: {type(status)})")
    print(f"Status normalizado: '{status_upper}'")
    print(f"Response Code original: '{response_code}' (tipo: {type(response_code)})")
    print(f"Response Code normalizado: {response_code_int}")
    print(f"Response Code como string: '{response_code_str}'")
    
    # Condiciones para pago exitoso - ser muy permisivo con diferentes formatos
    conditions = [
        status_upper == 'AUTHORIZED',
        status_lower == 'authorized',
        status_upper == 'APPROVED',
        status_lower == 'approved',
        status_upper == 'SUCCESS',
        status_lower == 'success',
        response_code_int == 0,
        response_code_str == '0',
        response_code_str.upper() == 'SUCCESS',
        response_code_str.upper() == 'APPROVED'
    ]
    
    is_success = any(conditions)
    
    condition_names = [
        'status_upper == AUTHORIZED',
        'status_lower == authorized',
        'status_upper == APPROVED',
        'status_lower == approved',
        'status_upper == SUCCESS',
        'status_lower == success',
        'response_code_int == 0',
        'response_code_str == "0"',
        'response_code_str.upper() == SUCCESS',
        'response_code_str.upper() == APPROVED'
    ]
    
    print(f"Condiciones evaluadas:")
    for i, condition in enumerate(conditions):
        print(f"  {condition_names[i]}: {condition}")
    
    print(f"¿Pago exitoso?: {is_success}")
    print(f"=== FIN TEST WEBPAY ===")
    
    if is_success:
        # Buscar boleta real más reciente para mostrar datos reales
        usuario_id = get_usuario_id_unico(request)
        boleta_real = BoletaMongo.objects(usuario_id_unico=usuario_id).order_by('-fecha').first()
        detalles_reales = []
        
        if boleta_real:
            detalles_reales = DetalleBoletaMongoDoc.objects(boleta_codigo=boleta_real.codigo)
            # Obtener la sucursal para mostrar en el template
            sucursal = SucursalMongo.objects(_id=boleta_real.sucursal_id).first()
        else:
            sucursal = None
        
        return render(request, 'pago_exitoso_mongo.html', {
            'response': response,
            'mensaje': f'Pago simulado exitoso (tipo: {response_type})',
            'test_mode': True,
            'boleta': boleta_real,
            'detalles': detalles_reales,
            'sucursal': sucursal
        })
    else:
        return render(request, 'pago_fallido_mongo.html', {
            'error': f'Pago simulado fallido (tipo: {response_type})',
            'response': response,
            'debug_info': {
                'status_raw': status,
                'response_code_raw': response_code,
                'status_normalized': status_upper,
                'response_code_normalized': response_code_int,
                'response_code_str': response_code_str,
                'conditions_checked': condition_names,
                'conditions_results': conditions,
                'test_mode': True
            }
        })

def descargar_boleta_pdf_mongo(request, codigo_boleta):
    """Descargar boleta en PDF desde MongoDB"""
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.colors import HexColor
    from io import BytesIO
    
    try:
        # Buscar boleta en MongoDB
        boleta = BoletaMongo.objects.get(codigo=codigo_boleta)
        
        # Crear buffer para PDF
        buffer = BytesIO()
        
        # Crear PDF
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Colores
        color_primary = HexColor('#2c3e50')
        color_secondary = HexColor('#3498db')
        color_text = HexColor('#2c3e50')
        
        # Header
        p.setFillColor(color_primary)
        p.rect(0, height - 100, width, 100, fill=True)
        
        # Logo/Título
        p.setFillColor(HexColor('#ffffff'))
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, height - 60, "FERREMAS")
        
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, "Ferretería Industrial")
        
        # Información de la boleta
        p.setFillColor(color_text)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 140, f"BOLETA N° {boleta.codigo}")
        
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 160, f"Fecha: {boleta.fecha.strftime('%d/%m/%Y %H:%M')}")
        p.drawString(50, height - 175, f"Sucursal: {boleta.sucursal_nombre}")
        p.drawString(50, height - 190, f"Usuario: {boleta.usuario_id_unico}")
        
        # Información de pago
        if boleta.webpay_authorization_code:
            p.drawString(300, height - 160, f"Método de Pago: Webpay")
            p.drawString(300, height - 175, f"Autorización: {boleta.webpay_authorization_code}")
            p.drawString(300, height - 190, f"Orden: {boleta.webpay_buy_order}")
        else:
            p.drawString(300, height - 160, f"Método de Pago: {boleta.metodo_pago}")
        
        # Línea separadora
        p.setStrokeColor(color_secondary)
        p.setLineWidth(2)
        p.line(50, height - 210, width - 50, height - 210)
        
        # Cabecera de tabla
        y_position = height - 240
        p.setFillColor(color_secondary)
        p.rect(50, y_position - 20, width - 100, 20, fill=True)
        
        p.setFillColor(HexColor('#ffffff'))
        p.setFont("Helvetica-Bold", 10)
        p.drawString(55, y_position - 15, "Producto")
        p.drawString(250, y_position - 15, "Cantidad")
        p.drawString(320, y_position - 15, "Precio Unit.")
        p.drawString(420, y_position - 15, "Subtotal")
        
        # Buscar detalles de boleta como documentos independientes
        detalles = DetalleBoletaMongoDoc.objects(boleta_codigo=codigo_boleta)
        
        y_position -= 30
        p.setFillColor(color_text)
        p.setFont("Helvetica", 9)
        
        total_items = 0
        subtotal_general = 0
        
        for detalle in detalles:
            if y_position < 100:  # Nueva página si es necesario
                p.showPage()
                y_position = height - 100
            
            # Información del producto
            producto_info = f"{detalle.producto_marca} {detalle.producto_modelo}"
            if len(producto_info) > 30:
                producto_info = producto_info[:30] + "..."
            
            p.drawString(55, y_position, producto_info)
            p.drawString(55, y_position - 12, detalle.producto_nombre[:40])
            
            p.drawString(260, y_position, str(detalle.cantidad))
            p.drawString(320, y_position, f"${detalle.precio_unitario:,.0f}")
            p.drawString(420, y_position, f"${detalle.subtotal():,.0f}")
            
            total_items += detalle.cantidad
            subtotal_general += detalle.subtotal()
            
            y_position -= 30
        
        # Totales
        y_position -= 20
        p.setStrokeColor(color_secondary)
        p.line(300, y_position, width - 50, y_position)
        
        y_position -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(300, y_position, f"Total Items: {total_items}")
        
        y_position -= 15
        p.setFont("Helvetica-Bold", 12)
        p.drawString(300, y_position, f"TOTAL: ${float(boleta.total):,.0f}")
        
        # Footer
        p.setFont("Helvetica", 8)
        p.drawString(50, 50, "Gracias por su compra - Ferremas")
        p.drawString(50, 40, f"Boleta generada el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        p.showPage()
        p.save()
        
        # Preparar respuesta
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="boleta_{codigo_boleta}.pdf"'
        
        return response
        
    except BoletaMongo.DoesNotExist:
        return HttpResponse("Boleta no encontrada", status=404)
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return HttpResponse(f"Error al generar PDF: {str(e)}", status=500)

def actualizar_stock_producto(producto_id, sucursal_id, cantidad, sucursal_nombre, producto_nombre):
    """
    Función auxiliar para actualizar el stock de un producto en una sucursal específica
    """
    try:
        from ferremas.mongo_models import ProductoMongo
        producto = ProductoMongo.objects(_id=producto_id).first()
        
        if not producto:
            print(f"❌ No se encontró el producto {producto_id} para actualizar stock")
            return False
        
        # Buscar el inventario de la sucursal específica
        for inv in producto.inventario:
            if inv.sucursal == sucursal_id:
                # Verificar que hay stock suficiente
                if inv.cantidad >= cantidad:
                    stock_anterior = inv.cantidad
                    inv.cantidad -= cantidad
                    inv.ultima_actualizacion = datetime.now()
                    print(f"✅ Stock actualizado para {producto_nombre} en {sucursal_nombre}: {stock_anterior} -> {inv.cantidad} (-{cantidad} unidades)")
                    
                    # Actualizar fecha de modificación del producto
                    producto.updated_at = datetime.now()
                    producto.save()
                    return True
                else:
                    print(f"⚠️ Stock insuficiente para {producto_nombre} en {sucursal_nombre}: disponible {inv.cantidad}, requerido {cantidad}")
                    return False
        
        print(f"❌ No se encontró inventario para {producto_nombre} en sucursal {sucursal_id}")
        return False
        
    except Exception as e:
        print(f"❌ Error al actualizar stock para {producto_nombre}: {e}")
        return False
