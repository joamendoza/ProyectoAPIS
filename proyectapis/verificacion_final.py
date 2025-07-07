#!/usr/bin/env python3
"""
Verificación Final - Proyecto Ferremas
Verifica que todos los templates activos tengan navbar y footer unificado
"""

import os
import glob

def verificar_unificacion():
    """Verifica que todos los templates tengan navbar y footer unificado"""
    
    # Patrones para buscar navbar y footer unificado
    navbar_pattern = 'navbar-brand.*Ferremas'
    footer_pattern = 'contacto@ferremas.cl'
    
    # Templates activos principales
    templates_activos = [
        'ferremas/templates/productos_venta.html',
        'ferremas/templates/pago_exitoso_mongo.html',
        'ferremas/templates/pago_fallido_mongo.html',
        'ferremas/templates/inventario_sucursales.html',
        'ferremas/templates/crear_producto_form.html',
        'ferremas/templates/actualizar_stock_form.html',
        'ferremas/templates/carrito_mongo.html',
        'ferremas/templates/carrito.html',
        'carrito/templates/carrito/carrito_mongo.html',
        'carrito/templates/carrito/lista_productos_mongo.html',
        'inventario/templates/inventario/producto_list.html',
        'inventario/templates/inventario/producto_form.html',
        'inventario/templates/inventario/producto_confirm_delete.html'
    ]
    
    print("🔍 VERIFICACIÓN FINAL - UNIFICACIÓN NAVBAR Y FOOTER")
    print("=" * 60)
    
    resultados = {
        'con_navbar': [],
        'con_footer': [],
        'sin_navbar': [],
        'sin_footer': [],
        'no_encontrado': []
    }
    
    for template in templates_activos:
        if os.path.exists(template):
            try:
                with open(template, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                tiene_navbar = 'navbar-brand' in contenido and 'Ferremas' in contenido
                tiene_footer = 'contacto@ferremas.cl' in contenido
                
                if tiene_navbar:
                    resultados['con_navbar'].append(template)
                else:
                    resultados['sin_navbar'].append(template)
                
                if tiene_footer:
                    resultados['con_footer'].append(template)
                else:
                    resultados['sin_footer'].append(template)
                    
            except Exception as e:
                print(f"❌ Error leyendo {template}: {e}")
        else:
            resultados['no_encontrado'].append(template)
    
    # Mostrar resultados
    print(f"✅ Templates con navbar unificado: {len(resultados['con_navbar'])}")
    for template in resultados['con_navbar']:
        print(f"   ✓ {template}")
    
    print(f"\n✅ Templates con footer unificado: {len(resultados['con_footer'])}")
    for template in resultados['con_footer']:
        print(f"   ✓ {template}")
    
    if resultados['sin_navbar']:
        print(f"\n❌ Templates SIN navbar unificado: {len(resultados['sin_navbar'])}")
        for template in resultados['sin_navbar']:
            print(f"   ❌ {template}")
    
    if resultados['sin_footer']:
        print(f"\n❌ Templates SIN footer unificado: {len(resultados['sin_footer'])}")
        for template in resultados['sin_footer']:
            print(f"   ❌ {template}")
    
    if resultados['no_encontrado']:
        print(f"\n⚠️  Templates no encontrados: {len(resultados['no_encontrado'])}")
        for template in resultados['no_encontrado']:
            print(f"   ⚠️  {template}")
    
    print("\n" + "=" * 60)
    
    # Calcular estadísticas
    total_templates = len(templates_activos) - len(resultados['no_encontrado'])
    templates_completos = len(set(resultados['con_navbar']) & set(resultados['con_footer']))
    
    print(f"📊 ESTADÍSTICAS FINALES:")
    print(f"   Templates activos: {total_templates}")
    print(f"   Templates con navbar y footer: {templates_completos}")
    print(f"   Porcentaje de completitud: {(templates_completos/total_templates)*100:.1f}%")
    
    if templates_completos == total_templates:
        print("🎉 ¡UNIFICACIÓN COMPLETADA AL 100%!")
    else:
        print("⚠️  Algunos templates necesitan ajustes")
    
    return resultados

def verificar_estructura_proyecto():
    """Verifica la estructura final del proyecto"""
    print("\n🏗️  VERIFICACIÓN ESTRUCTURA DEL PROYECTO")
    print("=" * 60)
    
    # Verificar que no queden archivos backup
    backup_patterns = ['**/*.backup', '**/*_backup.*', '**/*_clean.*']
    archivos_backup = []
    
    for pattern in backup_patterns:
        archivos_backup.extend(glob.glob(pattern, recursive=True))
    
    if archivos_backup:
        print(f"⚠️  Archivos backup encontrados: {len(archivos_backup)}")
        for archivo in archivos_backup:
            print(f"   ⚠️  {archivo}")
    else:
        print("✅ No se encontraron archivos backup")
    
    # Verificar templates por app
    apps = ['ferremas', 'carrito', 'inventario']
    for app in apps:
        template_dir = f"{app}/templates"
        if os.path.exists(template_dir):
            templates = glob.glob(f"{template_dir}/**/*.html", recursive=True)
            print(f"📁 {app}: {len(templates)} templates")
            for template in templates:
                print(f"   ✓ {template}")
        else:
            print(f"❌ {app}: directorio de templates no encontrado")

if __name__ == "__main__":
    verificar_unificacion()
    verificar_estructura_proyecto()
