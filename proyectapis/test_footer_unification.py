#!/usr/bin/env python3
"""
Test script to verify footer unification across templates
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
    'ferremas/templates/carrito_mongo.html',
    'carrito/templates/carrito/carrito_mongo.html',
]

# Expected unified footer structure elements
FOOTER_ELEMENTS = [
    'footer class="bg-dark text-white py-5"',
    'col-md-4',
    'fas fa-tools me-2',
    'Ferremas',
    'Tu ferretería de confianza desde 1995',
    'Contacto',
    'fas fa-phone me-2',
    '+56 2 1234 5678',
    'fas fa-envelope me-2',
    'contacto@ferremas.cl',
    'Horarios',
    'Lunes a Viernes: 8:00 - 19:00',
    'Sábados: 9:00 - 17:00',
]

def check_template_footer(template_path):
    """Check if a template has the unified footer structure"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_elements = []
        for element in FOOTER_ELEMENTS:
            if element not in content:
                missing_elements.append(element)
        
        return missing_elements
    except FileNotFoundError:
        return [f"Template file not found: {template_path}"]
    except Exception as e:
        return [f"Error reading template: {str(e)}"]

def main():
    print("🔍 Checking footer unification across templates...")
    print("=" * 60)
    
    all_passed = True
    
    for template in TEMPLATES_TO_CHECK:
        print(f"\n📄 Checking: {template}")
        missing = check_template_footer(template)
        
        if missing:
            print(f"   ❌ Missing footer elements: {len(missing)}")
            for element in missing[:3]:  # Show first 3 missing elements
                print(f"      - {element}")
            if len(missing) > 3:
                print(f"      ... and {len(missing) - 3} more")
            all_passed = False
        else:
            print(f"   ✅ All footer elements present")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All templates have unified footer structure!")
    else:
        print("⚠️  Some templates are missing footer elements.")
    
    return all_passed

if __name__ == "__main__":
    main()
