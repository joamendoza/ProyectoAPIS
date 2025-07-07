#!/usr/bin/env python
"""
Test simple de carrito
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

def test_carrito_simple():
    """Test básico del carrito"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    print("🧪 Test simple del carrito")
    print("-" * 40)
    
    # Verificar productos disponibles
    print("1. Verificando productos...")
    productos_response = session.get(f"{base_url}/api/productos/")
    if productos_response.status_code == 200:
        productos = productos_response.json()
        print(f"✅ Productos disponibles: {len(productos)}")
        if productos:
            print(f"   Primer producto: {productos[0]}")
    else:
        print(f"❌ Error obteniendo productos: {productos_response.status_code}")
    
    # Agregar un producto al carrito
    print("\n2. Agregando producto al carrito...")
    add_response = session.post(
        f"{base_url}/carrito/agregar/",
        data={
            'producto_id': 'TALADRO-001',
            'cantidad': 1,
            'sucursal_id': 1
        }
    )
    
    print(f"   Status: {add_response.status_code}")
    if add_response.status_code == 200:
        try:
            data = add_response.json()
            print(f"   Respuesta: {data}")
        except:
            print(f"   Respuesta (text): {add_response.text[:200]}...")
    
    # Ver carrito
    print("\n3. Visualizando carrito...")
    cart_response = session.get(f"{base_url}/carrito/")
    print(f"   Status: {cart_response.status_code}")
    
    if cart_response.status_code == 200:
        content = cart_response.text
        # Buscar información de debug
        if 'Items: 0' in content:
            print("   ❌ Carrito vacío")
        else:
            print("   ✅ Carrito con productos")
            
        # Extraer cookies
        cookies = session.cookies.get_dict()
        print(f"   Cookies: {cookies}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    test_carrito_simple()
