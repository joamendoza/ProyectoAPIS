from django.contrib import admin
from inventario.models import Producto, PrecioProducto, InventarioProducto, Sucursal
from .models import Administrador

# Los modelos ya están registrados en sus respectivas apps
# Este archivo se mantiene para compatibilidad pero no registra modelos
# para evitar duplicación en el admin

# Si necesitas personalizar la administración de Ferremas específicamente,
# puedes desregistrar los modelos de las otras apps y registrarlos aquí
# con configuraciones específicas

# Ejemplo de personalización (comentado para evitar duplicación):
"""
# Desregistrar de otras apps si es necesario
admin.site.unregister(Producto)

@admin.register(Producto)
class ProductoFerremasAdmin(admin.ModelAdmin):
    list_display = ['id_producto', 'marca', 'modelo', 'nombre', 'created_at']
    list_filter = ['marca', 'created_at']
    search_fields = ['id_producto', 'marca', 'modelo', 'nombre']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información del Producto', {
            'fields': ('id_producto', 'marca', 'modelo', 'nombre', 'categoria', 'descripcion')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
"""
