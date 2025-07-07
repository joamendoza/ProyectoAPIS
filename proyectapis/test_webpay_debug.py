"""
Debug directo del botón de Webpay - Simulando el navegador
"""
import requests
import json

def debug_webpay_direct():
    """Debug directo del botón de Webpay"""
    print("=== DEBUG DIRECTO DEL BOTÓN DE WEBPAY ===")
    
    session = requests.Session()
    
    # Simular headers de navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    session.headers.update(headers)
    
    try:
        # 1. Obtener página principal para establecer sesión
        print("1. Obteniendo página principal...")
        response = session.get("http://localhost:8000/")
        print(f"Status: {response.status_code}")
        
        # 2. Obtener CSRF token de las cookies
        csrf_token = session.cookies.get('csrftoken')
        
        # Si no hay token en cookies, intentar obtenerlo del HTML
        if not csrf_token:
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        print(f"CSRF token: {csrf_token}")
        
        if not csrf_token:
            print("❌ No se pudo obtener CSRF token")
            return False
        
        # 3. Agregar producto al carrito usando la API
        print("\n2. Agregando producto al carrito...")
        
        # Primero obtener la lista de productos
        productos_response = session.get("http://localhost:8000/api/productos/")
        if productos_response.status_code == 200:
            productos = productos_response.json()
            if productos:
                primer_producto = productos[0]
                producto_id = primer_producto['_id']
                print(f"Producto a agregar: {primer_producto['nombre']} (ID: {producto_id})")
                
                # Agregar al carrito
                add_data = {
                    'csrfmiddlewaretoken': csrf_token,
                    'cantidad': 1,
                    'sucursal': 'Sucursal Centro'  # Sucursal por defecto
                }
                
                add_response = session.post(f"http://localhost:8000/carrito/agregar/{producto_id}/", 
                                          data=add_data, 
                                          headers={'Referer': 'http://localhost:8000/'})
                print(f"Status agregar: {add_response.status_code}")
                
                if add_response.status_code not in [200, 302]:
                    print(f"Error al agregar producto: {add_response.content}")
                    return
        
        # 4. Verificar carrito
        print("\n3. Verificando carrito...")
        carrito_response = session.get("http://localhost:8000/carrito/")
        print(f"Status carrito: {carrito_response.status_code}")
        
        if carrito_response.status_code != 200:
            print("Error al acceder al carrito")
            return
        
        # 5. Intentar pagar con Webpay
        print("\n4. Intentando pagar con Webpay...")
        
        # Actualizar CSRF token si es necesario
        csrf_token = session.cookies.get('csrftoken')
        
        pago_data = {
            'csrfmiddlewaretoken': csrf_token
        }
        
        pago_response = session.post("http://localhost:8000/carrito/pagar/", 
                                   data=pago_data, 
                                   allow_redirects=False,
                                   headers={'Referer': 'http://localhost:8000/carrito/'})
        
        print(f"Status pago: {pago_response.status_code}")
        print(f"Headers: {dict(pago_response.headers)}")
        
        if pago_response.status_code == 302:
            redirect_url = pago_response.headers.get('Location')
            print(f"✅ Redirección a: {redirect_url}")
            
            # Verificar si la redirección es a Webpay
            if redirect_url and ('webpay' in redirect_url.lower() or 'transbank' in redirect_url.lower()):
                print("🎉 ¡ÉXITO! Redirigiendo correctamente a Webpay")
                return True
            else:
                print(f"❌ La redirección no es a Webpay")
                
                # Seguir la redirección para ver qué pasa
                if redirect_url:
                    if redirect_url.startswith('/'):
                        redirect_url = "http://localhost:8000" + redirect_url
                    
                    print(f"Siguiendo redirección: {redirect_url}")
                    follow_response = session.get(redirect_url)
                    print(f"Status página destino: {follow_response.status_code}")
                    
                    if 'error' in follow_response.text.lower() or 'fallido' in follow_response.text.lower():
                        print("❌ Página de error detectada")
                        # Intentar extraer el mensaje de error
                        content = follow_response.text
                        if 'error' in content:
                            # Buscar texto después de "error"
                            import re
                            error_match = re.search(r'error[^>]*>([^<]+)', content, re.IGNORECASE)
                            if error_match:
                                print(f"Mensaje de error: {error_match.group(1).strip()}")
                    return False
        
        elif pago_response.status_code == 200:
            print("❌ No hubo redirección")
            content = pago_response.text
            if 'error' in content.lower() or 'fallido' in content.lower():
                print("❌ Página de error mostrada directamente")
                # Intentar extraer el mensaje de error
                import re
                error_match = re.search(r'error[^>]*>([^<]+)', content, re.IGNORECASE)
                if error_match:
                    print(f"Mensaje de error: {error_match.group(1).strip()}")
            return False
        
        else:
            print(f"❌ Error en respuesta de pago: {pago_response.status_code}")
            print(f"Contenido: {pago_response.content[:500]}")
            return False
    
    except Exception as e:
        print(f"❌ Error durante el debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_webpay_direct()
