#!/usr/bin/env python3
"""
Mapeo completo de todas las templates web del proyecto Ferremas
"""

import os
import re
from pathlib import Path

# Mapeo de URLs activas y sus templates
ACTIVE_URLS_TEMPLATES = {
    # URLs principales de ferremas.web_urls
    '/': 'productos_venta.html',
    '/venta/': 'productos_venta.html', 
    '/inventario/': 'inventario_sucursales.html',
    '/crear-producto/': 'crear_producto_form.html',
    '/actualizar-stock/': 'actualizar_stock_form.html',
    '/carrito/': 'carrito_mongo.html',  # Desde ferremas/templates/
    '/compra-exitosa/': 'compra_exitosa.html',
    '/compra-rechazada/': 'compra_rechazada.html',
    
    # URLs del carrito MongoDB desde carrito.urls_mongo
    '/carrito/productos/': 'lista_productos_mongo.html',  # Desde carrito/templates/carrito/
    
    # URLs de pago desde Webpay
    '/webpay/return/': 'pago_exitoso_mongo.html o pago_fallido_mongo.html',
    
    # URLs de inventario (si están activas)
    '/inventario/productos/': 'inventario/producto_list.html',
    '/inventario/producto/nuevo/': 'inventario/producto_form.html',
    '/inventario/producto/eliminar/': 'inventario/producto_confirm_delete.html',
}

# Templates por categoría y estado
TEMPLATES_BY_CATEGORY = {
    'TEMPLATES_PRINCIPALES_ACTIVAS': [
        'ferremas/templates/productos_venta.html',           # ✅ ACTIVA - Página principal y /venta/
        'ferremas/templates/inventario_sucursales.html',     # ✅ ACTIVA - /inventario/
        'ferremas/templates/crear_producto_form.html',       # ✅ ACTIVA - /crear-producto/
        'ferremas/templates/actualizar_stock_form.html',     # ✅ ACTIVA - /actualizar-stock/
        'ferremas/templates/carrito_mongo.html',             # ✅ ACTIVA - /carrito/
        'ferremas/templates/pago_exitoso_mongo.html',        # ✅ ACTIVA - Resultado exitoso Webpay
        'ferremas/templates/pago_fallido_mongo.html',        # ✅ ACTIVA - Resultado fallido Webpay
    ],
    
    'TEMPLATES_CARRITO_ACTIVAS': [
        'carrito/templates/carrito/carrito_mongo.html',      # ❓ POSIBLE DUPLICADO
        'carrito/templates/carrito/lista_productos_mongo.html', # ✅ ACTIVA - /carrito/productos/
        'carrito/templates/carrito/pago_exitoso.html',       # ❓ POSIBLE ALTERNATIVA
        'carrito/templates/carrito/pago_fallido.html',       # ❓ POSIBLE ALTERNATIVA
    ],
    
    'TEMPLATES_INVENTARIO_ACTIVAS': [
        'inventario/templates/inventario/producto_list.html',    # ❓ CONDICIONAL
        'inventario/templates/inventario/producto_form.html',    # ❓ CONDICIONAL  
        'inventario/templates/inventario/producto_confirm_delete.html', # ❓ CONDICIONAL
    ],
    
    'TEMPLATES_BACKUP_DESARROLLO': [
        'ferremas/templates/productos_venta_clean.html',     # 🔄 BACKUP
        'ferremas/templates/productos_venta_backup.html',    # 🔄 BACKUP
        'ferremas/templates/carrito.html',                   # 🔄 BACKUP/ALTERNATIVA
        'ferremas/templates/carrito_backup.html',            # 🔄 BACKUP
        'ferremas/templates/carrito_nuevo.html',             # 🔄 DESARROLLO
        'ferremas/templates/carrito_mongo_nuevo.html',       # 🔄 DESARROLLO
        'ferremas/templates/carrito_mongo_fixed.html',       # 🔄 DESARROLLO
        'carrito/templates/carrito/lista_productos.html',    # 🔄 BACKUP
    ],
    
    'TEMPLATES_POSIBLES_ACTIVAS': [
        'ferremas/templates/compra_exitosa.html',            # ❓ POSIBLE
        'ferremas/templates/compra_rechazada.html',          # ❓ POSIBLE
        'ferremas/templates/webpay_redirect.html',           # ❓ POSIBLE
    ]
}

def check_template_status(template_path):
    """Verifica el estado de unificación de un template"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar navbar unificado
        has_unified_navbar = all(element in content for element in [
            'nav class="navbar navbar-expand-lg',
            'navbar-brand',
            'nav-item dropdown',
            'fas fa-code me-1',
            'API',
            'dropdown-menu'
        ])
        
        # Verificar footer unificado
        has_unified_footer = all(element in content for element in [
            'footer class="bg-dark text-white py-5"',
            'col-md-4',
            'Tu ferretería de confianza desde 1995',
            'Contacto',
            '+56 2 1234 5678',
            'contacto@ferremas.cl',
            'Horarios'
        ])
        
        return {
            'exists': True,
            'navbar_unified': has_unified_navbar,
            'footer_unified': has_unified_footer,
            'fully_unified': has_unified_navbar and has_unified_footer
        }
    except FileNotFoundError:
        return {'exists': False, 'navbar_unified': False, 'footer_unified': False, 'fully_unified': False}
    except Exception as e:
        return {'exists': False, 'error': str(e), 'navbar_unified': False, 'footer_unified': False, 'fully_unified': False}

def main():
    print("🗺️  MAPEO COMPLETO DE TEMPLATES WEB - PROYECTO FERREMAS")
    print("=" * 80)
    
    for category, templates in TEMPLATES_BY_CATEGORY.items():
        print(f"\n📁 {category.replace('_', ' ')}")
        print("-" * 60)
        
        for template in templates:
            status = check_template_status(template)
            if status['exists']:
                unified_status = "✅ UNIFICADA" if status['fully_unified'] else "❌ PENDIENTE"
                navbar_status = "✅" if status['navbar_unified'] else "❌"
                footer_status = "✅" if status['footer_unified'] else "❌"
                
                print(f"   {unified_status} {template}")
                print(f"      🧭 Navbar: {navbar_status}  📧 Footer: {footer_status}")
            else:
                print(f"   ❌ NO ENCONTRADA {template}")
    
    print(f"\n{'=' * 80}")
    print("📋 RESUMEN DE URLs ACTIVAS:")
    print("-" * 40)
    for url, template in ACTIVE_URLS_TEMPLATES.items():
        print(f"   {url} → {template}")
    
    print(f"\n🎯 PRÓXIMOS PASOS:")
    print("   1. Verificar templates con ❌ PENDIENTE")
    print("   2. Confirmar qué templates de inventario están activas")
    print("   3. Limpiar templates de backup/desarrollo si no se usan")

if __name__ == "__main__":
    main()
