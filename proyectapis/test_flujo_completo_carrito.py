#!/usr/bin/env python
"""
Script completo de prueba del carrito - Simulación real de navegador
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
from http.cookies import SimpleCookie

def test_flujo_completo_carrito():
    """Prueba completa del flujo del carrito"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("🛒 PRUEBA COMPLETA DEL CARRITO - FERREMAS")
    print("="*60)
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    # Paso 1: Agregar producto al carrito
    print("\n1️⃣ AGREGANDO PRODUCTO AL CARRITO")
    print("-" * 40)
    
    add_response = session.post(
        f"{base_url}/carrito/agregar/",
        data={
            'producto_id': 'TALADRO-001',
            'cantidad': 2,
            'sucursal_id': 1
        }
    )
    
    print(f"Status Code: {add_response.status_code}")
    
    if add_response.status_code == 200:
        add_data = add_response.json()
        print(f"✅ Producto agregado exitosamente")
        print(f"   Usuario ID: {add_data.get('usuario_id')}")
        print(f"   Mensaje: {add_data.get('message')}")
        print(f"   Cantidad: {add_data.get('cantidad')}")
        print(f"   Subtotal: ${add_data.get('subtotal'):,.2f}")
        
        # Mostrar cookies establecidas
        print(f"   Cookies establecidas: {list(session.cookies.keys())}")
        
        # Paso 2: Ver carrito
        print("\n2️⃣ VIENDO CARRITO")
        print("-" * 40)
        
        cart_response = session.get(f"{base_url}/carrito/")
        
        if cart_response.status_code == 200:
            print("✅ Carrito cargado exitosamente")
            
            # Verificar contenido del carrito
            cart_content = cart_response.text
            
            # Buscar información de debug
            if 'DEBUG:' in cart_content:
                print("✅ Información de debug encontrada")
            
            # Verificar si hay items
            if 'Items: 0' in cart_content:
                print("❌ EL CARRITO APARECE VACÍO")
            else:
                print("✅ El carrito tiene items")
                
            # Extraer información de debug
            if 'DEBUG:' in cart_content:
                debug_start = cart_content.find('DEBUG:')
                debug_end = cart_content.find('</div>', debug_start)
                debug_section = cart_content[debug_start:debug_end]
                print(f"   Debug info: {debug_section}")
            
        else:
            print(f"❌ Error al cargar carrito: {cart_response.status_code}")
        
        # Paso 3: Agregar otro producto
        print("\n3️⃣ AGREGANDO SEGUNDO PRODUCTO")
        print("-" * 40)
        
        add_response2 = session.post(
            f"{base_url}/carrito/agregar/",
            data={
                'producto_id': 'SIERRA-001',
                'cantidad': 1,
                'sucursal_id': 1
            }
        )
        
        if add_response2.status_code == 200:
            add_data2 = add_response2.json()
            print(f"✅ Segundo producto agregado")
            print(f"   Mensaje: {add_data2.get('message')}")
        else:
            print(f"❌ Error agregando segundo producto: {add_response2.status_code}")
            print(f"   Respuesta: {add_response2.text}")
        
        # Paso 4: Ver carrito actualizado
        print("\n4️⃣ VIENDO CARRITO ACTUALIZADO")
        print("-" * 40)
        
        cart_response2 = session.get(f"{base_url}/carrito/")
        
        if cart_response2.status_code == 200:
            print("✅ Carrito actualizado cargado")
            
            cart_content2 = cart_response2.text
            
            if 'Items: 0' in cart_content2:
                print("❌ EL CARRITO SIGUE VACÍO")
            elif 'Items: 1' in cart_content2:
                print("⚠️  Solo un item en carrito")
            elif 'Items: 2' in cart_content2:
                print("✅ Ambos items en carrito")
            else:
                print("❓ Estado del carrito no claro")
        
        # Paso 5: Test con nueva sesión (simular nueva pestaña)
        print("\n5️⃣ SIMULANDO NUEVA PESTAÑA (SIN COOKIES)")
        print("-" * 40)
        
        new_session = requests.Session()
        cart_response3 = new_session.get(f"{base_url}/carrito/")
        
        if cart_response3.status_code == 200:
            cart_content3 = cart_response3.text
            
            if 'Items: 0' in cart_content3:
                print("✅ Nueva sesión tiene carrito vacío (esperado)")
            else:
                print("❓ Nueva sesión tiene items (inesperado)")
        
        print("\n" + "="*60)
        print("🏁 PRUEBA COMPLETADA")
        print("="*60)
        
    else:
        print(f"❌ Error al agregar producto: {add_response.status_code}")
        print(f"   Respuesta: {add_response.text}")

if __name__ == "__main__":
    print("Asegúrate de que el servidor esté corriendo en http://127.0.0.1:8000")
    input("Presiona Enter para continuar...")
    test_flujo_completo_carrito()
