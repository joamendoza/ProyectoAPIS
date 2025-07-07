#!/usr/bin/env python3
"""
Script para verificar que el frontend está completamente limpio de placeholders externos
y funciona con el sistema de placeholders locales.
"""

import os
import re
import sys
import json
import requests
from pathlib import Path

# Configuración
BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "ferremas" / "templates" / "productos_venta.html"
SERVER_URL = "http://127.0.0.1:8000"

def test_template_clean():
    """Verificar que el template no tiene referencias a placeholders externos"""
    print("🔍 === VERIFICANDO TEMPLATE LIMPIO ===")
    
    if not TEMPLATE_PATH.exists():
        print(f"❌ Template no encontrado: {TEMPLATE_PATH}")
        return False
    
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar referencias problemáticas
    problematic_patterns = [
        r'via\.placeholder\.com',
        r'placeholder\.com',
        r'loading.*spinner',
        r'loading.*state',
        r'error.*state',
        r'#loading',
        r'#error',
        r'getElementById.*loading',
        r'getElementById.*error'
    ]
    
    issues = []
    for pattern in problematic_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            issues.append(f"Encontrado patrón problemático: {pattern} ({len(matches)} ocurrencias)")
    
    if issues:
        print("❌ Problemas encontrados:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("✅ Template limpio - sin referencias a placeholders externos")
    return True

def test_category_icons():
    """Verificar que la función getCategoryIcon está definida"""
    print("\n🎨 === VERIFICANDO ÍCONOS DE CATEGORÍAS ===")
    
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar función getCategoryIcon
    if 'function getCategoryIcon' not in content:
        print("❌ Función getCategoryIcon no encontrada")
        return False
    
    # Buscar mapeo de categorías
    category_pattern = r"'(\w+)':\s*'(fas?\s+fa-[\w-]+)'"
    categories = re.findall(category_pattern, content)
    
    if not categories:
        print("❌ No se encontraron categorías mapeadas")
        return False
    
    print(f"✅ Función getCategoryIcon encontrada con {len(categories)} categorías:")
    for cat, icon in categories:
        print(f"  - {cat}: {icon}")
    
    return True

def test_local_placeholders():
    """Verificar que se usan placeholders locales"""
    print("\n🏠 === VERIFICANDO PLACEHOLDERS LOCALES ===")
    
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar div de placeholder local
    local_placeholder_patterns = [
        r'product-image-placeholder',
        r'linear-gradient.*f8f9fa',
        r'border.*dashed.*ced4da',
        r'fas fa-.*fa-3x'
    ]
    
    found_patterns = 0
    for pattern in local_placeholder_patterns:
        if re.search(pattern, content):
            found_patterns += 1
    
    if found_patterns < 3:
        print("❌ Placeholders locales no encontrados o incompletos")
        return False
    
    print("✅ Placeholders locales implementados correctamente")
    return True

def test_api_connection():
    """Verificar conexión con la API"""
    print("\n🌐 === VERIFICANDO CONEXIÓN API ===")
    
    try:
        response = requests.get(f"{SERVER_URL}/api/productos/venta/", timeout=5)
        if response.status_code == 200:
            products = response.json()
            print(f"✅ API funcionando - {len(products)} productos disponibles")
            return True
        else:
            print(f"❌ API retornó error {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_frontend_structure():
    """Verificar estructura del frontend"""
    print("\n🏗️ === VERIFICANDO ESTRUCTURA FRONTEND ===")
    
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Elementos esenciales
    essential_elements = [
        'productsGrid',
        'sucursalModal',
        'createProductCard',
        'loadProducts',
        'displayProducts',
        'handleAddToCartClick',
        'showSucursalModal'
    ]
    
    missing_elements = []
    for element in essential_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Elementos faltantes: {missing_elements}")
        return False
    
    print("✅ Estructura del frontend completa")
    return True

def main():
    """Función principal"""
    print("🧪 === PRUEBA FINAL DEL FRONTEND LIMPIO ===")
    
    tests = [
        ("Template limpio", test_template_clean),
        ("Íconos de categorías", test_category_icons),
        ("Placeholders locales", test_local_placeholders),
        ("Conexión API", test_api_connection),
        ("Estructura frontend", test_frontend_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n📊 === RESUMEN DE PRUEBAS ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! Frontend limpio y funcional.")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron. Revisar los issues arriba.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
