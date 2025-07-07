#!/usr/bin/env python
"""
Debug carrito - verificar usuario IDs
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from ferremas.mongo_models import CarritoMongo

def debug_carrito():
    """Debug de usuarios en carrito"""
    
    print("🔍 DEBUG CARRITO")
    print("-" * 40)
    
    # Obtener todos los items del carrito
    carrito_items = CarritoMongo.objects.all()
    
    print(f"Total items en carrito: {len(carrito_items)}")
    print()
    
    if carrito_items:
        print("Items en carrito:")
        for item in carrito_items:
            print(f"- Usuario: {item.usuario_id_unico}")
            print(f"  Producto: {item.producto_id} ({item.producto_nombre})")
            print(f"  Cantidad: {item.cantidad}")
            print(f"  Subtotal: {item.subtotal()}")
            print()
    else:
        print("No hay items en el carrito")
        
    print("-" * 40)

if __name__ == "__main__":
    debug_carrito()
