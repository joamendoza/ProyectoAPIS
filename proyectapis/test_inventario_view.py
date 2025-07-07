"""
Test de la vista de inventario corregida
"""
import requests

def test_inventario_view():
    """Probar que la vista de inventario funciona correctamente"""
    print("=== TEST DE LA VISTA DE INVENTARIO ===")
    
    try:
        # Realizar solicitud a la vista de inventario
        response = requests.get("http://localhost:8000/inventario/")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ La vista de inventario responde correctamente")
            
            # Verificar que el contenido HTML contiene los elementos esperados
            content = response.text
            
            # Verificar elementos clave
            checks = [
                ('<title>Ferremas - Inventario por Sucursales</title>', 'Título correcto'),
                ('<h1 class="display-4 fw-bold">', 'Encabezado principal'),
                ('id="inventarioGrid"', 'Contenedor del inventario'),
                ('id="loadingState"', 'Estado de carga'),
                ('id="errorState"', 'Estado de error'),
                ('const sucursalesData =', 'Datos JavaScript'),
                ('displayInventario()', 'Función para mostrar inventario'),
                ('navbar', 'Barra de navegación'),
                ('footer', 'Pie de página')
            ]
            
            for check, description in checks:
                if check in content:
                    print(f"✅ {description}: OK")
                else:
                    print(f"❌ {description}: FALTANTE")
            
            # Verificar que ya no está en blanco
            if len(content.strip()) > 1000:  # Debe tener contenido sustancial
                print("✅ La página tiene contenido sustancial")
            else:
                print("❌ La página parece estar vacía")
            
            # Verificar que no hay errores de template
            if "TemplateSyntaxError" not in content and "Error" not in content:
                print("✅ No hay errores de template visibles")
            else:
                print("❌ Posibles errores de template detectados")
                
            return True
        else:
            print(f"❌ Error en la vista: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar la vista: {e}")
        return False

if __name__ == "__main__":
    if test_inventario_view():
        print("\n🎉 ¡La vista de inventario ha sido corregida exitosamente!")
    else:
        print("\n❌ La vista de inventario aún tiene problemas")
