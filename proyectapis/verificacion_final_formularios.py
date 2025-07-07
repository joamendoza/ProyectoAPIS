#!/usr/bin/env python3
"""
Verificación final de funcionalidad de formularios
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from ferremas.mongo_models import ProductoMongo
from django.test import Client

def test_crear_producto_funcional():
    """Test funcional para crear un producto real"""
    print("=== TEST FUNCIONAL: Crear Producto ===")
    
    client = Client()
    
    # Datos de prueba
    producto_data = {
        'producto_id': f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'marca': 'Test Brand',
        'modelo': 'Test Model',
        'nombre': 'Producto de Prueba Funcional',
        'categoria': 'herramientas',
        'descripcion': 'Producto creado durante pruebas funcionales',
        'precio': '25990',
        'cantidad': '8',
        'sucursal_id': '1',
        'password': 'ferremas123',
        'admin_password': 'admin123'
    }
    
    # Contar productos antes
    productos_antes = ProductoMongo.objects.count()
    print(f"Productos antes: {productos_antes}")
    
    try:
        # Intentar crear el producto
        response = client.post('/crear-producto/', producto_data)
        
        # Verificar respuesta
        if response.status_code == 200:
            print("✓ Formulario procesado correctamente")
            
            # Verificar si se creó el producto
            productos_despues = ProductoMongo.objects.count()
            print(f"Productos después: {productos_despues}")
            
            if productos_despues > productos_antes:
                print("✓ Producto creado exitosamente")
                
                # Buscar el producto creado
                producto_creado = ProductoMongo.objects.filter(
                    nombre=producto_data['nombre']
                ).first()
                
                if producto_creado:
                    print(f"✓ Producto encontrado: {producto_creado.nombre}")
                    print(f"  - Marca: {producto_creado.marca}")
                    print(f"  - Modelo: {producto_creado.modelo}")
                    print(f"  - Precio: ${producto_creado.get_precio_actual()}")
                    print(f"  - Stock total: {producto_creado.get_stock_total()}")
                else:
                    print("⚠ Producto no encontrado en base de datos")
            else:
                print("⚠ No se detectó aumento en la cantidad de productos")
                
        elif response.status_code == 302:
            print("✓ Redirección exitosa (probablemente producto creado)")
        else:
            print(f"✗ Error en la creación: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error durante la prueba: {e}")

def test_actualizar_stock_funcional():
    """Test funcional para actualizar stock de un producto existente"""
    print("\n=== TEST FUNCIONAL: Actualizar Stock ===")
    
    client = Client()
    
    # Obtener un producto existente
    producto = ProductoMongo.objects.first()
    if not producto:
        print("✗ No hay productos para probar actualización de stock")
        return
    
    print(f"Producto seleccionado: {producto.nombre}")
    stock_anterior = producto.get_stock_total()
    print(f"Stock anterior: {stock_anterior}")
    
    # Datos de prueba
    stock_data = {
        'producto_id': str(producto.id),
        'sucursal_id': '1',
        'cantidad': '50',  # Nueva cantidad
        'password': 'ferremas123'
    }
    
    try:
        # Intentar actualizar stock
        response = client.post('/actualizar-stock/', stock_data)
        
        if response.status_code == 200:
            print("✓ Formulario procesado correctamente")
            
            # Recargar el producto para verificar cambios
            producto.reload()
            stock_nuevo = producto.get_stock_total()
            print(f"Stock nuevo: {stock_nuevo}")
            
            if stock_nuevo != stock_anterior:
                print("✓ Stock actualizado exitosamente")
            else:
                print("⚠ No se detectaron cambios en el stock")
                
        elif response.status_code == 302:
            print("✓ Redirección exitosa (probablemente stock actualizado)")
        else:
            print(f"✗ Error en la actualización: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error durante la prueba: {e}")

def test_navegacion_completa():
    """Test de navegación completa entre todas las páginas"""
    print("\n=== TEST FUNCIONAL: Navegación Completa ===")
    
    client = Client()
    
    paginas = [
        ('/', 'Página Principal'),
        ('/venta/', 'Productos en Venta'),
        ('/crear-producto/', 'Crear Producto'),
        ('/actualizar-stock/', 'Actualizar Stock'),
        ('/inventario/', 'Inventario por Sucursales'),
        ('/carrito/', 'Carrito de Compras')
    ]
    
    for url, nombre in paginas:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✓ {nombre} accesible")
            else:
                print(f"✗ {nombre} error {response.status_code}")
        except Exception as e:
            print(f"✗ {nombre} error: {e}")

def mostrar_estadisticas():
    """Mostrar estadísticas actuales del sistema"""
    print("\n=== ESTADÍSTICAS DEL SISTEMA ===")
    
    try:
        # Productos
        productos = ProductoMongo.objects.all()
        print(f"Total de productos: {productos.count()}")
        
        # Categorías
        categorias = set()
        stock_total = 0
        
        for producto in productos:
            if producto.categoria:
                categorias.add(producto.categoria)
            stock_total += producto.get_stock_total()
        
        print(f"Categorías únicas: {len(categorias)}")
        print(f"Stock total en sistema: {stock_total}")
        
        # Productos por categoría
        if categorias:
            print("\nProductos por categoría:")
            for categoria in sorted(categorias):
                count = productos.filter(categoria=categoria).count()
                print(f"  - {categoria}: {count} productos")
        
        # Productos con mayor stock
        print("\nTop 5 productos con mayor stock:")
        productos_ordenados = sorted(productos, key=lambda p: p.get_stock_total(), reverse=True)
        for i, producto in enumerate(productos_ordenados[:5]):
            print(f"  {i+1}. {producto.nombre} - Stock: {producto.get_stock_total()}")
            
    except Exception as e:
        print(f"✗ Error obteniendo estadísticas: {e}")

def main():
    """Función principal"""
    print("=== VERIFICACIÓN FINAL DE FUNCIONALIDAD ===")
    print(f"Fecha: {datetime.now()}")
    print("=" * 60)
    
    # Tests funcionales
    test_crear_producto_funcional()
    test_actualizar_stock_funcional()
    test_navegacion_completa()
    
    # Estadísticas
    mostrar_estadisticas()
    
    print("\n" + "=" * 60)
    print("VERIFICACIÓN FINAL COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
