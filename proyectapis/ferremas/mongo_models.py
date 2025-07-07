"""
Modelos de MongoDB para Ferremas API usando MongoEngine
"""
from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime
from typing import List, Optional

class Precio(EmbeddedDocument):
    """Modelo para precios históricos"""
    fecha = fields.DateTimeField(default=datetime.now)
    valor = fields.DecimalField(precision=2)

class Inventario(EmbeddedDocument):
    """Modelo para inventario por sucursal"""
    sucursal = fields.IntField(required=True)
    nombre_sucursal = fields.StringField()
    cantidad = fields.IntField(default=0)
    ultima_actualizacion = fields.DateTimeField(default=datetime.now)

class ProductoMongo(Document):
    """Modelo de producto en MongoDB"""
    _id = fields.StringField(primary_key=True)
    marca = fields.StringField(required=True, max_length=100)
    modelo = fields.StringField(required=True, max_length=100)
    nombre = fields.StringField(required=True, max_length=200)
    categoria = fields.StringField(max_length=50)
    descripcion = fields.StringField()
    precio = fields.ListField(fields.EmbeddedDocumentField(Precio))
    inventario = fields.ListField(fields.EmbeddedDocumentField(Inventario))
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        'collection': 'productos',
        'indexes': [
            'marca',
            'categoria'
        ]
    }

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.nombre}"

    def get_precio_actual(self):
        """Obtiene el precio más reciente"""
        if self.precio:
            return max(self.precio, key=lambda p: p.fecha).valor
        return 0

    def get_stock_total(self):
        """Obtiene el stock total"""
        return sum(inv.cantidad for inv in self.inventario)

    def get_stock_sucursal(self, sucursal_id):
        """Obtiene el stock de una sucursal específica"""
        for inv in self.inventario:
            if inv.sucursal == sucursal_id:
                return inv.cantidad
        return 0

    @property
    def id(self):
        """Devuelve el _id sin guión bajo para usar en templates"""
        return self._id

class SucursalMongo(Document):
    """Modelo de sucursal en MongoDB"""
    _id = fields.IntField(primary_key=True)
    nombre = fields.StringField(required=True, max_length=100)
    password = fields.StringField(required=True, max_length=100)
    calle = fields.StringField(max_length=200)
    numeracion = fields.StringField(max_length=20)
    comuna = fields.StringField(max_length=100)
    region = fields.StringField(max_length=100)
    telefono = fields.StringField(max_length=20, default="No disponible")
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        'collection': 'sucursales'
    }

    def __str__(self):
        return f"{self.nombre} - {self.comuna}"
    
    @property
    def direccion(self):
        """Propiedad para obtener la dirección completa"""
        if self.calle and self.numeracion:
            return f"{self.calle} {self.numeracion}, {self.comuna}"
        elif self.calle:
            return f"{self.calle}, {self.comuna}"
        else:
            return self.comuna or "Dirección no disponible"

class AdministradorMongo(Document):
    """Modelo de administrador en MongoDB"""
    nombre = fields.StringField(required=True, max_length=100)
    email = fields.EmailField()
    password = fields.StringField(required=True, max_length=100)
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        'collection': 'administradores'
    }

    def __str__(self):
        return self.nombre


class DetalleBoletaMongo(EmbeddedDocument):
    """Modelo de detalle de boleta embebido en MongoDB"""
    producto_id = fields.StringField(required=True)
    producto_nombre = fields.StringField(required=True)
    producto_marca = fields.StringField(required=True)
    producto_modelo = fields.StringField(required=True)
    cantidad = fields.IntField(required=True, min_value=1)
    precio_unitario = fields.DecimalField(precision=2)  # Nuevo campo
    precio = fields.DecimalField(precision=2)  # Campo legacy para compatibilidad
    sucursal_id = fields.IntField(required=True)
    sucursal_nombre = fields.StringField(required=True)

    def subtotal(self):
        """Calcula el subtotal del detalle"""
        # Usar precio_unitario si existe, si no usar precio (compatibilidad)
        precio = self.precio_unitario if self.precio_unitario else self.precio
        return float(precio) * self.cantidad if precio else 0
    
    @property
    def precio_final(self):
        """Obtener el precio final (para compatibilidad)"""
        return self.precio_unitario if self.precio_unitario else self.precio
    
    @property
    def producto(self):
        """Propiedad para obtener el producto como objeto"""
        class ProductoTemp:
            def __init__(self, id, nombre, marca, modelo):
                self._id = id
                self.nombre = nombre
                self.marca = marca
                self.modelo = modelo
                self.codigo = id
        
        return ProductoTemp(self.producto_id, self.producto_nombre, self.producto_marca, self.producto_modelo)

