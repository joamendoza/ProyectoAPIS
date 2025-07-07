#!/usr/bin/env python3
"""
Script para probar las URLs del carrito directamente
"""

import requests
import json
import sys
from pathlib import Path

SERVER_URL = "http://127.0.0.1:8000"

def test_carrito_urls():
    """Probar las URLs del carrito"""
    print("🔍 === PROBANDO URLS DEL CARRITO ===")
    
    # Obtener página del carrito
    try:
        response = requests.get(f"{SERVER_URL}/carrito/", timeout=10)
        print(f"GET /carrito/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Página del carrito carga correctamente")
            
            # Buscar elementos del carrito en el HTML
            html_content = response.text
            
            # Buscar si hay items en el carrito
            import re
            item_ids = re.findall(r'data-item-id="([^"]+)"', html_content)
            
            if item_ids:
                print(f"📋 Items encontrados en el carrito: {len(item_ids)}")
                
                # Probar URL de actualización
                first_item = item_ids[0]
                print(f"🔧 Probando actualización para item: {first_item}")
                
                # Obtener CSRF token
                csrf_match = re.search(r"window\.csrfToken = '([^']+)'", html_content)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"🔑 CSRF Token encontrado: {csrf_token[:20]}...")
                    
                    # Probar actualización
                    update_response = requests.post(
                        f"{SERVER_URL}/carrito/actualizar/{first_item}/",
                        json={"cantidad": 2},
                        headers={
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrf_token,
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        timeout=10
                    )
                    
                    print(f"POST /carrito/actualizar/{first_item}/ - Status: {update_response.status_code}")
                    
                    if update_response.status_code == 200:
                        try:
                            result = update_response.json()
                            if result.get('success'):
                                print("✅ Actualización exitosa")
                                print(f"   Nueva cantidad: {result.get('nueva_cantidad')}")
                            else:
                                print(f"❌ Error en actualización: {result.get('error')}")
                        except:
                            print("❌ Respuesta no es JSON válido")
                    else:
                        print(f"❌ Error HTTP: {update_response.status_code}")
                        print(f"   Respuesta: {update_response.text[:200]}...")
                
                else:
                    print("❌ No se encontró CSRF token en el HTML")
                
            else:
                print("⚠️ No se encontraron items en el carrito")
                print("💡 Necesitas agregar productos al carrito primero")
                
        else:
            print(f"❌ Error al cargar carrito: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error al probar carrito: {e}")

def test_add_product_to_cart():
    """Agregar un producto al carrito"""
    print("\n🛒 === AGREGANDO PRODUCTO AL CARRITO ===")
    
    try:
        # Obtener productos disponibles
        products_response = requests.get(f"{SERVER_URL}/api/productos/venta/", timeout=10)
        if products_response.status_code == 200:
            products = products_response.json()
            if products:
                product_id = products[0]['_id']
                product_name = products[0]['nombre']
                print(f"📦 Producto a agregar: {product_name}")
                
                # Obtener CSRF token desde la página del carrito
                carrito_response = requests.get(f"{SERVER_URL}/carrito/", timeout=10)
                if carrito_response.status_code == 200:
                    html_content = carrito_response.text
                    import re
                    csrf_match = re.search(r"window\.csrfToken = '([^']+)'", html_content)
                    
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        print(f"🔑 CSRF Token: {csrf_token[:20]}...")
                        
                        # Agregar producto
                        add_response = requests.post(
                            f"{SERVER_URL}/carrito/agregar/{product_id}/",
                            json={"sucursal_id": None},
                            headers={
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrf_token,
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            timeout=10
                        )
                        
                        print(f"POST /carrito/agregar/{product_id}/ - Status: {add_response.status_code}")
                        
                        if add_response.status_code == 200:
                            try:
                                result = add_response.json()
                                if result.get('success'):
                                    print("✅ Producto agregado exitosamente")
                                    return True
                                else:
                                    print(f"❌ Error al agregar: {result.get('error')}")
                            except:
                                print("❌ Respuesta no es JSON válido")
                        else:
                            print(f"❌ Error HTTP: {add_response.status_code}")
                            print(f"   Respuesta: {add_response.text[:200]}...")
                    else:
                        print("❌ No se encontró CSRF token")
                else:
                    print(f"❌ Error al obtener página del carrito: {carrito_response.status_code}")
            else:
                print("❌ No hay productos disponibles")
        else:
            print(f"❌ Error al obtener productos: {products_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error al agregar producto: {e}")
    
    return False

def main():
    """Función principal"""
    print("🧪 === DIAGNÓSTICO DE URLS DEL CARRITO ===")
    
    # Primero agregar un producto
    if test_add_product_to_cart():
        print("\n" + "="*50)
        # Luego probar las URLs
        test_carrito_urls()
    else:
        print("\n⚠️ No se pudo agregar producto, probando URLs existentes...")
        test_carrito_urls()

if __name__ == "__main__":
    main()
