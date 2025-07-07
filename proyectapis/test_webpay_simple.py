"""
Script simple para probar el flujo del carrito y Webpay
"""
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "http://localhost:8000"

def test_webpay_flow():
    """Probar el flujo completo del carrito y Webpay"""
    print("=== PRUEBA DEL FLUJO DE WEBPAY ===")
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    try:
        # 1. Obtener página principal
        print("1. Obteniendo página principal...")
        response = session.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Error al obtener página principal")
            return
        
        # 2. Extraer CSRF token
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = None
        
        # Buscar token en meta tag
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta:
            csrf_token = csrf_meta.get('content')
        
        # Buscar token en input hidden
        if not csrf_token:
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
        
        # Obtener de cookies
        if not csrf_token and 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        
        print(f"CSRF token: {csrf_token[:20] if csrf_token else 'NO ENCONTRADO'}...")
        
        # 3. Agregar producto al carrito
        print("\n2. Agregando producto al carrito...")
        
        # Buscar el primer producto disponible
        productos = soup.find_all('div', {'class': 'card'})
        if not productos:
            print("❌ No se encontraron productos")
            return
        
        # Extraer ID del primer producto
        producto_id = None
        for producto in productos:
            btn_agregar = producto.find('button', {'onclick': True})
            if btn_agregar:
                onclick = btn_agregar.get('onclick', '')
                match = re.search(r"'([^']+)'", onclick)
                if match:
                    producto_id = match.group(1)
                    break
        
        if not producto_id:
            print("❌ No se pudo extraer ID del producto")
            return
        
        print(f"ID del producto: {producto_id}")
        
        # Agregar producto al carrito
        data = {
            'producto_id': producto_id,
            'cantidad': 1,
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(f"{BASE_URL}/carrito/agregar/", data=data)
        print(f"Status agregar: {response.status_code}")
        
        # 4. Ir al carrito
        print("\n3. Accediendo al carrito...")
        response = session.get(f"{BASE_URL}/carrito/")
        print(f"Status carrito: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Error al acceder al carrito")
            return
        
        # 5. Probar botón de Webpay
        print("\n4. Probando botón de Webpay...")
        
        # Actualizar CSRF token
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        
        # Buscar el botón de Webpay
        webpay_btn = soup.find('button', string=re.compile(r'Pagar.*Webpay', re.IGNORECASE))
        if not webpay_btn:
            webpay_btn = soup.find('button', {'class': re.compile(r'.*webpay.*', re.IGNORECASE)})
        
        if not webpay_btn:
            print("❌ No se encontró el botón de Webpay")
            # Buscar formularios
            forms = soup.find_all('form')
            print(f"Formularios encontrados: {len(forms)}")
            for i, form in enumerate(forms):
                print(f"  Formulario {i+1}: action='{form.get('action')}', method='{form.get('method')}'")
            return
        
        print("✅ Botón de Webpay encontrado")
        
        # Obtener la acción del formulario
        form = webpay_btn.find_parent('form')
        if not form:
            print("❌ No se encontró el formulario del botón de Webpay")
            return
        
        action = form.get('action', '')
        method = form.get('method', 'GET').upper()
        
        print(f"Formulario: action='{action}', method='{method}'")
        
        # Preparar datos para el envío
        form_data = {
            'csrfmiddlewaretoken': csrf_token
        }
        
        # Agregar otros inputs del formulario
        for input_elem in form.find_all('input'):
            name = input_elem.get('name')
            value = input_elem.get('value', '')
            if name and name != 'csrfmiddlewaretoken':
                form_data[name] = value
        
        # Enviar solicitud
        if method == 'POST':
            response = session.post(f"{BASE_URL}{action}", data=form_data, allow_redirects=False)
        else:
            response = session.get(f"{BASE_URL}{action}", allow_redirects=False)
        
        print(f"Status de pago: {response.status_code}")
        
        # Verificar respuesta
        if response.status_code == 302:
            redirect_url = response.headers.get('Location', '')
            print(f"✅ Redirección a: {redirect_url}")
            
            if 'webpay' in redirect_url.lower() or 'transbank' in redirect_url.lower():
                print("✅ Redirigiendo correctamente a Webpay!")
                return True
            else:
                print(f"❌ Redirección no es a Webpay: {redirect_url}")
        
        elif response.status_code == 200:
            # Verificar si es página de error
            if 'error' in response.text.lower() or 'fallido' in response.text.lower():
                print("❌ Se mostró página de error")
                # Extraer mensaje de error
                soup = BeautifulSoup(response.content, 'html.parser')
                error_msg = soup.find('div', {'class': re.compile(r'.*error.*', re.IGNORECASE)})
                if error_msg:
                    print(f"Mensaje de error: {error_msg.get_text(strip=True)}")
            else:
                print("✅ Página de respuesta cargada")
        
        else:
            print(f"❌ Error en respuesta: {response.status_code}")
            print(f"Contenido: {response.content[:200]}...")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_webpay_flow()
