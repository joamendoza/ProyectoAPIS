#!/usr/bin/env python
"""
Debug paso a paso del carrito
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from ferremas.mongo_models import CarritoMongo
from ferremas.mongo_views import CarritoManager

def debug_step_by_step():
    """Debug paso a paso"""
    
    print("🔍 DEBUG PASO A PASO")
    print("-" * 40)
    
    # Simular el usuario ID que se usa en las pruebas
    usuario_id = "fallback_576515811a05"
    print(f"Usuario ID usado: {usuario_id}")
    
    # Verificar items en mongo directamente
    print("\n1. Items en MongoDB:")
    items_directos = CarritoMongo.objects.filter(usuario_id_unico=usuario_id)
    print(f"   Items encontrados: {len(items_directos)}")
    for item in items_directos:
        print(f"   - {item.producto_nombre} (x{item.cantidad})")
    
    # Usar CarritoManager para calcular totales
    print("\n2. Usando CarritoManager:")
    totales = CarritoManager.calcular_totales_carrito(usuario_id)
    print(f"   Total items: {totales['total_items']}")
    print(f"   Total precio: {totales['total_precio']}")
    print(f"   Carrito items: {len(totales['carrito_items'])}")
    
    if totales['carrito_items']:
        print("   Items calculados:")
        for item in totales['carrito_items']:
            print(f"   - {item.producto_nombre} (x{item.cantidad})")
    
    # Verificar todos los usuarios
    print("\n3. Todos los usuarios en carrito:")
    all_items = CarritoMongo.objects.all()
    usuarios = set(item.usuario_id_unico for item in all_items)
    for usuario in usuarios:
        count = CarritoMongo.objects.filter(usuario_id_unico=usuario).count()
        print(f"   - Usuario: {usuario} ({count} items)")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    debug_step_by_step()
