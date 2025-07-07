#!/usr/bin/env python3
"""
Script para diagnosticar el flujo de Webpay
"""

import requests
import json
import sys
from pathlib import Path

SERVER_URL = "http://127.0.0.1:8000"

def test_webpay_flow():
    """Probar el flujo completo de Webpay"""
    print("💳 === DIAGNÓSTICO DE WEBPAY ===")
    
    try:
        # 1. Verificar que hay productos en el carrito
        print("\n1. Verificando carrito...")
        carrito_response = requests.get(f"{SERVER_URL}/carrito/", timeout=10)
        
        if carrito_response.status_code == 200:
            html_content = carrito_response.text
            
            # Buscar elementos del carrito
            import re
            item_ids = re.findall(r'data-item-id="([^"]+)"', html_content)
            
            if not item_ids:
                print("⚠️ El carrito está vacío. Agregando producto...")
                
                # Agregar un producto primero
                products_response = requests.get(f"{SERVER_URL}/api/productos/venta/", timeout=10)
                if products_response.status_code == 200:
                    products = products_response.json()
                    if products:
                        product_id = products[0]['_id']
                        
                        # Obtener CSRF token
                        csrf_match = re.search(r'content="([^"]+)"[^>]*name="csrf-token"', html_content)
                        if csrf_match:
                            csrf_token = csrf_match.group(1)
                            
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
                            
                            if add_response.status_code == 200:
                                result = add_response.json()
                                if result.get('success'):
                                    print("✅ Producto agregado al carrito")
                                else:
                                    print(f"❌ Error al agregar producto: {result.get('error')}")
                                    return False
                        else:
                            print("❌ No se pudo obtener CSRF token")
                            return False
            else:
                print(f"✅ Carrito tiene {len(item_ids)} productos")
            
            # 2. Probar inicio de pago con Webpay
            print("\n2. Probando inicio de pago con Webpay...")
            
            # Usar una sesión para mantener cookies
            session = requests.Session()
            
            # Obtener la página del carrito con la sesión
            carrito_response = session.get(f"{SERVER_URL}/carrito/", timeout=10)
            
            # Intentar iniciar pago
            webpay_response = session.get(f"{SERVER_URL}/carrito/pagar/", timeout=10, allow_redirects=False)
            
            print(f"📥 Respuesta Webpay: {webpay_response.status_code}")
            
            if webpay_response.status_code == 302:
                # Redirección exitosa
                redirect_url = webpay_response.headers.get('Location', '')
                print(f"✅ Redirección a: {redirect_url}")
                
                if 'webpay' in redirect_url.lower() or 'transbank' in redirect_url.lower():
                    print("✅ Redirección a Webpay exitosa")
                    return True
                else:
                    print(f"⚠️ Redirección no parece ser a Webpay: {redirect_url}")
                    
            elif webpay_response.status_code == 200:
                # No hubo redirección, revisar contenido
                html_content = webpay_response.text
                
                if 'error' in html_content.lower():
                    print("❌ Página de error detectada")
                    # Buscar mensaje de error específico
                    error_match = re.search(r'<p[^>]*>([^<]*error[^<]*)</p>', html_content, re.IGNORECASE)
                    if error_match:
                        print(f"   Error: {error_match.group(1).strip()}")
                    
                    # Buscar más detalles del error
                    if 'carrito está vacío' in html_content:
                        print("   🛒 El carrito está vacío")
                    elif 'monto es inválido' in html_content:
                        print("   💰 El monto es inválido")
                    elif 'transbank' in html_content.lower():
                        print("   🏦 Error de Transbank")
                    
                    return False
                else:
                    print("❌ No hubo redirección a Webpay")
                    print(f"   Contenido: {html_content[:200]}...")
                    return False
                    
            else:
                print(f"❌ Error HTTP: {webpay_response.status_code}")
                try:
                    print(f"   Respuesta: {webpay_response.text[:200]}...")
                except:
                    print("   No se pudo leer la respuesta")
                return False
        
        else:
            print(f"❌ Error al cargar carrito: {carrito_response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        return False

def test_webpay_urls():
    """Probar URLs de Webpay"""
    print("\n🔗 === PROBANDO URLS DE WEBPAY ===")
    
    urls_to_test = [
        ("/carrito/pagar/", "Iniciar pago"),
        ("/carrito/webpay/respuesta/", "Respuesta Webpay"),
        ("/carrito/webpay/debug/", "Debug Webpay"),
        ("/carrito/webpay/test/", "Test Webpay")
    ]
    
    for url, description in urls_to_test:
        try:
            response = requests.get(f"{SERVER_URL}{url}", timeout=5, allow_redirects=False)
            print(f"✅ {description}: {response.status_code}")
            
            if response.status_code == 500:
                print(f"   ⚠️ Error interno del servidor")
            elif response.status_code == 404:
                print(f"   ❌ URL no encontrada")
                
        except Exception as e:
            print(f"❌ {description}: Error de conexión - {e}")

def main():
    """Función principal"""
    print("🧪 === DIAGNÓSTICO COMPLETO DE WEBPAY ===")
    
    test_webpay_urls()
    
    if test_webpay_flow():
        print("\n🎉 === WEBPAY FUNCIONANDO CORRECTAMENTE ===")
    else:
        print("\n⚠️ === PROBLEMAS DETECTADOS EN WEBPAY ===")
        print("\n🔧 === POSIBLES SOLUCIONES ===")
        print("1. Verificar que el carrito tenga productos")
        print("2. Revisar configuración de Transbank")
        print("3. Verificar credenciales de API")
        print("4. Comprobar conectividad con Transbank")
    
    print("\n📝 === INSTRUCCIONES PARA PRUEBA MANUAL ===")
    print("1. Ve a http://127.0.0.1:8000/productos/venta/")
    print("2. Agrega algunos productos al carrito")
    print("3. Ve a http://127.0.0.1:8000/carrito/")
    print("4. Haz clic en 'Pagar con Webpay'")
    print("5. Deberías ser redirigido a la página de Transbank")

if __name__ == "__main__":
    main()
