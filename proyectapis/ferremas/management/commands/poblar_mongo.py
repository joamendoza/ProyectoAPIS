"""
Comando para poblar MongoDB con datos de ejemplo de Ferremas
"""
from django.core.management.base import BaseCommand
from ferremas.mongo_config import configure_mongoengine
from ferremas.mongo_models import ProductoMongo, SucursalMongo, AdministradorMongo, Precio, Inventario
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Pobla MongoDB con datos de ejemplo para Ferremas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando poblado de MongoDB para Ferremas...'))
        
        # Configurar MongoEngine
        configure_mongoengine()
        
        # Limpiar datos existentes
        self.limpiar_datos()
        
        # Crear sucursales
        self.crear_sucursales()
        
        # Crear administrador
        self.crear_administrador()
        
        # Crear productos
        self.crear_productos()
        
        self.stdout.write(self.style.SUCCESS('✅ ¡Poblado de MongoDB completado exitosamente!'))
        self.mostrar_credenciales()

    def limpiar_datos(self):
        """Limpia datos existentes"""
        try:
            ProductoMongo.objects.all().delete()
            SucursalMongo.objects.all().delete()
            AdministradorMongo.objects.all().delete()
            self.stdout.write(self.style.WARNING('🗑️  Datos existentes eliminados'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error limpiando datos: {e}'))

    def crear_sucursales(self):
        """Crea las sucursales de ejemplo"""
        sucursales_data = [
            {
                '_id': 1,
                'nombre': 'Ferremas Centro',
                'password': 'centro123',
                'calle': 'Av. Libertador Bernardo O\'Higgins',
                'numeracion': '1234',
                'comuna': 'Santiago',
                'region': 'Metropolitana'
            },
            {
                '_id': 2,
                'nombre': 'Ferremas Maipú',
                'password': 'maipu123',
                'calle': 'Av. Pajaritos',
                'numeracion': '5678',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
            {
                '_id': 3,
                'nombre': 'Ferremas Las Condes',
                'password': 'condes123',
                'calle': 'Av. Apoquindo',
                'numeracion': '9012',
                'comuna': 'Las Condes',
                'region': 'Metropolitana'
            }
        ]
        
        for sucursal_data in sucursales_data:
            sucursal = SucursalMongo(**sucursal_data)
            sucursal.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Sucursal "{sucursal.nombre}" creada exitosamente'))

    def crear_administrador(self):
        """Crea el administrador del sistema"""
        admin = AdministradorMongo(
            nombre='Administrador Ferremas',
            email='admin@ferremas.com',
            password='admin123'
        )
        admin.save()
        self.stdout.write(self.style.SUCCESS('✅ Administrador creado exitosamente'))

    def crear_productos(self):
        """Crea productos de ejemplo"""
        productos_data = [
            {
                '_id': 'TALADRO-001',
                'marca': 'Bosch',
                'modelo': 'GSB 13 RE',
                'nombre': 'Taladro Percutor 13mm 600W',
                'categoria': 'herramientas',
                'descripcion': 'Taladro percutor profesional con motor de 600W, mandril de 13mm y función de percusión. Ideal para trabajos en mampostería y metal.',
                'precio_base': 89990,
                'inventario_base': [15, 20, 12]
            },
            {
                '_id': 'SIERRA-002',
                'marca': 'DeWalt',
                'modelo': 'DWE575',
                'nombre': 'Sierra Circular 7-1/4" 1600W',
                'categoria': 'herramientas',
                'descripcion': 'Sierra circular de 7-1/4" con motor de 1600W, base de magnesio y sistema de extracción de polvo. Perfecta para cortes precisos.',
                'precio_base': 125990,
                'inventario_base': [8, 15, 10]
            },
            {
                '_id': 'TORNILLO-003',
                'marca': 'Hilti',
                'modelo': 'X-U 6x60',
                'nombre': 'Tornillo Autoperforante 6x60mm (Caja 100 unidades)',
                'categoria': 'tornillos',
                'descripcion': 'Tornillos autoperforantes de alta resistencia para fijación en metal. Cabeza hexagonal con arandela integrada.',
                'precio_base': 12990,
                'inventario_base': [50, 75, 45]
            },
            {
                '_id': 'PINTURA-004',
                'marca': 'Sherwin Williams',
                'modelo': 'ProClassic',
                'nombre': 'Pintura Látex Blanco Semi-Mate 1 Galón',
                'categoria': 'materiales',
                'descripcion': 'Pintura látex de alta calidad con acabado semi-mate, excelente cobertura y resistencia. Ideal para interiores.',
                'precio_base': 25990,
                'inventario_base': [30, 25, 35]
            },
            {
                '_id': 'CABLE-005',
                'marca': 'Procobre',
                'modelo': 'NYA-12',
                'nombre': 'Cable Eléctrico NYA 12 AWG (Metro)',
                'categoria': 'materiales',
                'descripcion': 'Cable eléctrico NYA de 12 AWG para instalaciones domiciliarias. Conductor de cobre con aislación PVC.',
                'precio_base': 890,
                'inventario_base': [200, 180, 220]
            },
            {
                '_id': 'CASCO-006',
                'marca': '3M',
                'modelo': 'H-701R',
                'nombre': 'Casco de Seguridad Industrial',
                'categoria': 'seguridad',
                'descripcion': 'Casco de seguridad industrial con suspensión de 4 puntos, barboquejo y alta resistencia al impacto.',
                'precio_base': 8990,
                'inventario_base': [25, 30, 20]
            },
            {
                '_id': 'MARTILLO-007',
                'marca': 'Stanley',
                'modelo': 'STHT51512',
                'nombre': 'Martillo de Carpintero 16 oz',
                'categoria': 'herramientas',
                'descripcion': 'Martillo de carpintero con cabeza de acero forjado y mango de fibra de vidrio. Diseño ergonómico para mayor comodidad.',
                'precio_base': 15990,
                'inventario_base': [40, 35, 45]
            },
            {
                '_id': 'BROCA-008',
                'marca': 'Makita',
                'modelo': 'D-17369',
                'nombre': 'Set de Brocas para Metal HSS 13 piezas',
                'categoria': 'herramientas',
                'descripcion': 'Set de brocas HSS para metal de 1.5mm a 6.5mm. Incluye estuche metálico para almacenamiento.',
                'precio_base': 22990,
                'inventario_base': [18, 22, 15]
            }
        ]
        
        sucursales = SucursalMongo.objects.all()
        
        for producto_data in productos_data:
            # Crear precios con variaciones
            precio_base = producto_data['precio_base']
            precios = [
                Precio(
                    fecha=datetime.now(),
                    valor=precio_base
                )
            ]
            
            # Crear inventario para cada sucursal
            inventario = []
            for i, sucursal in enumerate(sucursales):
                cantidad = producto_data['inventario_base'][i]
                inventario.append(Inventario(
                    sucursal=sucursal._id,
                    nombre_sucursal=sucursal.nombre,
                    cantidad=cantidad,
                    ultima_actualizacion=datetime.now()
                ))
            
            # Crear producto
            producto = ProductoMongo(
                _id=producto_data['_id'],
                marca=producto_data['marca'],
                modelo=producto_data['modelo'],
                nombre=producto_data['nombre'],
                categoria=producto_data['categoria'],
                descripcion=producto_data['descripcion'],
                precio=precios,
                inventario=inventario
            )
            producto.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Producto "{producto.nombre}" creado exitosamente'))

    def mostrar_credenciales(self):
        """Muestra las credenciales del sistema"""
        self.stdout.write(self.style.HTTP_INFO('\n🔑 Credenciales del Sistema:'))
        self.stdout.write(self.style.HTTP_INFO('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
        self.stdout.write(self.style.HTTP_INFO('📋 Administrador API:'))
        self.stdout.write(self.style.HTTP_INFO('  - Password: admin123'))
        self.stdout.write(self.style.HTTP_INFO('\n🏪 Credenciales de Sucursales:'))
        self.stdout.write(self.style.HTTP_INFO('  - Sucursal 1 (Centro): centro123'))
        self.stdout.write(self.style.HTTP_INFO('  - Sucursal 2 (Maipú): maipu123'))
        self.stdout.write(self.style.HTTP_INFO('  - Sucursal 3 (Las Condes): condes123'))
        self.stdout.write(self.style.HTTP_INFO('\n🌐 URLs Disponibles:'))
        self.stdout.write(self.style.HTTP_INFO('  - API: http://localhost:8000/api/'))
        self.stdout.write(self.style.HTTP_INFO('  - Productos: http://localhost:8000/api/productos/'))
        self.stdout.write(self.style.HTTP_INFO('  - Sucursales: http://localhost:8000/api/sucursales/'))
        self.stdout.write(self.style.HTTP_INFO('  - Página de Venta: http://localhost:8000/venta/'))
        self.stdout.write(self.style.HTTP_INFO('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
