import bcchapi
import pandas as pd
import json
import os
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from inventario.models import Producto
from .models import Carrito

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
        carrito_item.cantidad += 1
    carrito_item.save()
    return redirect('ver_carrito')

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
