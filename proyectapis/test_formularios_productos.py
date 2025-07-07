#!/usr/bin/env python3
"""
Test script para verificar la funcionalidad de los formularios de productos
"""

import os
import sys
import django
import requests
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from ferremas.mongo_models import ProductoMongo, Inventario
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware

def test_crear_producto_form():
    """Test para verificar el formulario de crear producto"""
    print("=== TEST: Formulario Crear Producto ===")
    
    client = Client()
    
    try:
        # Test GET request
        response = client.get('/crear-producto/')
        print(f"GET Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Formulario accesible")
            
            # Verificar que contiene los elementos esperados
            content = response.content.decode()
            required_elements = [
                'form',
                'name="producto_id"',
                'name="marca"',
                'name="modelo"',
                'name="nombre"',
                'name="categoria"',
                'name="descripcion"',
                'name="precio"',
                'name="cantidad"',
                'name="sucursal_id"',
                'btn-primary'
            ]
            
            for element in required_elements:
                if element in content:
                    print(f"✓ Elemento '{element}' encontrado")
                else:
                    print(f"✗ Elemento '{element}' faltante")
                    
        else:
            print(f"✗ Error accediendo al formulario: {response.status_code}")
            
        # Test POST request
        print("\n--- Test POST ---")
        form_data = {
            'producto_id': 'PRODUCTO-TEST',
            'marca': 'Bosch',
            'modelo': 'GSB 13 RE',
            'nombre': 'Taladro Percutor Test',
            'categoria': 'herramientas',
            'descripcion': 'Descripción del producto de prueba',
            'precio': '89990',
            'cantidad': '15',
            'sucursal_id': '1',
            'password': 'test123',
            'admin_password': 'admin123'
        }
        
        response = client.post('/crear-producto/', form_data)
        print(f"POST Status: {response.status_code}")
        
        if response.status_code == 302:
            print("✓ Redirección exitosa después de crear producto")
        elif response.status_code == 200:
            print("✓ Formulario procesado (verificar mensajes)")
        else:
            print(f"✗ Error en POST: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error en test: {e}")

def test_actualizar_stock_form():
    """Test para verificar el formulario de actualizar stock"""
    print("\n=== TEST: Formulario Actualizar Stock ===")
    
    client = Client()
    
    try:
        # Test GET request
        response = client.get('/actualizar-stock/')
        print(f"GET Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Formulario accesible")
            
            # Verificar que contiene los elementos esperados
            content = response.content.decode()
            required_elements = [
                'form',
                'name="producto_id"',
                'name="sucursal_id"',
                'name="cantidad"',
                'name="password"',
                'btn-primary'
            ]
            
            for element in required_elements:
                if element in content:
                    print(f"✓ Elemento '{element}' encontrado")
                else:
                    print(f"✗ Elemento '{element}' faltante")
                    
        else:
            print(f"✗ Error accediendo al formulario: {response.status_code}")
            
        # Test POST request (solo si hay productos)
        print("\n--- Test POST ---")
        
        # Primero verificar si hay productos
        productos = ProductoMongo.objects.all()
        if productos:
            producto_id = str(productos[0].id)
            
            form_data = {
                'producto_id': producto_id,
                'sucursal_id': '1',
                'cantidad': '10',
                'password': 'test123'
            }
            
            response = client.post('/actualizar-stock/', form_data)
            print(f"POST Status: {response.status_code}")
            
            if response.status_code == 302:
                print("✓ Redirección exitosa después de actualizar stock")
            elif response.status_code == 200:
                print("✓ Formulario procesado (verificar mensajes)")
            else:
                print(f"✗ Error en POST: {response.status_code}")
        else:
            print("⚠ No hay productos para probar actualización de stock")
            
    except Exception as e:
        print(f"✗ Error en test: {e}")

def test_navegacion_formularios():
    """Test para verificar la navegación entre formularios"""
    print("\n=== TEST: Navegación entre formularios ===")
    
    client = Client()
    
    try:
        # Test navegación desde home
        response = client.get('/')
        print(f"Home Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode()
            
            # Verificar enlaces a formularios
            links = [
                '/crear-producto/',
                '/actualizar-stock/',
                '/inventario/'
            ]
            
            for link in links:
                if link in content:
                    print(f"✓ Enlace '{link}' encontrado en home")
                else:
                    print(f"✗ Enlace '{link}' faltante en home")
                    
        # Test navegación inversa (desde formularios a home)
        forms = [
            '/crear-producto/',
            '/actualizar-stock/'
        ]
        
        for form_url in forms:
            response = client.get(form_url)
            if response.status_code == 200:
                content = response.content.decode()
                if 'href="/"' in content or 'href="/ferremas/"' in content:
                    print(f"✓ Navegación desde {form_url} a home disponible")
                else:
                    print(f"✗ Navegación desde {form_url} a home faltante")
                    
    except Exception as e:
        print(f"✗ Error en test navegación: {e}")

def test_validaciones_formularios():
    """Test para verificar validaciones en formularios"""
    print("\n=== TEST: Validaciones de formularios ===")
    
    client = Client()
    
    try:
        # Test validación crear producto - campos vacíos
        print("\n--- Test validación crear producto ---")
        response = client.post('/crear-producto/', {})
        print(f"POST vacío Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Formulario maneja campos vacíos")
        
        # Test validación actualizar stock - campos vacíos
        print("\n--- Test validación actualizar stock ---")
        response = client.post('/actualizar-stock/', {})
        print(f"POST vacío Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Formulario maneja campos vacíos")
            
        # Test validación actualizar stock - producto inexistente
        form_data = {
            'producto_id': '507f1f77bcf86cd799439011',  # ID inexistente
            'sucursal_id': '1',
            'cantidad': '10',
            'password': 'test123'
        }
        
        response = client.post('/actualizar-stock/', form_data)
        print(f"POST producto inexistente Status: {response.status_code}")
        
    except Exception as e:
        print(f"✗ Error en test validaciones: {e}")

def test_consistencia_datos():
    """Test para verificar consistencia de datos"""
    print("\n=== TEST: Consistencia de datos ===")
    
    try:
        # Verificar productos en MongoDB
        productos_count = ProductoMongo.objects.count()
        print(f"Productos en MongoDB: {productos_count}")
        
        # Verificar inventario en MongoDB - como está embebido en productos
        inventario_count = 0
        for producto in ProductoMongo.objects.all():
            inventario_count += len(producto.inventario)
        print(f"Registros de inventario: {inventario_count}")
        
        # Verificar relación productos-inventario
        productos_con_inventario = 0
        for producto in ProductoMongo.objects.all():
            if producto.inventario:
                productos_con_inventario += 1
                
        print(f"Productos con inventario: {productos_con_inventario}/{productos_count}")
        
        if productos_count > 0:
            print("✓ Hay productos en el sistema")
        else:
            print("⚠ No hay productos en el sistema")
            
    except Exception as e:
        print(f"✗ Error en test consistencia: {e}")

def main():
    """Función principal para ejecutar todos los tests"""
    print("=== VERIFICACIÓN COMPLETA DE FORMULARIOS FERREMAS ===")
    print(f"Fecha: {datetime.now()}")
    print("=" * 60)
    
    test_crear_producto_form()
    test_actualizar_stock_form()
    test_navegacion_formularios()
    test_validaciones_formularios()
    test_consistencia_datos()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETADOS")
    print("=" * 60)

if __name__ == "__main__":
    main()
