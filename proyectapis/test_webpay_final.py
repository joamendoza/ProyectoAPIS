"""
Test directo del botón de Webpay sin CSRF
"""
import requests
import json

def test_webpay_without_csrf():
    """Test del botón de Webpay simulando el flujo del frontend"""
    print("=== TEST DIRECTO DEL BOTÓN DE WEBPAY ===")
    
    session = requests.Session()
    
    # Headers para simular navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    try:
        # 1. Obtener página principal para establecer sesión
        print("1. Estableciendo sesión...")
        response = session.get("http://localhost:8000/")
        print(f"Status: {response.status_code}")
        
        # 2. Obtener productos
        print("\n2. Obteniendo productos...")
        productos_response = session.get("http://localhost:8000/api/productos/")
        if productos_response.status_code != 200:
            print(f"❌ Error al obtener productos: {productos_response.status_code}")
            return False
        
        productos = productos_response.json()
        if not productos:
            print("❌ No hay productos disponibles")
            return False
        
        primer_producto = productos[0]
        producto_id = primer_producto['_id']
        print(f"Producto a usar: {primer_producto['nombre']} (ID: {producto_id})")
        
        # 3. Agregar producto al carrito usando JSON
        print("\n3. Agregando producto al carrito...")
        
        # Obtener CSRF token de las cookies
        csrf_token = session.cookies.get('csrftoken')
        
        # Preparar datos para agregar al carrito
        cart_data = {
            'cantidad': 1,
            'sucursal': 'Sucursal Centro'
        }
        
        # Configurar headers con CSRF token si está disponible
        request_headers = headers.copy()
        if csrf_token:
            request_headers['X-CSRFToken'] = csrf_token
        
        add_response = session.post(
            f"http://localhost:8000/carrito/agregar/{producto_id}/",
            headers=request_headers,
            json=cart_data
        )
        
        print(f"Status agregar: {add_response.status_code}")
        
        if add_response.status_code not in [200, 201]:
            print(f"❌ Error al agregar producto: {add_response.content}")
            # Intentar con POST form data
            print("Intentando con form data...")
            form_data = {
                'cantidad': 1,
                'sucursal': 'Sucursal Centro'
            }
            if csrf_token:
                form_data['csrfmiddlewaretoken'] = csrf_token
            
            add_response = session.post(
                f"http://localhost:8000/carrito/agregar/{producto_id}/",
                data=form_data,
                headers={'Referer': 'http://localhost:8000/'}
            )
            print(f"Status con form data: {add_response.status_code}")
            
            if add_response.status_code not in [200, 201, 302]:
                print(f"❌ Error persistente: {add_response.content}")
                return False
        
        # 4. Verificar carrito
        print("\n4. Verificando carrito...")
        carrito_response = session.get("http://localhost:8000/carrito/")
        print(f"Status carrito: {carrito_response.status_code}")
        
        if carrito_response.status_code != 200:
            print(f"❌ Error al verificar carrito: {carrito_response.content}")
            return False
        
        # 5. Intentar pagar con Webpay
        print("\n5. Intentando pagar con Webpay...")
        
        # Obtener CSRF token actualizado
        csrf_token = session.cookies.get('csrftoken')
        
        # Preparar datos para pago
        pago_data = {}
        if csrf_token:
            pago_data['csrfmiddlewaretoken'] = csrf_token
        
        # Realizar solicitud de pago
        pago_response = session.post(
            "http://localhost:8000/carrito/pagar/",
            data=pago_data,
            allow_redirects=False,
            headers={'Referer': 'http://localhost:8000/carrito/'}
        )
        
        print(f"Status pago: {pago_response.status_code}")
        
        if pago_response.status_code == 302:
            redirect_url = pago_response.headers.get('Location', '')
            print(f"✅ Redirección detectada: {redirect_url}")
            
            # Verificar si es redirección a Webpay
            if 'webpay' in redirect_url.lower() or 'transbank' in redirect_url.lower():
                print("🎉 ¡ÉXITO! Redirigiendo correctamente a Webpay!")
                return True
            else:
                print(f"❌ Redirección no es a Webpay: {redirect_url}")
                
                # Seguir la redirección para diagnosticar
                if redirect_url.startswith('/'):
                    redirect_url = "http://localhost:8000" + redirect_url
                
                follow_response = session.get(redirect_url)
                print(f"Status página destino: {follow_response.status_code}")
                
                if 'error' in follow_response.text.lower():
                    print("❌ Página de error detectada")
                    # Extraer mensaje de error específico
                    content = follow_response.text
                    if 'carrito está vacío' in content.lower():
                        print("💡 El carrito parece estar vacío")
                    elif 'monto' in content.lower() and 'inválido' in content.lower():
                        print("💡 Problema con el monto del carrito")
                    elif 'transbank' in content.lower():
                        print("💡 Error relacionado con Transbank")
                return False
        
        elif pago_response.status_code == 200:
            print("❌ No hubo redirección - posible error")
            content = pago_response.text
            if 'error' in content.lower():
                print("❌ Página de error mostrada")
                if 'carrito está vacío' in content.lower():
                    print("💡 El carrito parece estar vacío")
        
        else:
            print(f"❌ Error en solicitud de pago: {pago_response.status_code}")
            print(f"Contenido: {pago_response.content[:300]}...")
        
        return False
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_webpay_without_csrf()
    if success:
        print("\n✅ Test exitoso - El botón de Webpay funciona correctamente")
    else:
        print("\n❌ Test fallido - Revisar configuración del botón de Webpay")
