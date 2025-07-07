#!/usr/bin/env python
"""
Script para probar la nueva implementación del carrito con cookies
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

import requests
import json

def test_carrito_con_cookies():
    """Prueba el carrito usando cookies para mantener sesión"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    print("=== PRUEBA CARRITO CON COOKIES ===")
    
    # 1. Agregar producto al carrito
    print("\n1. AGREGANDO PRODUCTO AL CARRITO")
    
    add_response = session.post(
        f"{base_url}/carrito/agregar/",
        data={
            'producto_id': 'TALADRO-001',
            'cantidad': 2,
            'sucursal_id': 1
        }
    )
    
    print(f"Status Code: {add_response.status_code}")
    print(f"Response: {add_response.text}")
    
    if add_response.status_code == 200:
        add_data = add_response.json()
        print(f"Usuario ID: {add_data.get('usuario_id')}")
        print(f"Producto agregado: {add_data.get('message')}")
        
        # 2. Ver carrito (usando la misma sesión)
        print("\n2. VIENDO CARRITO (MISMA SESIÓN)")
        
        cart_response = session.get(f"{base_url}/carrito/")
        print(f"Status Code: {cart_response.status_code}")
        
        if cart_response.status_code == 200:
            print("✅ Carrito cargado correctamente")
            # Buscar información de debug en el HTML
            if 'debug_info' in cart_response.text:
                print("✅ Información de debug encontrada en HTML")
            if 'total_items' in cart_response.text:
                print("✅ Items encontrados en carrito")
        else:
            print("❌ Error al cargar carrito")
    else:
        print("❌ Error al agregar producto")
        print(f"Response: {add_response.text}")

def test_carrito_sin_cookies():
    """Prueba el carrito sin mantener cookies (para comparar)"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("\n\n=== PRUEBA CARRITO SIN COOKIES (COMPARACIÓN) ===")
    
    # 1. Agregar producto al carrito
    print("\n1. AGREGANDO PRODUCTO AL CARRITO")
    
    add_response = requests.post(
        f"{base_url}/carrito/agregar/",
        data={
            'producto_id': 'TALADRO-001',
            'cantidad': 1,
            'sucursal_id': 1
        }
    )
    
    print(f"Status Code: {add_response.status_code}")
    if add_response.status_code == 200:
        add_data = add_response.json()
        print(f"Usuario ID (agregar): {add_data.get('usuario_id')}")
        
        # 2. Ver carrito (request separado, sin cookies)
        print("\n2. VIENDO CARRITO (REQUEST SEPARADO)")
        
        cart_response = requests.get(f"{base_url}/carrito/")
        print(f"Status Code: {cart_response.status_code}")
        
        if cart_response.status_code == 200:
            print("✅ Carrito cargado, pero probablemente vacío")
        else:
            print("❌ Error al cargar carrito")
    else:
        print("❌ Error al agregar producto")

if __name__ == "__main__":
    print("Asegúrate de que el servidor esté corriendo en http://127.0.0.1:8000")
    print("Ejecuta: python manage.py runserver")
    input("Presiona Enter para continuar...")
    
    # Probar con cookies
    test_carrito_con_cookies()
    
    # Probar sin cookies
    test_carrito_sin_cookies()
