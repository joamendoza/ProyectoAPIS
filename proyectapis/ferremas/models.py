from django.db import models
from django.contrib.auth.models import User
from inventario.models import Producto, PrecioProducto, InventarioProducto, Sucursal

# Los modelos ahora están centralizados en las apps inventario y ferremas
# para mantener la compatibilidad y evitar duplicación

class Administrador(models.Model):
    """Modelo para administradores generales siguiendo formato Ferremas"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    password_admin = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

    def __str__(self):
        return f"Admin: {self.usuario.username}"

# Alias para compatibilidad con código existente
ProductoFerremas = Producto

# Re-exportar los modelos para mantener las importaciones existentes
__all__ = [
    'ProductoFerremas',
    'PrecioProducto', 
    'InventarioProducto',
    'Sucursal',
    'Administrador'
]
