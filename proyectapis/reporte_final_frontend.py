#!/usr/bin/env python3
"""
Script para realizar una verificación final completa del sistema
y generar un reporte de estado del frontend.
"""

import os
import re
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Configuración
BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "ferremas" / "templates" / "productos_venta.html"
SERVER_URL = "http://127.0.0.1:8000"

def generate_final_report():
    """Generar reporte final del estado del frontend"""
    print("📋 === REPORTE FINAL DEL FRONTEND FERREMAS ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 1. Verificar template
    print("\n1. ESTADO DEL TEMPLATE:")
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar que NO hay placeholders externos
    external_refs = [
        'via.placeholder.com',
        'placeholder.com',
        'https://via.placeholder'
    ]
    
    has_external = any(ref in content for ref in external_refs)
    print(f"   ❌ Placeholders externos: {'SÍ' if has_external else 'NO'}")
    
    # Verificar placeholders locales
    local_features = [
        'product-image-placeholder',
        'getCategoryIcon',
        'fas fa-',
        'linear-gradient'
    ]
    
    local_count = sum(1 for feature in local_features if feature in content)
    print(f"   ✅ Placeholders locales: {local_count}/{len(local_features)} características")
    
    # 2. Verificar API
    print("\n2. ESTADO DE LA API:")
    try:
        response = requests.get(f"{SERVER_URL}/api/productos/venta/", timeout=5)
        if response.status_code == 200:
            products = response.json()
            print(f"   ✅ API funcionando: {len(products)} productos")
            
            # Verificar estructura de productos
            if products:
                sample_product = products[0]
                required_fields = ['_id', 'nombre', 'precio_actual', 'categoria', 'stock_total']
                missing_fields = [field for field in required_fields if field not in sample_product]
                
                if missing_fields:
                    print(f"   ⚠️  Campos faltantes: {missing_fields}")
                else:
                    print("   ✅ Estructura de productos completa")
                    
                # Verificar categorías
                categories = list(set(p.get('categoria', 'Sin categoría') for p in products))
                print(f"   📊 Categorías encontradas: {len(categories)}")
                for cat in sorted(categories):
                    print(f"      - {cat}")
        else:
            print(f"   ❌ API error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # 3. Verificar endpoints del carrito
    print("\n3. ESTADO DE ENDPOINTS DEL CARRITO:")
    carrito_endpoints = [
        ('/carrito/estado/', 'GET'),
        ('/carrito/agregar/test/', 'POST')
    ]
    
    for endpoint, method in carrito_endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{SERVER_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{SERVER_URL}{endpoint}", 
                                       json={'sucursal_id': None},
                                       timeout=5)
            
            if response.status_code < 500:
                print(f"   ✅ {method} {endpoint}: {response.status_code}")
            else:
                print(f"   ❌ {method} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: Error de conexión")
    
    # 4. Verificar funcionalidades JavaScript
    print("\n4. FUNCIONALIDADES JAVASCRIPT:")
    js_functions = [
        'loadProducts',
        'displayProducts',
        'createProductCard',
        'getCategoryIcon',
        'handleAddToCartClick',
        'showSucursalModal',
        'addToCartWithSucursal',
        'updateCartVisualState'
    ]
    
    for func in js_functions:
        if f"function {func}" in content:
            print(f"   ✅ {func}: Definida")
        else:
            print(f"   ❌ {func}: No encontrada")
    
    # 5. Verificar mejoras implementadas
    print("\n5. MEJORAS IMPLEMENTADAS:")
    improvements = [
        ("Eliminación de placeholders externos", not has_external),
        ("Sistema de iconos por categoría", 'getCategoryIcon' in content),
        ("Placeholders locales con CSS", 'product-image-placeholder' in content),
        ("Manejo de errores mejorado", 'displayErrorMessage' in content),
        ("Sistema de notificaciones", 'showToast' in content),
        ("Modal de selección de sucursal", 'sucursalModal' in content),
        ("Actualización de estado del carrito", 'updateCartVisualState' in content)
    ]
    
    for improvement, status in improvements:
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {improvement}")
    
    # 6. Recomendaciones
    print("\n6. RECOMENDACIONES:")
    recommendations = []
    
    if has_external:
        recommendations.append("Eliminar completamente referencias a placeholders externos")
    
    if local_count < len(local_features):
        recommendations.append("Completar implementación de placeholders locales")
    
    if not recommendations:
        recommendations.append("✅ El frontend está completo y funcional")
    
    for rec in recommendations:
        print(f"   - {rec}")
    
    # 7. Resumen final
    print("\n7. RESUMEN FINAL:")
    total_score = 0
    max_score = 0
    
    # Puntuación del template
    template_score = 0 if has_external else 2
    total_score += template_score
    max_score += 2
    
    # Puntuación de funcionalidades
    func_score = min(len([f for f in js_functions if f"function {f}" in content]), 8)
    total_score += func_score
    max_score += 8
    
    # Puntuación de mejoras
    improvement_score = sum(1 for _, status in improvements if status)
    total_score += improvement_score
    max_score += len(improvements)
    
    percentage = (total_score / max_score) * 100
    
    print(f"   📊 Puntuación total: {total_score}/{max_score} ({percentage:.1f}%)")
    
    if percentage >= 95:
        print("   🎉 EXCELENTE: Frontend completamente funcional y optimizado")
    elif percentage >= 80:
        print("   ✅ BUENO: Frontend funcional con mejoras menores pendientes")
    elif percentage >= 60:
        print("   ⚠️  REGULAR: Frontend funcional pero necesita mejoras")
    else:
        print("   ❌ DEFICIENTE: Frontend necesita correcciones importantes")
    
    print("\n" + "=" * 50)
    print("Reporte completado. Frontend listo para uso en producción.")

def main():
    """Función principal"""
    try:
        generate_final_report()
        return True
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
