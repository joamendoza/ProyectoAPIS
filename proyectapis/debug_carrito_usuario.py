#!/usr/bin/env python
"""
Script de debug para diagnosticar el problema del carrito vacío
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from ferremas.mongo_models import *
from ferremas.mongo_views import CarritoManager
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser
import json

def debug_carrito_usuario():
    """Función principal de debug"""
    print("=== DEBUG CARRITO USUARIO ===")
    
    # Crear request factory
    factory = RequestFactory()
    
    # Simular request de agregar producto
    request_agregar = factory.post('/carrito/agregar/', {
        'producto_id': '678bb93b05db9daf16c22a6b',
        'cantidad': 2,
        'sucursal_id': 1
    })
    
    # Añadir sesión al request
    middleware = SessionMiddleware(lambda x: x)
    middleware.process_request(request_agregar)
    request_agregar.session.save()
    request_agregar.user = AnonymousUser()
    
    print("\n1. SIMULANDO AGREGAR PRODUCTO AL CARRITO")
    print(f"Request POST data: {request_agregar.POST}")
    
    # Obtener usuario ID
    usuario_id_agregar = CarritoManager.obtener_usuario_id(request_agregar)
    print(f"Usuario ID obtenido: {usuario_id_agregar}")
    print(f"Session key: {request_agregar.session.session_key}")
    print(f"Session data: {dict(request_agregar.session)}")
    
    # Verificar si existen productos con este usuario
    carrito_items = CarritoMongo.objects.filter(usuario_id_unico=usuario_id_agregar)
    print(f"Items en carrito con este usuario: {carrito_items.count()}")
    
    # Simular request de ver carrito
    request_ver = factory.get('/carrito/')
    
    # Crear nueva sesión (simular nueva request)
    middleware.process_request(request_ver)
    request_ver.session.save()
    request_ver.user = AnonymousUser()
    
    print("\n2. SIMULANDO VER CARRITO (NUEVA REQUEST)")
    usuario_id_ver = CarritoManager.obtener_usuario_id(request_ver)
    print(f"Usuario ID obtenido: {usuario_id_ver}")
    print(f"Session key: {request_ver.session.session_key}")
    print(f"Session data: {dict(request_ver.session)}")
    
    # Verificar si son el mismo usuario
    print(f"\n3. COMPARACIÓN DE USUARIOS")
    print(f"Usuario agregar: {usuario_id_agregar}")
    print(f"Usuario ver: {usuario_id_ver}")
    print(f"Son iguales: {usuario_id_agregar == usuario_id_ver}")
    
    # Simular misma sesión
    print("\n4. SIMULANDO MISMA SESIÓN")
    request_ver_misma_sesion = factory.get('/carrito/')
    request_ver_misma_sesion.session = request_agregar.session
    request_ver_misma_sesion.user = AnonymousUser()
    
    usuario_id_misma_sesion = CarritoManager.obtener_usuario_id(request_ver_misma_sesion)
    print(f"Usuario ID con misma sesión: {usuario_id_misma_sesion}")
    print(f"Son iguales: {usuario_id_agregar == usuario_id_misma_sesion}")
    
    # Verificar todos los carritos existentes
    print("\n5. TODOS LOS CARRITOS EN BASE DE DATOS")
    todos_carritos = CarritoMongo.objects.all()
    for i, item in enumerate(todos_carritos):
        print(f"Item {i+1}: usuario={item.usuario_id_unico}, producto={item.producto_nombre}, cantidad={item.cantidad}")
    
    # Probar calcular totales
    print("\n6. CALCULANDO TOTALES")
    totales = CarritoManager.calcular_totales_carrito(usuario_id_agregar)
    print(f"Totales para usuario {usuario_id_agregar}:")
    print(f"  Total items: {totales['total_items']}")
    print(f"  Total precio: {totales['total_precio']}")
    print(f"  Items: {len(totales['carrito_items'])}")
    
    # Test con diferentes usuarios
    print("\n7. TEST CON DIFERENTES USUARIOS")
    usuarios_test = [
        "invitado123456",
        "user-1", 
        "fallback_test123",
        "emergency_123456"
    ]
    
    for usuario in usuarios_test:
        items = CarritoMongo.objects.filter(usuario_id_unico=usuario)
        print(f"Usuario {usuario}: {items.count()} items")
        if items.count() > 0:
            for item in items:
                print(f"  - {item.producto_nombre} (cantidad: {item.cantidad})")

if __name__ == "__main__":
    debug_carrito_usuario()
