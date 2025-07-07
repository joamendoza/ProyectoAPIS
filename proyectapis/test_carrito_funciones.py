#!/usr/bin/env python3
"""
Script para probar las funciones de actualización de cantidad en el carrito
"""

import requests
import json
import sys
from pathlib import Path

SERVER_URL = "http://127.0.0.1:8000"

def get_csrf_token():
    """Obtener token CSRF del servidor"""
    try:
        response = requests.get(f"{SERVER_URL}/carrito/")
        if response.status_code == 200:
            # Extraer token CSRF de las cookies
            csrf_token = None
            for cookie in response.cookies:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
            return csrf_token
        return None
    except:
        return None

def test_add_product_to_cart():
    """Agregar un producto al carrito para probar"""
    print("🛒 === AGREGANDO PRODUCTO AL CARRITO ===")
    
    # Primero obtener productos disponibles
    try:
        products_response = requests.get(f"{SERVER_URL}/api/productos/venta/", timeout=5)
        if products_response.status_code == 200:
            products = products_response.json()
            if products:
                product_id = products[0]['_id']
                print(f"✅ Producto a agregar: {products[0]['nombre']} (ID: {product_id})")
                
                # Agregar producto al carrito
                csrf_token = get_csrf_token()
                if not csrf_token:
                    print("❌ No se pudo obtener el token CSRF")
                    return None
                
                add_response = requests.post(
                    f"{SERVER_URL}/carrito/agregar/{product_id}/",
                    json={"sucursal_id": None},
                    headers={
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf_token
                    },
                    cookies={'csrftoken': csrf_token}
                )
                
                if add_response.status_code == 200:
                    result = add_response.json()
                    if result.get('success'):
                        print("✅ Producto agregado al carrito")
                        return product_id
                    else:
                        print(f"❌ Error al agregar producto: {result.get('error', 'Error desconocido')}")
                else:
                    print(f"❌ Error HTTP al agregar producto: {add_response.status_code}")
                    try:
                        error_data = add_response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Error: {add_response.text}")
            else:
                print("❌ No hay productos disponibles")
        else:
            print(f"❌ Error al obtener productos: {products_response.status_code}")
    except Exception as e:
        print(f"❌ Error al agregar producto: {e}")
    
    return None

def test_get_cart_items():
    """Obtener elementos del carrito"""
    print("\n📋 === OBTENIENDO ELEMENTOS DEL CARRITO ===")
    
    try:
        response = requests.get(f"{SERVER_URL}/carrito/", timeout=5)
        if response.status_code == 200:
            # Buscar elementos del carrito en el HTML
            html_content = response.text
            
            # Buscar data-item-id en el HTML
            import re
            item_ids = re.findall(r'data-item-id="([^"]+)"', html_content)
            
            if item_ids:
                print(f"✅ Elementos en el carrito: {len(item_ids)}")
                for i, item_id in enumerate(item_ids):
                    print(f"   Item {i+1}: {item_id}")
                return item_ids
            else:
                print("⚠️ No se encontraron elementos en el carrito")
                return []
        else:
            print(f"❌ Error al obtener carrito: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error al obtener carrito: {e}")
        return []

def test_update_quantity(item_id, new_quantity):
    """Probar actualización de cantidad"""
    print(f"\n🔄 === ACTUALIZANDO CANTIDAD (Item: {item_id}, Cantidad: {new_quantity}) ===")
    
    try:
        csrf_token = get_csrf_token()
        if not csrf_token:
            print("❌ No se pudo obtener el token CSRF")
            return False
        
        response = requests.post(
            f"{SERVER_URL}/carrito/actualizar/{item_id}/",
            json={"cantidad": new_quantity},
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            cookies={'csrftoken': csrf_token},
            timeout=5
        )
        
        print(f"📥 Respuesta del servidor: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Cantidad actualizada exitosamente")
                print(f"   Nueva cantidad: {result.get('nueva_cantidad')}")
                print(f"   Nuevo subtotal: {result.get('nuevo_subtotal')}")
                return True
            else:
                print(f"❌ Error en la actualización: {result.get('error', 'Error desconocido')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
        
        return False
    except Exception as e:
        print(f"❌ Error en la actualización: {e}")
        return False

def test_remove_item(item_id):
    """Probar eliminación de elemento"""
    print(f"\n🗑️ === ELIMINANDO ELEMENTO (Item: {item_id}) ===")
    
    try:
        csrf_token = get_csrf_token()
        if not csrf_token:
            print("❌ No se pudo obtener el token CSRF")
            return False
        
        response = requests.post(
            f"{SERVER_URL}/carrito/eliminar/{item_id}/",
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            cookies={'csrftoken': csrf_token},
            timeout=5
        )
        
        print(f"📥 Respuesta del servidor: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Elemento eliminado exitosamente")
                return True
            else:
                print(f"❌ Error en la eliminación: {result.get('error', 'Error desconocido')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
        
        return False
    except Exception as e:
        print(f"❌ Error en la eliminación: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 === PRUEBA DE FUNCIONES DEL CARRITO ===")
    
    # Paso 1: Agregar producto al carrito
    product_id = test_add_product_to_cart()
    if not product_id:
        print("❌ No se pudo agregar producto al carrito. Terminando prueba.")
        return False
    
    # Paso 2: Obtener elementos del carrito
    cart_items = test_get_cart_items()
    if not cart_items:
        print("❌ No se encontraron elementos en el carrito. Terminando prueba.")
        return False
    
    # Paso 3: Probar actualización de cantidad
    first_item = cart_items[0]
    
    # Aumentar cantidad
    if not test_update_quantity(first_item, 3):
        print("❌ Falló la actualización de cantidad")
        return False
    
    # Disminuir cantidad
    if not test_update_quantity(first_item, 1):
        print("❌ Falló la disminución de cantidad")
        return False
    
    # Paso 4: Probar eliminación
    if not test_remove_item(first_item):
        print("❌ Falló la eliminación del elemento")
        return False
    
    print("\n🎉 === TODAS LAS PRUEBAS PASARON ===")
    print("✅ Las funciones de actualización y eliminación funcionan correctamente")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
