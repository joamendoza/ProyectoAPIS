#!/usr/bin/env python3
"""
Verificar que el frontend sin placeholders funciona correctamente
"""
import os
import sys
from pathlib import Path

# Configurar path para Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')

import django
django.setup()

def test_api_products():
    """Test de la API de productos"""
    
    print("🧪 === TEST API DE PRODUCTOS ===")
    
    try:
        import requests
        
        response = requests.get('http://localhost:8000/api/productos/venta/', timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funciona correctamente")
            print(f"📦 Productos encontrados: {len(data)}")
            
            if len(data) > 0:
                first_product = data[0]
                print(f"🏷️ Primer producto: {first_product.get('nombre', 'Sin nombre')}")
                print(f"💰 Precio: ${first_product.get('precio_actual', 0)}")
                print(f"📊 Stock: {first_product.get('stock_total', 0)}")
                
                # Verificar estructura
                required_fields = ['_id', 'nombre', 'precio_actual', 'stock_total']
                missing_fields = [field for field in required_fields if field not in first_product]
                
                if missing_fields:
                    print(f"⚠️ Campos faltantes: {missing_fields}")
                else:
                    print("✅ Estructura de producto correcta")
                
                return True
            else:
                print("⚠️ No hay productos en la base de datos")
                return False
        else:
            print(f"❌ Error en API: {response.status_code}")
            print(f"📄 Respuesta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar API: {e}")
        return False

def test_frontend_structure():
    """Test de la estructura del frontend"""
    
    print("\n🔍 === TEST ESTRUCTURA FRONTEND ===")
    
    template_path = Path(__file__).parent / 'ferremas' / 'templates' / 'productos_venta.html'
    
    if not template_path.exists():
        print("❌ Template no encontrado")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar que no hay elementos de loading
    if 'id="loading"' in content:
        print("❌ Elemento de loading aún presente")
        return False
    
    if 'id="error"' in content and 'error-message' in content:
        print("❌ Elemento de error aún presente")
        return False
    
    if 'id="noProducts"' in content and 'text-center py-5 d-none' in content:
        print("❌ Elemento noProducts aún presente")
        return False
    
    # Verificar que el grid está visible
    if 'id="productsGrid" class="row d-none"' in content:
        print("❌ Grid de productos aún oculto")
        return False
    
    if 'id="productsGrid" class="row"' in content:
        print("✅ Grid de productos visible por defecto")
    else:
        print("⚠️ Grid de productos no encontrado")
    
    # Verificar funciones JavaScript simplificadas
    if 'function showLoading()' in content:
        print("❌ Función showLoading aún presente")
        return False
    
    if 'function displayProducts(' in content:
        print("✅ Función displayProducts presente")
    else:
        print("❌ Función displayProducts no encontrada")
        return False
    
    if 'function displayErrorMessage(' in content:
        print("✅ Función displayErrorMessage presente")
    else:
        print("❌ Función displayErrorMessage no encontrada")
        return False
    
    print("✅ Estructura del frontend correcta")
    return True

def main():
    """Función principal"""
    
    print("🚀 === VERIFICACIÓN FRONTEND SIN PLACEHOLDERS ===")
    print("="*60)
    
    success = True
    
    # Test 1: API
    if not test_api_products():
        success = False
    
    # Test 2: Estructura frontend
    if not test_frontend_structure():
        success = False
    
    # Instrucciones finales
    print("\n📋 === INSTRUCCIONES DE VERIFICACIÓN MANUAL ===")
    print("="*50)
    print("1. Abre: http://localhost:8000/venta/")
    print("2. Verifica que:")
    print("   ✅ NO aparece spinner de carga")
    print("   ✅ Los productos aparecen inmediatamente")
    print("   ✅ No hay placeholder infinito")
    print("   ✅ Las tarjetas de productos son funcionales")
    print("3. Abre la consola del navegador (F12)")
    print("4. Verifica logs:")
    print("   ✅ '🚀 INICIANDO APLICACIÓN FERREMAS'")
    print("   ✅ '📦 Cargando productos desde la API...'")
    print("   ✅ '✅ Productos cargados: X'")
    print("   ✅ '✅ Productos mostrados correctamente'")
    print("5. Prueba agregar productos al carrito")
    
    print("\n🎯 === RESULTADO ===")
    print("="*30)
    if success:
        print("✅ PLACEHOLDERS ELIMINADOS EXITOSAMENTE")
        print("✅ Frontend simplificado y funcional")
        print("✅ Carga inmediata de productos")
    else:
        print("❌ HAY PROBLEMAS QUE RESOLVER")
        print("Revisa los errores anteriores")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
