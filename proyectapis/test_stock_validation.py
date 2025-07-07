#!/usr/bin/env python3
"""
Script para probar la validación de stock en el carrito
"""

import requests
import json
import sys
from pathlib import Path

SERVER_URL = "http://127.0.0.1:8000"

def test_stock_validation():
    """Probar la validación de stock"""
    print("📦 === PROBANDO VALIDACIÓN DE STOCK ===")
    
    try:
        # 1. Obtener productos disponibles
        products_response = requests.get(f"{SERVER_URL}/api/productos/venta/", timeout=10)
        if products_response.status_code == 200:
            products = products_response.json()
            if products:
                # Buscar un producto con stock limitado
                product_with_stock = None
                for product in products:
                    if product.get('stock_total', 0) > 0 and product.get('stock_total', 0) < 10:
                        product_with_stock = product
                        break
                
                if not product_with_stock:
                    product_with_stock = products[0]  # Usar el primero disponible
                
                product_id = product_with_stock['_id']
                product_name = product_with_stock['nombre']
                stock_total = product_with_stock.get('stock_total', 0)
                
                print(f"✅ Producto seleccionado: {product_name}")
                print(f"📊 Stock total: {stock_total}")
                
                # 2. Obtener CSRF token
                carrito_response = requests.get(f"{SERVER_URL}/carrito/", timeout=10)
                if carrito_response.status_code == 200:
                    html_content = carrito_response.text
                    import re
                    csrf_match = re.search(r'content="([^"]+)"[^>]*name="csrf-token"', html_content)
                    
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        print(f"🔑 CSRF Token obtenido")
                        
                        # 3. Agregar producto al carrito
                        add_response = requests.post(
                            f"{SERVER_URL}/carrito/agregar/{product_id}/",
                            json={"sucursal_id": None},
                            headers={
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrf_token,
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            timeout=10
                        )
                        
                        if add_response.status_code == 200:
                            add_result = add_response.json()
                            if add_result.get('success'):
                                print("✅ Producto agregado al carrito")
                                
                                # 4. Obtener items del carrito
                                carrito_response = requests.get(f"{SERVER_URL}/carrito/", timeout=10)
                                if carrito_response.status_code == 200:
                                    html_content = carrito_response.text
                                    
                                    # Buscar item ID en el HTML
                                    item_ids = re.findall(r'data-item-id="([^"]+)"', html_content)
                                    stock_values = re.findall(r'data-stock="([^"]+)"', html_content)
                                    
                                    if item_ids and stock_values:
                                        item_id = item_ids[0]
                                        max_stock = int(stock_values[0])
                                        
                                        print(f"🔍 Item ID: {item_id}")
                                        print(f"📦 Stock máximo: {max_stock}")
                                        
                                        # 5. Probar actualización dentro del límite
                                        test_quantity = min(max_stock, 2)
                                        print(f"\n🧪 Probando cantidad válida: {test_quantity}")
                                        
                                        update_response = requests.post(
                                            f"{SERVER_URL}/carrito/actualizar/{item_id}/",
                                            json={"cantidad": test_quantity},
                                            headers={
                                                'Content-Type': 'application/json',
                                                'X-CSRFToken': csrf_token,
                                                'X-Requested-With': 'XMLHttpRequest'
                                            },
                                            timeout=10
                                        )
                                        
                                        if update_response.status_code == 200:
                                            result = update_response.json()
                                            if result.get('success'):
                                                print("✅ Actualización válida exitosa")
                                            else:
                                                print(f"❌ Error en actualización válida: {result.get('error')}")
                                        else:
                                            print(f"❌ Error HTTP en actualización válida: {update_response.status_code}")
                                        
                                        # 6. Probar actualización fuera del límite
                                        invalid_quantity = max_stock + 5
                                        print(f"\n🧪 Probando cantidad inválida: {invalid_quantity} (máximo: {max_stock})")
                                        
                                        invalid_response = requests.post(
                                            f"{SERVER_URL}/carrito/actualizar/{item_id}/",
                                            json={"cantidad": invalid_quantity},
                                            headers={
                                                'Content-Type': 'application/json',
                                                'X-CSRFToken': csrf_token,
                                                'X-Requested-With': 'XMLHttpRequest'
                                            },
                                            timeout=10
                                        )
                                        
                                        if invalid_response.status_code == 400:
                                            result = invalid_response.json()
                                            if not result.get('success'):
                                                print(f"✅ Validación correcta: {result.get('error')}")
                                            else:
                                                print("❌ Error: Debería haber rechazado la cantidad excesiva")
                                        else:
                                            print(f"⚠️ Respuesta inesperada: {invalid_response.status_code}")
                                            try:
                                                result = invalid_response.json()
                                                print(f"   Resultado: {result}")
                                            except:
                                                print(f"   Texto: {invalid_response.text}")
                                        
                                        return True
                                    else:
                                        print("❌ No se encontraron items en el carrito")
                                else:
                                    print(f"❌ Error al obtener carrito actualizado: {carrito_response.status_code}")
                            else:
                                print(f"❌ Error al agregar producto: {add_result.get('error')}")
                        else:
                            print(f"❌ Error HTTP al agregar producto: {add_response.status_code}")
                    else:
                        print("❌ No se pudo obtener CSRF token")
                else:
                    print(f"❌ Error al cargar carrito: {carrito_response.status_code}")
            else:
                print("❌ No hay productos disponibles")
        else:
            print(f"❌ Error al obtener productos: {products_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
    
    return False

def main():
    """Función principal"""
    print("🧪 === PRUEBA DE VALIDACIÓN DE STOCK ===")
    
    if test_stock_validation():
        print("\n🎉 === VALIDACIÓN DE STOCK FUNCIONANDO ===")
    else:
        print("\n⚠️ === REVISAR VALIDACIÓN DE STOCK ===")
    
    print("\n📝 === INSTRUCCIONES PARA PRUEBA MANUAL ===")
    print("1. Ve a http://127.0.0.1:8000/productos/venta/")
    print("2. Agrega un producto al carrito")
    print("3. Ve a http://127.0.0.1:8000/carrito/")
    print("4. Intenta aumentar la cantidad más allá del stock disponible")
    print("5. Verifica que aparezca el mensaje de error")

if __name__ == "__main__":
    main()
