#!/usr/bin/env python3
"""
Script para identificar y limpiar archivos sin uso en el proyecto Ferremas
"""

import os
import shutil
from pathlib import Path

# Archivos que son claramente backups, duplicados o no utilizados
FILES_TO_CLEAN = {
    'TEMPLATES_BACKUP': [
        'ferremas/templates/productos_venta_clean.html',
        'ferremas/templates/productos_venta_backup.html',
        'ferremas/templates/carrito_backup.html',
        'ferremas/templates/carrito_nuevo.html',
        'ferremas/templates/carrito_mongo_nuevo.html',
        'ferremas/templates/carrito_mongo_fixed.html',
        'carrito/templates/carrito/lista_productos.html',
        'inventario/templates/inventario/producto_form.backup',
        'inventario/templates/inventario/producto_list.backup',
        'inventario/templates/inventario/producto_confirm_delete.backup',
    ],
    
    'CARRITO_BACKUP_FILES': [
        'carrito/templates/carrito/carrito_mongo.backup',
        'carrito/templates/carrito/lista_productos.backup',
        'carrito/templates/carrito/pago_fallido.backup',
    ],
    
    'SCRIPTS_TEMPORALES': [
        'test_navbar_unification.py',
        'test_footer_unification.py',
        'mapeo_templates_completo.py',
    ],
    
    'ARCHIVOS_DEBUG': [
        'debug_carrito_usuario.py',
        'debug_carrito_usuarios.py',
        'test_carrito_cookies.py',
        'test_carrito_simple.py',
        'test_carrito.html',
        'test_debug_paso_paso.py',
        'test_ferremas_api.py',
        'test_flujo_completo_carrito.py',
        'test_sistema_completo.py',
        'test_user_id_consistency.py',
        'setup_demo_cart.py',
    ]
}

# Archivos de configuración y logs que pueden limpiarse
LOGS_AND_CONFIG_FILES = [
    'carrito_debug.log',
    'debug.log',
    'moneda_cache.json',
]

# Documentación que puede estar desactualizada
OLD_DOCS = [
    'CARRITO_MEJORAS_COMPLETADAS.md',
    'FOOTER_UNIFICADO_COMPLETO.md',
    'FORMULARIOS_POST.md',
    'INTEGRACION_COMPLETA.md',
    'LAYOUT_CARRITO_SOLUCION_FINAL.md',
    'MEJORAS_CARRITO_FINAL.md',
    'MEJORAS_CARRITO.md',
    'NAVEGACION_ARREGLADA.md',
    'NAVEGACION_FOOTER_ESTANDARIZADOS.md',
    'README_ARREGLADO.md',
    'SISTEMA_CARRITO_MEJORADO.md',
    'SISTEMA_CONFIRMACION_COMPRA.md',
    'SOLUCION_LAYOUT_CARRITO.md',
    'TIPOGRAFIA_UNIFICADA_FERREMAS.md',
    'UNIFICACION_COMPLETA_VISTAS_GESTION.md',
    'UNIFICACION_ESTILOS_FERREMAS.md',
]

def safe_remove(file_path):
    """Elimina un archivo de forma segura"""
    try:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
                return f"✅ Eliminado: {file_path}"
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                return f"✅ Eliminado directorio: {file_path}"
        else:
            return f"⚠️  No encontrado: {file_path}"
    except Exception as e:
        return f"❌ Error eliminando {file_path}: {str(e)}"

def backup_important_files():
    """Crea backup de archivos importantes antes de limpiar"""
    backup_dir = "backup_limpieza"
    os.makedirs(backup_dir, exist_ok=True)
    
    important_files = [
        'ferremas/templates/carrito.html',  # Mantener como alternativa
        'test_navbar_unification.py',      # Script útil
        'test_footer_unification.py',      # Script útil
    ]
    
    for file_path in important_files:
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, f"{backup_dir}/{os.path.basename(file_path)}")
                print(f"📦 Respaldado: {file_path}")
            except Exception as e:
                print(f"❌ Error respaldando {file_path}: {e}")

def main():
    print("🧹 LIMPIEZA DE ARCHIVOS SIN USO - PROYECTO FERREMAS")
    print("=" * 60)
    
    # Crear backup de archivos importantes
    print("\n📦 Creando backup de archivos importantes...")
    backup_important_files()
    
    removed_count = 0
    
    for category, files in FILES_TO_CLEAN.items():
        print(f"\n🗂️  {category.replace('_', ' ')}")
        print("-" * 40)
        
        for file_path in files:
            result = safe_remove(file_path)
            print(f"   {result}")
            if "✅ Eliminado" in result:
                removed_count += 1
    
    print(f"\n🗑️  LOGS Y ARCHIVOS DE CONFIGURACIÓN")
    print("-" * 40)
    for file_path in LOGS_AND_CONFIG_FILES:
        result = safe_remove(file_path)
        print(f"   {result}")
        if "✅ Eliminado" in result:
            removed_count += 1
    
    print(f"\n📚 DOCUMENTACIÓN OBSOLETA")
    print("-" * 40)
    for file_path in OLD_DOCS:
        result = safe_remove(file_path)
        print(f"   {result}")
        if "✅ Eliminado" in result:
            removed_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"🎯 RESUMEN DE LIMPIEZA:")
    print(f"   Total de archivos eliminados: {removed_count}")
    print(f"   Backup creado en: backup_limpieza/")
    print(f"\n✨ ¡Proyecto limpio y organizado!")

if __name__ == "__main__":
    main()
