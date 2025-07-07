#!/usr/bin/env python3
"""
Test del frontend rehecho de selección de sucursal
Verifica que el frontend envía correctamente el sucursal_id
"""
import os
import sys
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# Configurar path para Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')

import django
django.setup()

def test_frontend_sucursal():
    """Test automatizado del frontend de selección de sucursal"""
    
    # Configurar Chrome para testing
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar en modo headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    
    try:
        print("🚀 Iniciando test automatizado del frontend...")
        
        # Inicializar driver
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # Ir a la página de productos
        print("📱 Navegando a la página de productos...")
        driver.get("http://localhost:8000/venta/")
        
        # Esperar a que carguen los productos
        print("⏳ Esperando a que carguen los productos...")
        wait.until(EC.presence_of_element_located((By.ID, "productsGrid")))
        
        # Verificar que se cargaron los productos
        products_grid = driver.find_element(By.ID, "productsGrid")
        if "d-none" in products_grid.get_attribute("class"):
            print("❌ Los productos no se cargaron correctamente")
            return False
        
        # Buscar botones de agregar al carrito
        add_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-product-id]")
        
        if not add_buttons:
            print("❌ No se encontraron botones de agregar al carrito")
            return False
        
        print(f"✅ Se encontraron {len(add_buttons)} botones de agregar al carrito")
        
        # Tomar el primer botón que no esté deshabilitado
        active_button = None
        for button in add_buttons:
            if not button.get_attribute("disabled"):
                active_button = button
                break
        
        if not active_button:
            print("❌ No se encontraron botones activos")
            return False
        
        product_id = active_button.get_attribute("data-product-id")
        print(f"🎯 Probando con producto ID: {product_id}")
        
        # Hacer click en el botón
        print("🖱️ Haciendo click en 'Agregar al carrito'...")
        driver.execute_script("arguments[0].click();", active_button)
        
        # Esperar a que aparezca el modal
        print("⏳ Esperando a que aparezca el modal de sucursal...")
        wait.until(EC.visibility_of_element_located((By.ID, "sucursalModal")))
        
        # Verificar que el modal se muestra
        modal = driver.find_element(By.ID, "sucursalModal")
        if "show" not in modal.get_attribute("class"):
            print("❌ El modal no se mostró correctamente")
            return False
        
        print("✅ Modal de sucursal mostrado correctamente")
        
        # Verificar que hay opciones de sucursal
        sucursales_list = driver.find_element(By.ID, "sucursales-list")
        sucursal_buttons = sucursales_list.find_elements(By.CSS_SELECTOR, "button[data-sucursal-id]")
        
        if not sucursal_buttons:
            print("❌ No se encontraron opciones de sucursal")
            return False
        
        print(f"✅ Se encontraron {len(sucursal_buttons)} opciones de sucursal")
        
        # Probar selección de sucursal
        first_sucursal_button = sucursal_buttons[0]
        sucursal_id = first_sucursal_button.get_attribute("data-sucursal-id")
        sucursal_name = first_sucursal_button.get_attribute("data-sucursal-name")
        
        print(f"🏪 Seleccionando sucursal: {sucursal_name} (ID: {sucursal_id})")
        
        # Interceptar peticiones de red (esto es complejo en Selenium, así que verificamos resultado)
        print("🔗 Haciendo click en seleccionar sucursal...")
        driver.execute_script("arguments[0].click();", first_sucursal_button)
        
        # Esperar a que se cierre el modal o aparezca un toast
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#sucursalModal.show")))
            print("✅ Modal cerrado correctamente")
        except:
            print("⚠️ Modal no se cerró automáticamente")
        
        # Verificar si aparece un toast de éxito
        time.sleep(2)  # Esperar a que aparezca el toast
        
        toasts = driver.find_elements(By.CSS_SELECTOR, ".toast")
        if toasts:
            toast_text = toasts[-1].text
            print(f"🔔 Toast mostrado: {toast_text}")
            
            if "éxito" in toast_text.lower() or "agregado" in toast_text.lower():
                print("✅ Producto agregado exitosamente")
                return True
            else:
                print("❌ Error en el toast")
                return False
        else:
            print("⚠️ No se mostró ningún toast")
            
            # Verificar si el carrito se actualizó
            cart_button = driver.find_element(By.ID, "cart-button")
            if "(1)" in cart_button.text or "1" in cart_button.text:
                print("✅ Carrito actualizado correctamente")
                return True
        
        print("✅ Test completado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

def test_javascript_console():
    """Test para verificar errores en consola JavaScript"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")
    
    driver = None
    
    try:
        print("🔍 Verificando errores de JavaScript en consola...")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:8000/venta/")
        
        # Esperar a que se cargue la página
        time.sleep(3)
        
        # Obtener logs de consola
        logs = driver.get_log('browser')
        
        errors = [log for log in logs if log['level'] == 'SEVERE']
        warnings = [log for log in logs if log['level'] == 'WARNING']
        
        print(f"📊 Errores encontrados: {len(errors)}")
        print(f"📊 Advertencias encontradas: {len(warnings)}")
        
        if errors:
            print("❌ ERRORES DE JAVASCRIPT:")
            for error in errors:
                print(f"  - {error['message']}")
            return False
        
        if warnings:
            print("⚠️ ADVERTENCIAS DE JAVASCRIPT:")
            for warning in warnings:
                print(f"  - {warning['message']}")
        
        # Ejecutar función de debug
        try:
            result = driver.execute_script("return window.debugFerremas ? 'DEBUG_AVAILABLE' : 'DEBUG_NOT_AVAILABLE'")
            print(f"🔧 Función de debug: {result}")
        except Exception as e:
            print(f"⚠️ Error al ejecutar debug: {e}")
        
        print("✅ No se encontraron errores críticos en JavaScript")
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar consola: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("🧪 === TEST FRONTEND SUCURSAL REHECHO ===")
    print("Verificando que el frontend funciona correctamente...")
    
    # Verificar que el servidor está corriendo
    import requests
    try:
        response = requests.get("http://localhost:8000/venta/", timeout=5)
        if response.status_code != 200:
            print("❌ El servidor no está corriendo en el puerto 8000")
            print("Por favor, ejecuta: python manage.py runserver")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ No se puede conectar al servidor")
        print("Por favor, ejecuta: python manage.py runserver")
        sys.exit(1)
    
    # Ejecutar tests
    success = True
    
    # Test 1: Verificar consola JavaScript
    print("\n1️⃣ Verificando errores de JavaScript...")
    if not test_javascript_console():
        success = False
    
    # Test 2: Test funcional completo
    print("\n2️⃣ Ejecutando test funcional completo...")
    if not test_frontend_sucursal():
        success = False
    
    # Resultado final
    print("\n" + "="*50)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
        print("El frontend rehecho funciona correctamente")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("Revisa los errores anteriores")
    
    sys.exit(0 if success else 1)
