#!/usr/bin/env python3
"""
Script para identificar exactamente qué templates están siendo utilizados
por las URLs activas del proyecto Ferremas.
"""

import os
import re

def analizar_templates_activos():
    """Analiza las vistas para identificar qué templates se usan realmente"""
    
    # Templates identificados en las vistas activas
    templates_activos = {
        # Ferremas web_urls.py -> mongo_views.py
        'productos_venta.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'productos_venta_view',
            'url': '/ y /venta/',
            'descripcion': 'Página principal de productos'
        },
        'inventario_sucursales.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'inventario_sucursales_view',
            'url': '/inventario/',
            'descripcion': 'Gestión de inventario'
        },
        'crear_producto_form.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'crear_producto_form_view',
            'url': '/crear-producto/',
            'descripcion': 'Formulario para crear productos'
        },
        'actualizar_stock_form.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'actualizar_stock_form_view',
            'url': '/actualizar-stock/',
            'descripcion': 'Formulario para actualizar stock'
        },
        'carrito_mongo.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'ver_carrito_view',
            'url': '/carrito/',
            'descripcion': 'Vista del carrito de compras'
        },
        'compra_exitosa.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'compra_exitosa_view',
            'url': '/compra-exitosa/',
            'descripcion': 'Confirmación de compra exitosa'
        },
        'compra_rechazada.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'compra_rechazada_view',
            'url': '/compra-rechazada/',
            'descripcion': 'Notificación de compra rechazada'
        },
        
        # Carrito urls_mongo.py -> views_mongo.py
        'carrito/lista_productos_mongo.html': {
            'ubicacion': 'carrito/templates/',
            'vista': 'lista_productos_mongo',
            'url': '/carrito/productos/',
            'descripcion': 'Lista de productos para el carrito'
        },
        'pago_exitoso_mongo.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'webpay_respuesta_mongo',
            'url': '/carrito/webpay/respuesta/',
            'descripcion': 'Confirmación de pago exitoso'
        },
        'pago_fallido_mongo.html': {
            'ubicacion': 'ferremas/templates/',
            'vista': 'webpay_respuesta_mongo',
            'url': '/carrito/webpay/respuesta/',
            'descripcion': 'Notificación de pago fallido'
        }
    }
    
    print("=== TEMPLATES ACTIVOS IDENTIFICADOS ===")
    print(f"Total de templates activos: {len(templates_activos)}")
    print()
    
    # Verificar cuáles existen
    proyecto_path = r"c:\Users\the_j\OneDrive\Escritorio\prototipoApis\ProyectoAPIS\proyectapis"
    
    templates_existentes = []
    templates_faltantes = []
    
    for template, info in templates_activos.items():
        if template.startswith('carrito/'):
            # Template dentro de carrito/templates/
            template_path = os.path.join(proyecto_path, info['ubicacion'], template)
        else:
            # Template en ferremas/templates/
            template_path = os.path.join(proyecto_path, info['ubicacion'], template)
        
        if os.path.exists(template_path):
            templates_existentes.append((template, info, template_path))
        else:
            templates_faltantes.append((template, info, template_path))
    
    print("=== TEMPLATES EXISTENTES ===")
    for template, info, path in templates_existentes:
        print(f"✓ {template}")
        print(f"  URL: {info['url']}")
        print(f"  Vista: {info['vista']}")
        print(f"  Descripción: {info['descripcion']}")
        print(f"  Ruta: {path}")
        print()
    
    if templates_faltantes:
        print("=== TEMPLATES FALTANTES ===")
        for template, info, path in templates_faltantes:
            print(f"✗ {template}")
            print(f"  URL: {info['url']}")
            print(f"  Vista: {info['vista']}")
            print(f"  Descripción: {info['descripcion']}")
            print(f"  Ruta esperada: {path}")
            print()
    
    print("=== RESUMEN ===")
    print(f"Templates existentes: {len(templates_existentes)}")
    print(f"Templates faltantes: {len(templates_faltantes)}")
    
    # Verificar navbar y footer en templates existentes
    print("\n=== VERIFICACIÓN NAVBAR/FOOTER ===")
    for template, info, path in templates_existentes:
        verificar_navbar_footer(template, path)
    
    return templates_activos

def verificar_navbar_footer(template_name, template_path):
    """Verifica si un template tiene navbar y footer unificados"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar indicadores de navbar unificado
        navbar_presente = (
            'navbar-expand-lg' in content and
            'dropdown-menu' in content and
            'Inventario' in content and
            'Carrito' in content
        )
        
        # Buscar indicadores de footer unificado
        footer_presente = (
            'footer' in content and
            'bg-dark' in content and
            'text-white' in content and
            'py-5' in content and
            'Ferremas' in content and
            'Contacto' in content and
            'Horarios' in content
        )
        
        status_navbar = "✓" if navbar_presente else "✗"
        status_footer = "✓" if footer_presente else "✗"
        
        print(f"{status_navbar} Navbar | {status_footer} Footer | {template_name}")
        
        return navbar_presente, footer_presente
    except Exception as e:
        print(f"✗ Error | ✗ Error | {template_name} (Error: {str(e)})")
        return False, False

if __name__ == "__main__":
    analizar_templates_activos()
