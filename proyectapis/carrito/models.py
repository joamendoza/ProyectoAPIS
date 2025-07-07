from django.db import models
from inventario.models import Producto
from django.contrib.auth.models import User

class Boleta(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    usuario_id_unico = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"Boleta {self.codigo} - ${self.total}"

class DetalleBoleta(models.Model):
    boleta = models.ForeignKey(Boleta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    def subtotal(self):
        return self.precio * self.cantidad

class Carrito(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    usuario_id_unico = models.CharField(max_length=100, default='default')
    created_at = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        return self.producto.get_precio_actual() * self.cantidad

    def __str__(self):
        return f"Carrito: {self.producto.nombre} x{self.cantidad}"

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
