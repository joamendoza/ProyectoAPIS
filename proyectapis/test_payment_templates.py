#!/usr/bin/env python3
"""
Test para verificar la estructura de las plantillas de pago
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from django.test import Client
from django.template.loader import render_to_string

def test_payment_templates():
    """Test para verificar las plantillas de pago exitoso y fallido"""
    print("=== TEST: Plantillas de Pago ===")
    
    client = Client()
    
    # Datos de ejemplo para las plantillas
    boleta_data = {
        'codigo': 'BOL-20250706-001',
        'usuario_id_unico': 'USER-123456',
        'fecha': datetime.now(),
        'total': 89990,
        'items': [
            {
                'nombre': 'Taladro Percutor',
                'cantidad': 1,
                'precio': 89990
            }
        ]
    }
    
    # Test template pago exitoso
    try:
        print("\n--- Test Pago Exitoso ---")
        
        # Verificar que la plantilla se puede renderizar
        rendered = render_to_string('pago_exitoso_mongo.html', {
            'boleta': boleta_data,
            'sucursal': {'nombre': 'Sucursal Centro'}
        })
        
        # Verificar elementos clave
        required_elements = [
            'navbar',
            'hero-section',
            'main-content',
            'footer',
            'Compra Exitosa',
            'fas fa-check-circle',
            'boleta-section',
            'action-buttons'
        ]
        
        print(f"Plantilla renderizada: {len(rendered)} caracteres")
        
        for element in required_elements:
            if element in rendered:
                print(f"✓ Elemento '{element}' encontrado")
            else:
                print(f"✗ Elemento '{element}' faltante")
                
    except Exception as e:
        print(f"✗ Error renderizando pago exitoso: {e}")
    
    # Test template pago fallido
    try:
        print("\n--- Test Pago Fallido ---")
        
        # Verificar que la plantilla se puede renderizar
        rendered = render_to_string('pago_fallido_mongo.html', {
            'debug_info': {
                'error_code': 'PAYMENT_REJECTED',
                'error_message': 'Pago rechazado por el banco',
                'transaction_id': 'TXN-123456'
            }
        })
        
        # Verificar elementos clave
        required_elements = [
            'navbar',
            'hero-section',
            'main-content',
            'footer',
            'Pago Rechazado',
            'fas fa-times-circle',
            'troubleshoot-list',
            'action-buttons'
        ]
        
        print(f"Plantilla renderizada: {len(rendered)} caracteres")
        
        for element in required_elements:
            if element in rendered:
                print(f"✓ Elemento '{element}' encontrado")
            else:
                print(f"✗ Elemento '{element}' faltante")
                
    except Exception as e:
        print(f"✗ Error renderizando pago fallido: {e}")

def test_payment_urls():
    """Test para verificar que las URLs de pago funcionan"""
    print("\n=== TEST: URLs de Pago ===")
    
    client = Client()
    
    # URLs para probar
    urls = [
        '/compra-exitosa/',
        '/compra-rechazada/'
    ]
    
    for url in urls:
        try:
            response = client.get(url)
            print(f"URL {url}: Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"✓ {url} accesible")
            elif response.status_code == 404:
                print(f"⚠ {url} no encontrada (puede ser normal sin parámetros)")
            else:
                print(f"✗ {url} error {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error accediendo a {url}: {e}")

def test_template_consistency():
    """Test para verificar consistencia entre plantillas"""
    print("\n=== TEST: Consistencia de Plantillas ===")
    
    templates = [
        'pago_exitoso_mongo.html',
        'pago_fallido_mongo.html'
    ]
    
    common_elements = [
        'navbar navbar-expand-lg',
        'container',
        'hero-section',
        'main-content',
        'footer bg-dark',
        'bootstrap@5.1.3',
        'font-awesome/6.0.0'
    ]
    
    for template in templates:
        try:
            print(f"\n--- Verificando {template} ---")
            
            # Leer el contenido del archivo
            template_path = f'ferremas/templates/{template}'
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for element in common_elements:
                if element in content:
                    print(f"✓ {element}")
                else:
                    print(f"✗ {element} faltante")
                    
        except Exception as e:
            print(f"✗ Error leyendo {template}: {e}")

def main():
    """Función principal"""
    print("=== VERIFICACIÓN DE PLANTILLAS DE PAGO ===")
    print(f"Fecha: {datetime.now()}")
    print("=" * 60)
    
    test_payment_templates()
    test_payment_urls()
    test_template_consistency()
    
    print("\n" + "=" * 60)
    print("VERIFICACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
