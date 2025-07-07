#!/usr/bin/env python3
"""
Script para monitorear los logs del servidor mientras se prueba el frontend
"""
import os
import sys
import time
import json
from pathlib import Path

# Configurar path para Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')

import django
django.setup()

from carrito.models import CarritoItem
from ferremas.models import Producto

def monitor_cart_changes():
    """Monitorear cambios en el carrito"""
    
    print("🔍 MONITOREANDO CAMBIOS EN EL CARRITO")
    print("="*50)
    print("Presiona Ctrl+C para detener el monitoreo")
    print("="*50)
    
    last_count = 0
    last_items = []
    
    try:
        while True:
            # Obtener items actuales del carrito
            current_items = list(CarritoItem.objects.all())
            current_count = len(current_items)
            
            # Verificar si hay cambios
            if current_count != last_count:
                print(f"\n🔄 CAMBIO DETECTADO: {last_count} → {current_count} items")
                
                if current_count > last_count:
                    # Nuevo item agregado
                    new_items = [item for item in current_items if item not in last_items]
                    for item in new_items:
                        print(f"➕ PRODUCTO AGREGADO:")
                        print(f"   🏷️  ID: {item.producto_id}")
                        print(f"   📦 Cantidad: {item.cantidad}")
                        print(f"   🏪 Sucursal: {item.sucursal_id}")
                        print(f"   👤 Usuario: {item.user_id}")
                        print(f"   📅 Fecha: {item.fecha_agregado}")
                        
                        # Obtener información del producto
                        try:
                            producto = Producto.objects.get(pk=item.producto_id)
                            print(f"   📝 Nombre: {producto.nombre}")
                            print(f"   💰 Precio: ${producto.precio_actual}")
                        except Producto.DoesNotExist:
                            print(f"   ❌ Producto no encontrado en base de datos")
                        
                        print()
                
                elif current_count < last_count:
                    # Item eliminado
                    print(f"➖ PRODUCTO ELIMINADO DEL CARRITO")
                
                last_count = current_count
                last_items = current_items.copy()
            
            time.sleep(2)  # Verificar cada 2 segundos
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoreo detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en el monitoreo: {e}")

def show_current_cart_state():
    """Mostrar estado actual del carrito"""
    
    print("\n📊 ESTADO ACTUAL DEL CARRITO")
    print("="*40)
    
    items = CarritoItem.objects.all()
    
    if not items:
        print("🛒 El carrito está vacío")
        return
    
    print(f"📦 Total de items: {len(items)}")
    print()
    
    for i, item in enumerate(items, 1):
        print(f"{i}. Producto: {item.producto_id}")
        print(f"   📦 Cantidad: {item.cantidad}")
        print(f"   🏪 Sucursal: {item.sucursal_id}")
        print(f"   👤 Usuario: {item.user_id}")
        print(f"   📅 Agregado: {item.fecha_agregado}")
        print()

def clear_cart():
    """Limpiar el carrito"""
    
    print("🧹 LIMPIANDO CARRITO...")
    
    count = CarritoItem.objects.count()
    CarritoItem.objects.all().delete()
    
    print(f"✅ Se eliminaron {count} items del carrito")

def main():
    """Función principal"""
    
    print("🛒 === MONITOR DE CARRITO ===")
    print("Herramienta para monitorear el carrito durante las pruebas")
    print()
    
    while True:
        print("Opciones:")
        print("1. Mostrar estado actual del carrito")
        print("2. Limpiar carrito")
        print("3. Monitorear cambios en tiempo real")
        print("4. Salir")
        print()
        
        choice = input("Selecciona una opción (1-4): ").strip()
        
        if choice == "1":
            show_current_cart_state()
        elif choice == "2":
            clear_cart()
        elif choice == "3":
            monitor_cart_changes()
        elif choice == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida")
        
        print()

if __name__ == "__main__":
    main()
