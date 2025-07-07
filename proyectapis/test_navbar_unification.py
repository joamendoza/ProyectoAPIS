#!/usr/bin/env python3
"""
Test script to verify navbar unification across templates
"""

import os
import re

# Templates to check
TEMPLATES_TO_CHECK = [
    'ferremas/templates/productos_venta.html',
    'ferremas/templates/pago_exitoso_mongo.html',
    'ferremas/templates/pago_fallido_mongo.html',
    'ferremas/templates/inventario_sucursales.html',
    'ferremas/templates/crear_producto_form.html',
    'ferremas/templates/actualizar_stock_form.html',
    'ferremas/templates/carrito.html',
    'carrito/templates/carrito/carrito_mongo.html',
]

# Expected navbar structure elements
NAVBAR_ELEMENTS = [
    'nav class="navbar navbar-expand-lg',
    'navbar-brand',
    'nav-item dropdown',
    'fas fa-code me-1',
    'API',
    'dropdown-menu',
    'dropdown-header',
    'Productos',
    'Sucursales',
    'Consultas',
    'Operaciones',
    'Listar Productos',
    'Productos para Venta',
    'Listar Sucursales',
    'Inventario Centro',
    'Inventario Maipú',
    'Inventario Las Condes',
    'Producto en Sucursales',
    'Crear Producto',
    'Actualizar Stock',
]

def check_template_navbar(template_path):
    """Check if a template has the unified navbar structure"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_elements = []
        for element in NAVBAR_ELEMENTS:
            if element not in content:
                missing_elements.append(element)
        
        return missing_elements
    except FileNotFoundError:
        return [f"Template file not found: {template_path}"]
    except Exception as e:
        return [f"Error reading template: {str(e)}"]

def main():
    print("🔍 Checking navbar unification across templates...")
    print("=" * 60)
    
    all_passed = True
    
    for template in TEMPLATES_TO_CHECK:
        print(f"\n📄 Checking: {template}")
        missing = check_template_navbar(template)
        
        if missing:
            print(f"   ❌ Missing elements: {len(missing)}")
            for element in missing[:5]:  # Show first 5 missing elements
                print(f"      - {element}")
            if len(missing) > 5:
                print(f"      ... and {len(missing) - 5} more")
            all_passed = False
        else:
            print(f"   ✅ All navbar elements present")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All templates have unified navbar structure!")
    else:
        print("⚠️  Some templates are missing navbar elements.")
    
    return all_passed

if __name__ == "__main__":
    main()
