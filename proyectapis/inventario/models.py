from django.db import models
from datetime import datetime

class Producto(models.Model):
    """Modelo unificado siguiendo el formato de Ferremas API"""
    CATEGORIAS = [
        ('herramientas', 'Herramientas'),
        ('materiales', 'Materiales de Construcción'),
        ('seguridad', 'Equipos de Seguridad'),
        ('tornillos', 'Tornillos y Anclajes'),
        ('adhesivos', 'Fijaciones y Adhesivos'),
        ('medicion', 'Equipos de Medición'),
    ]

    # Campos siguiendo formato Ferremas
    id_producto = models.CharField(max_length=50, unique=True, primary_key=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.nombre}"

    def get_precio_actual(self):
        """Obtiene el precio más reciente del producto"""
        precio = self.precios.first()
        return precio.valor if precio else 0

    def get_stock_total(self):
        """Obtiene el stock total sumando todos los inventarios"""
        return sum(inv.cantidad for inv in self.inventarios.all())


class PrecioProducto(models.Model):
    """Modelo para historial de precios siguiendo formato Ferremas"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='precios')
    fecha = models.DateTimeField(default=datetime.now)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Precio Producto"
        verbose_name_plural = "Precios Productos"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.producto.nombre} - ${self.valor} ({self.fecha.strftime('%Y-%m-%d')})"


class Sucursal(models.Model):
    """Modelo para sucursales siguiendo formato Ferremas"""
    nombre = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    calle = models.CharField(max_length=200)
    numeracion = models.CharField(max_length=20)
    comuna = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

    def __str__(self):
        return f"{self.nombre} - {self.comuna}"


class InventarioProducto(models.Model):
    """Modelo para inventario por sucursal siguiendo formato Ferremas"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='inventarios')
    cantidad = models.PositiveIntegerField()
    ultima_actualizacion = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inventario Producto"
        verbose_name_plural = "Inventarios Productos"
        unique_together = ['producto', 'sucursal']

    def __str__(self):
        return f"{self.producto.nombre} en {self.sucursal.nombre} - {self.cantidad} unidades"

    @property
    def stock(self):
        """Alias para compatibilidad con código existente"""
        return self.cantidad
