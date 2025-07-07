"""
Debug script to check the structure of boletas in MongoDB
"""
import os
import sys
import django

# Setup Django
sys.path.append('C:\\Users\\the_j\\OneDrive\\Escritorio\\prototipoApis\\ProyectoAPIS\\proyectapis')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectapis.settings')
django.setup()

from ferremas.mongo_config import configure_mongoengine
from ferremas.mongo_models import BoletaMongo

def debug_boletas():
    """Debug boletas structure"""
    print("🔍 DEBUGGING BOLETAS STRUCTURE")
    print("=" * 50)
    
    try:
        # Configure MongoDB
        configure_mongoengine()
        
        # Get some boletas
        boletas = BoletaMongo.objects().limit(3)
        
        print(f"Found {boletas.count()} boletas")
        
        for i, boleta in enumerate(boletas):
            print(f"\n📋 BOLETA {i+1}: {boleta.codigo}")
            print(f"   Total: {boleta.total}")
            print(f"   Fecha: {boleta.fecha}")
            print(f"   Detalles count: {len(boleta.detalles)}")
            
            if boleta.detalles:
                print(f"   First detail type: {type(boleta.detalles[0])}")
                detail = boleta.detalles[0]
                print(f"   Available fields: {dir(detail)}")
                
                # Try to access each field
                try:
                    print(f"   producto_id: {detail.producto_id}")
                except Exception as e:
                    print(f"   ❌ Error accessing producto_id: {e}")
                
                try:
                    print(f"   producto_nombre: {detail.producto_nombre}")
                except Exception as e:
                    print(f"   ❌ Error accessing producto_nombre: {e}")
                
                try:
                    print(f"   precio_unitario: {detail.precio_unitario}")
                except Exception as e:
                    print(f"   ❌ Error accessing precio_unitario: {e}")
                
                try:
                    print(f"   cantidad: {detail.cantidad}")
                except Exception as e:
                    print(f"   ❌ Error accessing cantidad: {e}")
                
                # Check if it has a 'precio' field instead of 'precio_unitario'
                if hasattr(detail, 'precio'):
                    print(f"   ⚠️ Found 'precio' field: {detail.precio}")
                
                # Show the raw data
                try:
                    print(f"   Raw data: {detail._data}")
                except:
                    print("   Cannot access _data")
            else:
                print("   No detalles found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_boletas()