class DetalleBoletaMongoDoc(Document):
    """Modelo de detalle de boleta como documento independiente en MongoDB"""
    boleta_codigo = fields.StringField(required=True)
    producto_id = fields.StringField(required=True)
    producto_nombre = fields.StringField(required=True)
    producto_marca = fields.StringField(required=True)
    producto_modelo = fields.StringField(required=True)
    cantidad = fields.IntField(required=True, min_value=1)
    precio_unitario = fields.DecimalField(required=True, precision=2)
    sucursal_id = fields.IntField(required=True)
    sucursal_nombre = fields.StringField(required=True)

    meta = {
        'collection': 'detalles_boleta',
        'indexes': [
            'boleta_codigo',
            'producto_id'
        ]
    }

    def subtotal(self):
        """Calcula el subtotal del detalle"""
        return float(self.precio_unitario) * self.cantidad
    
    @property
    def producto(self):
        """Propiedad para obtener el producto como objeto"""
        class ProductoTemp:
            def __init__(self, id, nombre, marca, modelo):
                self._id = id
                self.nombre = nombre
                self.marca = marca
                self.modelo = modelo
                self.codigo = id
        
        return ProductoTemp(self.producto_id, self.producto_nombre, self.producto_marca, self.producto_modelo)

class BoletaMongo(Document):
    """Modelo de boleta en MongoDB"""
    codigo = fields.StringField(required=True, unique=True, max_length=50)  # Aumentado de 20 a 50
    usuario_id_unico = fields.StringField(required=True, max_length=100)
    fecha = fields.DateTimeField(default=datetime.now)
    total = fields.DecimalField(required=True, precision=2)
    estado = fields.StringField(default='completada', choices=['pendiente', 'completada', 'cancelada'])
    metodo_pago = fields.StringField(default='webpay', choices=['webpay', 'efectivo', 'transferencia'])
    sucursal_id = fields.IntField(required=True)
    sucursal_nombre = fields.StringField(required=True)
    detalles = fields.ListField(fields.EmbeddedDocumentField(DetalleBoletaMongo))
    
    # Campos adicionales para Webpay
    webpay_token = fields.StringField(max_length=64)
    webpay_buy_order = fields.StringField(max_length=50)
    webpay_session_id = fields.StringField(max_length=100)
    webpay_amount = fields.DecimalField(precision=2)
    webpay_authorization_code = fields.StringField(max_length=20)

    meta = {
        'collection': 'boletas',
        'indexes': [
            'codigo',
            'usuario_id_unico',
            'fecha',
            'webpay_buy_order'
        ]
    }

    def __str__(self):
        return f"Boleta {self.codigo} - ${self.total}"
    
    @property
    def subtotal(self):
        """Calcula el subtotal (total sin IVA)"""
        return float(self.total) / 1.19
    
    @property
    def iva(self):
        """Calcula el IVA (19%)"""
        return float(self.total) - self.subtotal
    
    @property
    def sucursal(self):
        """Propiedad para obtener la sucursal como objeto"""
        try:
            return SucursalMongo.objects.get(_id=self.sucursal_id)
        except SucursalMongo.DoesNotExist:
            # Crear objeto temporal si no se encuentra la sucursal
            class SucursalTemp:
                def __init__(self, id, nombre):
                    self.id = id
                    self.nombre = nombre
                    self.direccion = "Dirección no disponible"
                    self.telefono = "Teléfono no disponible"
            
            return SucursalTemp(self.sucursal_id, self.sucursal_nombre)

class CarritoMongo(Document):
    """Modelo de carrito de compras en MongoDB"""
    producto_id = fields.StringField(required=True)
    producto_nombre = fields.StringField(required=True)
    producto_marca = fields.StringField(required=True)
    producto_modelo = fields.StringField(required=True)
    precio_unitario = fields.DecimalField(required=True, precision=2)
    cantidad = fields.IntField(default=1, min_value=1)
    usuario_id_unico = fields.StringField(required=True, max_length=100)
    sucursal_id = fields.IntField(required=True)
    sucursal_nombre = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        'collection': 'carrito',
        'indexes': [
            'usuario_id_unico',
            ('usuario_id_unico', 'producto_id')
        ]
    }

    def subtotal(self):
        """Calcula el subtotal del item"""
        return float(self.precio_unitario) * self.cantidad

    def __str__(self):
        return f"Carrito: {self.producto_nombre} x{self.cantidad}"
