from django.contrib import admin
from .models import Boleta, DetalleBoleta, Carrito, Administrador


@admin.register(Boleta)
class BoletaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'usuario_id_unico', 'fecha', 'total']
    list_filter = ['fecha']
    search_fields = ['codigo', 'usuario_id_unico']
    readonly_fields = ['fecha']
    date_hierarchy = 'fecha'


@admin.register(DetalleBoleta)
class DetalleBoletaAdmin(admin.ModelAdmin):
    list_display = ['boleta', 'producto', 'cantidad', 'precio', 'subtotal']
    list_filter = ['boleta__fecha']
    search_fields = ['boleta__codigo', 'producto__nombre']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('boleta', 'producto')


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad', 'usuario_id_unico', 'subtotal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['producto__nombre', 'usuario_id_unico']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('producto')


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'created_at']
    list_filter = ['created_at']
    search_fields = ['usuario__username', 'usuario__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información del Administrador', {
            'fields': ('usuario', 'password_admin')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')
