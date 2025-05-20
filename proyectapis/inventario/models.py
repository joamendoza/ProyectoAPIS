from django.db import models

class Producto(models.Model):
    CATEGORIAS = [
        ('herramientas', 'Herramientas'),
        ('materiales', 'Materiales de Construcción'),
        ('seguridad', 'Equipos de Seguridad'),
        ('tornillos', 'Tornillos y Anclajes'),
        ('adhesivos', 'Fijaciones y Adhesivos'),
        ('medicion', 'Equipos de Medición'),
    ]

    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre
