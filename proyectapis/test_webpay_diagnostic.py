"""
Script de diagnóstico específico para el botón de Webpay
"""
import requests
import json
import os
import sys
from datetime import datetime

# Configuración del servidor
BASE_URL = "http://localhost:8000"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test_webpay_button_diagnostic():
    """Diagnosticar el problema del botón de Webpay"""
    print("=== DIAGNÓSTICO DEL BOTÓN DE WEBPAY ===")
    
    # Crear una sesión para mantener cookies
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        # 1. Primero ir a la página de productos para obtener CSRF token
        print("\n1. Obteniendo CSRF token...")
        response = session.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print(f"❌ Error al acceder a la página de productos: {response.status_code}")
            return False
        
        # Extraer CSRF token
        csrf_token = None
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        
        if not csrf_token:
            # Intentar extraer del HTML
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        if not csrf_token:
            print("❌ No se pudo obtener el CSRF token")
            return False
        
        print(f"✅ CSRF token obtenido: {csrf_token[:20]}...")
        
        # 2. Agregar un producto al carrito
        print("\n2. Agregando producto al carrito...")
        product_data = {
            'producto_id': '6742b95c2f8e1b4e3c123456',  # ID de ejemplo
            'cantidad': 1,
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(f"{BASE_URL}/carrito/agregar/", data=product_data)
        print(f"Status de agregar producto: {response.status_code}")
        
        # 3. Verificar que hay productos en el carrito
        print("\n3. Verificando carrito...")
        response = session.get(f"{BASE_URL}/carrito/")
        if response.status_code != 200:
            print(f"❌ Error al acceder al carrito: {response.status_code}")
            return False
        
        print(f"✅ Carrito accesible. Contenido: {len(response.content)} bytes")
        
        # 4. Intentar iniciar pago con Webpay
        print("\n4. Intentando iniciar pago con Webpay...")
        
        # Actualizar CSRF token si es necesario
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        
        pago_data = {
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(f"{BASE_URL}/carrito/pagar/", data=pago_data, allow_redirects=False)
        
        print(f"Status de iniciar pago: {response.status_code}")
        print(f"Headers de respuesta: {dict(response.headers)}")
        
        if response.status_code == 302:
            # Redirección - obtener URL de destino
            redirect_url = response.headers.get('Location', '')
            print(f"✅ Redirección a: {redirect_url}")
            
            # Seguir la redirección
            if redirect_url:
                if redirect_url.startswith('/'):
                    redirect_url = BASE_URL + redirect_url
                
                print(f"\n5. Siguiendo redirección a: {redirect_url}")
                response = session.get(redirect_url)
                print(f"Status de página de destino: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Página cargada correctamente")
                    # Verificar si es página de error
                    if 'pago_fallido' in response.url or 'error' in response.text.lower():
                        print("❌ La página de destino es una página de error")
                        # Extraer mensaje de error
                        import re
                        error_match = re.search(r'<div[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)', response.text, re.IGNORECASE)
                        if error_match:
                            print(f"Mensaje de error: {error_match.group(1).strip()}")
                        return False
                    else:
                        print("✅ Redirigido a página de pago exitosamente")
                        return True
                else:
                    print(f"❌ Error al cargar página de destino: {response.status_code}")
                    return False
        
        elif response.status_code == 200:
            # No hubo redirección, revisar contenido
            if 'pago_fallido' in response.text or 'error' in response.text.lower():
                print("❌ Se mostró página de error directamente")
                # Extraer mensaje de error
                import re
                error_match = re.search(r'<div[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)', response.text, re.IGNORECASE)
                if error_match:
                    print(f"Mensaje de error: {error_match.group(1).strip()}")
                return False
            else:
                print("✅ Página de pago cargada correctamente")
                return True
        
        else:
            print(f"❌ Error al iniciar pago: {response.status_code}")
            if response.content:
                print(f"Contenido de respuesta: {response.content[:500]}...")
            return False
    
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        return False

def check_webpay_configuration():
    """Verificar configuración de Webpay"""
    print("\n=== VERIFICACIÓN DE CONFIGURACIÓN WEBPAY ===")
    
    try:
        # Verificar que las librerías de Transbank están instaladas
        from transbank.webpay.webpay_plus.transaction import Transaction
        from transbank.common.options import WebpayOptions
        from transbank.common.integration_type import IntegrationType
        print(f"✅ Transbank SDK instalado correctamente")
        
        # Verificar configuración de prueba
        options = WebpayOptions(
            commerce_code="597055555532",
            api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
            integration_type=IntegrationType.TEST
        )
        
        tx = Transaction(options)
        print("✅ Configuración de Webpay TEST creada correctamente")
        
        # Intentar crear una transacción de prueba
        try:
            response = tx.create(
                buy_order="test-order-123",
                session_id="test-session",
                amount=1000,
                return_url="http://localhost:8000/carrito/webpay/respuesta/"
            )
            print("✅ Transacción de prueba creada exitosamente")
            print(f"URL de pago: {response.get('url', 'No URL')}")
            print(f"Token: {response.get('token', 'No token')}")
            return True
        except Exception as e:
            print(f"❌ Error al crear transacción de prueba: {e}")
            return False
    
    except ImportError as e:
        print(f"❌ Error al importar Transbank SDK: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en verificación de configuración: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    print("DIAGNÓSTICO COMPLETO DEL BOTÓN DE WEBPAY")
    print("=" * 50)
    
    # Verificar configuración
    config_ok = check_webpay_configuration()
    
    if not config_ok:
        print("\n❌ La configuración de Webpay tiene problemas")
        print("Verifica que el SDK de Transbank esté instalado correctamente")
        return
    
    # Realizar diagnóstico del botón
    button_ok = test_webpay_button_diagnostic()
    
    if button_ok:
        print("\n✅ El botón de Webpay funciona correctamente")
    else:
        print("\n❌ El botón de Webpay tiene problemas")
        print("Revisa los logs del servidor para más detalles")

if __name__ == "__main__":
    main()
