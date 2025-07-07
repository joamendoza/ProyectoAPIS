"""
Test script para verificar los nuevos endpoints de la API de Boletas
"""
import requests
import json
from datetime import datetime, timedelta

def test_boletas_api():
    """Test de la API de boletas"""
    base_url = "http://127.0.0.1:8000/api"
    
    print("🔍 TESTING BOLETAS API ENDPOINTS")
    print("=" * 50)
    
    # Test 1: Consultar todas las boletas
    print("\n1. Consultando todas las boletas:")
    try:
        response = requests.get(f"{base_url}/boletas/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Éxito: {data['count']} boletas encontradas")
            print(f"   Límite: {data['limit']}, Offset: {data['offset']}")
            if data['results']:
                print(f"   Primera boleta: {data['results'][0]['codigo']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    # Test 2: Consultar boletas con filtros
    print("\n2. Consultando boletas con filtros:")
    try:
        # Boletas completadas
        response = requests.get(f"{base_url}/boletas/?estado=completada&limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Boletas completadas: {data['count']}")
        else:
            print(f"❌ Error: {response.status_code}")
            
        # Boletas por fecha (últimos 30 días)
        fecha_desde = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        response = requests.get(f"{base_url}/boletas/?fecha_desde={fecha_desde}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Boletas últimos 30 días: {data['count']}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Obtener detalle de boleta específica
    print("\n3. Obteniendo detalle de boleta específica:")
    try:
        # Primero obtener una boleta para usar como ejemplo
        response = requests.get(f"{base_url}/boletas/?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                boleta_codigo = data['results'][0]['codigo']
                print(f"   Usando boleta: {boleta_codigo}")
                
                # Obtener detalle
                response = requests.get(f"{base_url}/boletas/{boleta_codigo}/")
                if response.status_code == 200:
                    boleta_data = response.json()
                    print(f"✅ Detalle obtenido:")
                    print(f"   Código: {boleta_data['codigo']}")
                    print(f"   Total: ${boleta_data['total']}")
                    print(f"   Fecha: {boleta_data['fecha']}")
                    print(f"   Detalles: {len(boleta_data['detalles'])} productos")
                else:
                    print(f"❌ Error: {response.status_code}")
            else:
                print("⚠️  No hay boletas disponibles para probar")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Obtener estadísticas
    print("\n4. Obteniendo estadísticas de boletas:")
    try:
        response = requests.get(f"{base_url}/boletas/estadisticas/")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Estadísticas obtenidas:")
            print(f"   Total boletas: {stats['resumen']['total_boletas']}")
            print(f"   Total ventas: ${stats['resumen']['total_ventas']}")
            print(f"   Promedio venta: ${stats['resumen']['promedio_venta']}")
            print(f"   Estados: {stats['por_estado']}")
            print(f"   Métodos de pago: {list(stats['por_metodo_pago'].keys())}")
            print(f"   Sucursales: {len(stats['por_sucursal'])} sucursales")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Filtros avanzados
    print("\n5. Probando filtros avanzados:")
    try:
        # Filtro por sucursal
        response = requests.get(f"{base_url}/boletas/?sucursal_id=1")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Boletas sucursal 1: {data['count']}")
        
        # Filtro por método de pago
        response = requests.get(f"{base_url}/boletas/?metodo_pago=webpay")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Boletas Webpay: {data['count']}")
        
        # Paginación
        response = requests.get(f"{base_url}/boletas/?limit=2&offset=0")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Paginación: {len(data['results'])} resultados")
            print(f"   Next: {data['next']}, Previous: {data['previous']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Validación de errores
    print("\n6. Probando validación de errores:")
    try:
        # Boleta inexistente
        response = requests.get(f"{base_url}/boletas/BOL-INEXISTENTE/")
        if response.status_code == 404:
            print("✅ Error 404 correctamente manejado para boleta inexistente")
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
        
        # Filtro de fecha inválido
        response = requests.get(f"{base_url}/boletas/?fecha_desde=fecha-invalida")
        if response.status_code == 400:
            print("✅ Error 400 correctamente manejado para fecha inválida")
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 TESTING COMPLETADO")
    print("\n📝 ENDPOINTS DISPONIBLES:")
    print("   GET /api/boletas/")
    print("   GET /api/boletas/{codigo}/")
    print("   GET /api/boletas/estadisticas/")
    print("\n📋 FILTROS DISPONIBLES:")
    print("   ?codigo=BOL-123")
    print("   ?usuario_id=user123")
    print("   ?fecha_desde=2024-01-01")
    print("   ?fecha_hasta=2024-12-31")
    print("   ?estado=completada")
    print("   ?sucursal_id=1")
    print("   ?metodo_pago=webpay")
    print("   ?limit=50&offset=0")

if __name__ == "__main__":
    test_boletas_api()
