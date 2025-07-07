"""
Debug de la vista de inventario - Verificar datos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from ferremas.mongo_models import SucursalMongo, ProductoMongo

def debug_inventario_view():
    """Debug de la vista de inventario"""
    print("=== DEBUG VISTA DE INVENTARIO ===")
    
    try:
        # 1. Verificar sucursales
        print("\n1. Verificando sucursales...")
        sucursales = SucursalMongo.objects.all()
        print(f"Total de sucursales: {len(sucursales)}")
        
        for sucursal in sucursales:
            print(f"  - Sucursal ID: {sucursal._id}")
            print(f"    Nombre: {sucursal.nombre}")
            print(f"    Dirección: {sucursal.calle} {sucursal.numeracion}, {sucursal.comuna}")
        
        # 2. Verificar productos
        print("\n2. Verificando productos...")
        productos = ProductoMongo.objects.all()
        print(f"Total de productos: {len(productos)}")
        
        for producto in productos[:3]:  # Solo mostrar primeros 3
            print(f"  - Producto ID: {producto._id}")
            print(f"    Nombre: {producto.nombre}")
            print(f"    Inventario: {len(producto.inventario)} sucursales")
            for inv in producto.inventario:
                print(f"      Sucursal {inv.sucursal}: {inv.cantidad} unidades")
        
        # 3. Simular la lógica de la vista
        print("\n3. Simulando lógica de la vista...")
        sucursales_data = []
        
        for sucursal in sucursales:
            productos_sucursal = []
            productos = ProductoMongo.objects.all()
            
            for producto in productos:
                for inv in producto.inventario:
                    if inv.sucursal == sucursal._id:
                        productos_sucursal.append({
                            'id': producto._id,
                            'nombre': producto.nombre,
                            'marca': producto.marca,
                            'modelo': producto.modelo,
                            'categoria': producto.categoria or 'Sin categoría',
                            'precio_actual': float(producto.get_precio_actual()),
                            'cantidad': inv.cantidad,
                            'ultima_actualizacion': inv.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if inv.ultima_actualizacion else 'N/A'
                        })
                        break
            
            sucursales_data.append({
                'id': sucursal._id,
                'nombre': sucursal.nombre,
                'direccion': f"{sucursal.calle} {sucursal.numeracion}, {sucursal.comuna}, {sucursal.region}",
                'total_productos': len(productos_sucursal),
                'productos': productos_sucursal
            })
        
        print(f"Datos procesados para {len(sucursales_data)} sucursales:")
        for sucursal_data in sucursales_data:
            print(f"  - {sucursal_data['nombre']}: {sucursal_data['total_productos']} productos")
        
        # 4. Verificar si hay datos para mostrar
        if not sucursales_data:
            print("\n❌ No hay datos de sucursales para mostrar")
            return False
        
        total_productos = sum(s['total_productos'] for s in sucursales_data)
        if total_productos == 0:
            print("\n❌ No hay productos en inventario para mostrar")
            return False
        
        print(f"\n✅ Datos disponibles: {len(sucursales_data)} sucursales con {total_productos} productos totales")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_inventario_view()
