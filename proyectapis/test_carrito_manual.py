#!/usr/bin/env python3
"""
Script para probar manualmente las funciones del carrito con debugging
"""

import requests
import json
from pathlib import Path

SERVER_URL = "http://127.0.0.1:8000"

def test_carrito_endpoints():
    """Probar endpoints del carrito"""
    print("🧪 === PROBANDO ENDPOINTS DEL CARRITO ===")
    
    # Primero agregar un producto
    print("\n1. Agregando producto al carrito...")
    try:
        # Obtener productos
        products_response = requests.get(f"{SERVER_URL}/api/productos/venta/")
        if products_response.status_code == 200:
            products = products_response.json()
            if products:
                product_id = products[0]['_id']
                print(f"✅ Producto seleccionado: {products[0]['nombre']}")
                
                # Obtener la página del carrito para obtener el CSRF token
                carrito_response = requests.get(f"{SERVER_URL}/carrito/")
                session = requests.Session()
                
                # Obtener cookies de la respuesta
                cookies = carrito_response.cookies
                csrf_token = cookies.get('csrftoken')
                
                if csrf_token:
                    print(f"✅ CSRF token obtenido: {csrf_token}")
                    
                    # Agregar producto
                    add_response = session.post(
                        f"{SERVER_URL}/carrito/agregar/{product_id}/",
                        json={"sucursal_id": None},
                        headers={
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrf_token,
                            'Referer': f"{SERVER_URL}/carrito/"
                        },
                        cookies=cookies
                    )
                    
                    print(f"📥 Respuesta agregar: {add_response.status_code}")
                    if add_response.status_code == 200:
                        result = add_response.json()
                        print(f"✅ Producto agregado: {result}")
                    else:
                        print(f"❌ Error al agregar: {add_response.text}")
                else:
                    print("❌ No se pudo obtener CSRF token")
            else:
                print("❌ No hay productos disponibles")
        else:
            print(f"❌ Error al obtener productos: {products_response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_carrito_html():
    """Probar que el HTML del carrito se carga correctamente"""
    print("\n2. Probando carga del HTML del carrito...")
    
    try:
        response = requests.get(f"{SERVER_URL}/carrito/")
        print(f"📥 Respuesta HTML: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Buscar elementos importantes
            checks = [
                ('updateQuantity', 'updateQuantity' in html_content),
                ('removeItem', 'removeItem' in html_content),
                ('CSRF Token', 'csrfToken' in html_content),
                ('data-item-id', 'data-item-id' in html_content),
                ('Bootstrap', 'bootstrap' in html_content),
                ('Carrito de Compras', 'Carrito de Compras' in html_content)
            ]
            
            print("✅ Elementos encontrados:")
            for name, found in checks:
                status = "✅" if found else "❌"
                print(f"   {status} {name}: {'Presente' if found else 'Ausente'}")
            
            # Buscar placeholders problemáticos
            problematic = [
                'via.placeholder.com',
                'placeholder.com'
            ]
            
            for problem in problematic:
                if problem in html_content:
                    print(f"   ⚠️  Placeholder problemático encontrado: {problem}")
            
        else:
            print(f"❌ Error al cargar HTML: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🛒 === DIAGNÓSTICO DEL CARRITO ===")
    
    test_carrito_html()
    test_carrito_endpoints()
    
    print("\n📝 === INSTRUCCIONES ===")
    print("1. Abre el navegador en: http://127.0.0.1:8000/carrito/")
    print("2. Agrega un producto al carrito")
    print("3. Intenta cambiar la cantidad usando los botones +/-")
    print("4. Revisa la consola del navegador (F12) para ver errores")
    print("5. Si hay errores, copia y pega el mensaje de error")

if __name__ == "__main__":
    main()
