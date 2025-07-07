from django.contrib import admin
from .models import Producto, PrecioProducto, InventarioProducto, Sucursal


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['id_producto', 'marca', 'modelo', 'nombre', 'categoria', 'get_precio_actual', 'get_stock_total', 'created_at']
    list_filter = ['marca', 'categoria', 'created_at']
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
    
    def get_precio_actual(self, obj):
        return f"${obj.get_precio_actual()}"
    get_precio_actual.short_description = "Precio Actual"
    
    def get_stock_total(self, obj):
        return obj.get_stock_total()
    get_stock_total.short_description = "Stock Total"


@admin.register(PrecioProducto)
class PrecioProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'valor', 'fecha', 'created_at']
    list_filter = ['fecha', 'created_at']
    search_fields = ['producto__nombre', 'producto__marca']
    readonly_fields = ['created_at']
    date_hierarchy = 'fecha'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('producto')


@admin.register(InventarioProducto)
class InventarioProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'sucursal', 'cantidad', 'ultima_actualizacion', 'created_at']
    list_filter = ['sucursal', 'ultima_actualizacion', 'created_at']
    search_fields = ['producto__nombre', 'producto__marca', 'sucursal__nombre']
    readonly_fields = ['created_at']
    date_hierarchy = 'ultima_actualizacion'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('producto', 'sucursal')


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'comuna', 'region', 'created_at']
    list_filter = ['region', 'comuna', 'created_at']
    search_fields = ['nombre', 'comuna', 'region']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'password')
        }),
        ('Dirección', {
            'fields': ('calle', 'numeracion', 'comuna', 'region')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
