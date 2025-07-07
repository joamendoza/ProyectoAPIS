#!/usr/bin/env python3
"""
Test directo del endpoint de estado del carrito
"""
import os
import sys
import json
from pathlib import Path

# Configurar path para Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')

import django
django.setup()

from django.test import RequestFactory
from django.http import HttpRequest
from carrito.views_mongo import estado_carrito_mongo

def test_estado_carrito_endpoint():
    """Test directo del endpoint de estado del carrito"""
    
    print("🧪 === TEST DEL ENDPOINT DE ESTADO DEL CARRITO ===")
    
    # Crear request factory
    factory = RequestFactory()
    
    # Crear request simulado
    request = factory.get('/carrito/estado/')
    
    # Simular session (necesario para get_usuario_id_unico)
    request.session = {}
    
    try:
        # Llamar a la vista directamente
        response = estado_carrito_mongo(request)
        
        print(f"✅ Respuesta generada exitosamente")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Content-Type: {response.get('Content-Type', 'No definido')}")
        
        # Obtener el contenido JSON
        content = response.content.decode('utf-8')
        print(f"📝 Contenido: {content}")
        
        # Parsear JSON
        data = json.loads(content)
        print(f"📋 Datos parseados:")
        print(f"   - success: {data.get('success', 'N/A')}")
        print(f"   - itemCount: {data.get('itemCount', 'N/A')}")
        print(f"   - totalAmount: {data.get('totalAmount', 'N/A')}")
        print(f"   - items: {len(data.get('items', []))} items")
        
        if data.get('success'):
            print("✅ El endpoint funciona correctamente")
            return True
        else:
            print(f"❌ Error en el endpoint: {data.get('error', 'Error desconocido')}")
            return False
        
    except Exception as e:
        print(f"❌ Error al ejecutar el endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_views():
    """Test de importación de vistas"""
    
    print("🔍 === TEST DE IMPORTACIÓN DE VISTAS ===")
    
    try:
        from carrito.views_mongo import estado_carrito_mongo
        print("✅ vista estado_carrito_mongo importada correctamente")
        
        from carrito.views_mongo import contar_carrito_mongo
        print("✅ vista contar_carrito_mongo importada correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

def test_url_patterns():
    """Test de configuración de URLs"""
    
    print("🔗 === TEST DE CONFIGURACIÓN DE URLS ===")
    
    try:
        from django.urls import reverse
        from django.test import RequestFactory
        
        # Intentar resolver la URL
        try:
            url = reverse('estado_carrito_mongo')
            print(f"✅ URL 'estado_carrito_mongo' resuelve a: {url}")
        except Exception as e:
            print(f"❌ Error al resolver URL: {e}")
            return False
        
        # Verificar que la URL está en el patrón
        from carrito.urls_mongo import urlpatterns
        estado_pattern = None
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name == 'estado_carrito_mongo':
                estado_pattern = pattern
                break
        
        if estado_pattern:
            print(f"✅ Patrón encontrado: {estado_pattern.pattern}")
            return True
        else:
            print("❌ Patrón no encontrado en urls_mongo.py")
            return False
        
    except Exception as e:
        print(f"❌ Error en test de URLs: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DIAGNÓSTICO COMPLETO DEL ENDPOINT DE CARRITO")
    print("="*50)
    
    success = True
    
    # Test 1: Importación
    print("\n1️⃣ Test de importación...")
    if not test_import_views():
        success = False
    
    # Test 2: URLs
    print("\n2️⃣ Test de configuración de URLs...")
    if not test_url_patterns():
        success = False
    
    # Test 3: Endpoint
    print("\n3️⃣ Test del endpoint...")
    if not test_estado_carrito_endpoint():
        success = False
    
    # Resultado final
    print("\n" + "="*50)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
        print("El endpoint debería funcionar correctamente")
        print("Si aún hay errores, reinicia el servidor Django")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("Revisa los errores anteriores")
    
    sys.exit(0 if success else 1)
