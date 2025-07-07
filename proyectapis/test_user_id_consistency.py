#!/usr/bin/env python
"""
Test user ID consistency
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

def test_user_id_consistency():
    """Test user ID consistency"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    print("🔍 Test consistencia de usuario ID")
    print("-" * 50)
    
    # Paso 1: Agregar producto
    print("1. Agregando producto...")
    add_response = session.post(
        f"{base_url}/carrito/agregar/",
        data={
            'producto_id': 'TALADRO-001',
            'cantidad': 1,
            'sucursal_id': 1
        }
    )
    
    if add_response.status_code == 200:
        add_data = add_response.json()
        print(f"   ✅ Producto agregado")
        print(f"   Usuario ID: {add_data.get('usuario_id')}")
        print(f"   Cookies después de agregar: {session.cookies.get_dict()}")
    
    # Paso 2: Ver carrito
    print("\n2. Viendo carrito...")
    cart_response = session.get(f"{base_url}/carrito/")
    
    if cart_response.status_code == 200:
        print(f"   ✅ Carrito obtenido")
        print(f"   Cookies durante visualización: {session.cookies.get_dict()}")
        
        # Extraer info de debug
        content = cart_response.text
        if 'DEBUG:' in content:
            start = content.find('DEBUG:')
            end = content.find('</div>', start)
            if end > start:
                debug_info = content[start:end]
                print(f"   Debug info: {debug_info}")
    
    # Paso 3: Agregar otro producto
    print("\n3. Agregando otro producto...")
    add_response2 = session.post(
        f"{base_url}/carrito/agregar/",
        data={
            'producto_id': 'SIERRA-002',
            'cantidad': 1,
            'sucursal_id': 1
        }
    )
    
    if add_response2.status_code == 200:
        add_data2 = add_response2.json()
        print(f"   ✅ Segundo producto agregado")
        print(f"   Usuario ID: {add_data2.get('usuario_id')}")
        print(f"   Cookies después de agregar: {session.cookies.get_dict()}")
    
    # Paso 4: Ver carrito nuevamente
    print("\n4. Viendo carrito nuevamente...")
    cart_response2 = session.get(f"{base_url}/carrito/")
    
    if cart_response2.status_code == 200:
        print(f"   ✅ Carrito obtenido")
        
        # Extraer info de debug
        content2 = cart_response2.text
        if 'DEBUG:' in content2:
            start = content2.find('DEBUG:')
            end = content2.find('</div>', start)
            if end > start:
                debug_info2 = content2[start:end]
                print(f"   Debug info: {debug_info2}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_user_id_consistency()
