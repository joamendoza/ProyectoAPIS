import random
import bcchapi
import pandas as pd
import json
import os
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from inventario.models import Producto
from .models import Carrito, Boleta, DetalleBoleta
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
import uuid
from reportlab.pdfgen import canvas
from django.http import HttpResponse

##COMO TE ODIO TRANSBANK##
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType
from transbank.error.transbank_error import TransbankError

CACHE_FILE = "moneda_cache.json"

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

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'carrito/lista_productos.html', {'productos': productos})

def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito_item, created = Carrito.objects.get_or_create(producto=producto)
    if not created:
        if carrito_item.cantidad < producto.stock:
            carrito_item.cantidad += 1
            carrito_item.save()
            messages.success(request, f"¡{producto.nombre} añadido al carrito!")
        else:
            messages.error(request, f"No puedes añadir más de {producto.stock} unidades de {producto.nombre}.")
    else:
        if producto.stock > 0:
            carrito_item.cantidad = 1
            carrito_item.save()
            messages.success(request, f"¡{producto.nombre} añadido al carrito!")
        else:
            carrito_item.delete()
            messages.error(request, f"{producto.nombre} no tiene stock disponible.")
    return redirect('lista_productos')

def ver_carrito(request):
    carrito = Carrito.objects.all()
    total = sum(item.subtotal() for item in carrito)

    valor_dolar = valor_euro = total_usd = total_eur = error_dolar = error_euro = None

    if request.GET.get("convertir") == "dolar":
        valor_dolar, error_dolar = obtener_moneda("F073.TCO.PRE.Z.D")
        if valor_dolar and total:
            total_usd = float(total) / float(valor_dolar)
    elif request.GET.get("convertir") == "euro":
        valor_euro, error_euro = obtener_moneda("F072.CLP.EUR.N.O.D")
        if valor_euro and total:
            total_eur = float(total) / float(valor_euro)

    return render(request, "carrito/ver_carrito.html", {
        "carrito": carrito,
        "total": total,
        "valor_dolar": valor_dolar,
        "total_usd": total_usd,
        "error_dolar": error_dolar,
        "valor_euro": valor_euro,
        "total_eur": total_eur,
        "error_euro": error_euro,
    })

def pagar(request):
    Carrito.objects.all().delete()
    return render(request, 'carrito/pago_exitoso.html')

def iniciar_pago_webpay(request):
    carrito = Carrito.objects.all()
    amount = sum(item.subtotal() for item in carrito)
    if amount <= 0:
        return render(request, 'carrito/pago_fallido.html', {'error': 'El carrito está vacío o el monto es inválido.'})

    buy_order = f"orden-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    session_id = "test-session"
    return_url = request.build_absolute_uri(reverse('webpay_respuesta'))
    options = WebpayOptions(
        commerce_code="597055555532",  #Cambiar por API key
        api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C", #Cambiar por API key real(secret key)
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
        print(f"Error de Transbank al iniciar el pago: {e.message}")
        import traceback
        traceback.print_exc()
        return render(request, 'pago_fallido.html', {'error': str(e.message)})
    except Exception as e:
        print(f"Error inesperado al iniciar el pago: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'pago_fallido.html', {'error': str(e)})
    
def generar_usuario_invitado_unico():
    from .models import Boleta
    while True:
        invitado_id = f"invitado{random.randint(100000, 999999)}"
        if not Boleta.objects.filter(usuario_id_unico=invitado_id).exists():
            return invitado_id

def webpay_respuesta(request):
    token = request.GET.get('token_ws')
    if not token:
        return render(request, 'carrito/pago_fallido.html', {'error': 'No se recibió el token de Transbank.'})
    options = WebpayOptions(
        commerce_code="597055555532",
        api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
        integration_type=IntegrationType.TEST
    )
    tx = Transaction(options)
    try:
        response = tx.commit(token)
        if response and response.get('response_code') == 0:
            carrito = Carrito.objects.all()
            total = sum(item.subtotal() for item in carrito)
            if request.user.is_authenticated:
                usuario_id_unico = f"user-{request.user.id}"
            else:
                usuario_id_unico = generar_usuario_invitado_unico()
            codigo_boleta = str(uuid.uuid4())[:8]
            boleta = Boleta.objects.create(
                codigo=codigo_boleta,
                usuario_id_unico=usuario_id_unico,
                total=total
            )
            for item in carrito:
                DetalleBoleta.objects.create(
                    boleta=boleta,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio=item.producto.precio
                )
                producto = item.producto
                producto.stock = max(producto.stock - item.cantidad, 0)
                producto.save()
            carrito.delete()
            return render(request, 'carrito/pago_exitoso.html', {'response': response, 'boleta': boleta})
        else:
            error_message = response.get('response_code_description', 'Pago rechazado o fallido.') if response else 'Respuesta vacía de Transbank.'
            return render(request, 'carrito/pago_fallido.html', {'error': error_message, 'response': response})

    except TransbankError as e:
        print(f"Error Transbank al procesar la respuesta: {e.message}")
        import traceback
        traceback.print_exc()
        return render(request, 'carrito/pago_fallido.html', {'error': f"Error Transbank: {e.message}"})
    except Exception as e:
        print(f"Error inesperado al procesar la respuesta de Transbank: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'carrito/pago_fallido.html', {'error': str(e)})

@require_POST
def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(Carrito, id=item_id)
    cantidad = int(request.POST.get('cantidad', 1))
    if item.cantidad > cantidad:
        item.cantidad -= cantidad
        item.save()
    else:
        item.delete()
    return redirect('ver_carrito')

def descargar_boleta_pdf(request, codigo_boleta):
    boleta = get_object_or_404(Boleta, codigo=codigo_boleta)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="boleta_{boleta.codigo}.pdf"'
    p = canvas.Canvas(response)
    y = 800

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, y, f"Boleta N° {boleta.codigo}")
    y -= 30
    p.setFont("Helvetica", 12)
    p.drawString(100, y, f"Usuario: {boleta.usuario_id_unico}")
    y -= 20
    p.drawString(100, y, f"Fecha: {boleta.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 20
    p.drawString(100, y, f"Total: ${boleta.total}")
    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Productos:")
    y -= 20
    p.setFont("Helvetica", 12)
    for detalle in boleta.detalles.all():
        p.drawString(110, y, f"{detalle.producto.nombre} | Cantidad: {detalle.cantidad} | Precio unitario: ${detalle.precio}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.showPage()
    p.save()
    return response
