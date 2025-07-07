from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventario.models import Sucursal, Producto, PrecioProducto, InventarioProducto
from carrito.models import Administrador
from datetime import datetime


class Command(BaseCommand):
    help = 'Poblar la base de datos con datos iniciales para Ferremas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando poblado de datos para Ferremas...'))
        
        # Crear sucursales
        sucursales_data = [
            {
                'id': 1,
                'nombre': 'Ferremas Centro',
                'password': 'centro123',
                'calle': 'Av. Libertador Bernardo O\'Higgins',
                'numeracion': '1234',
                'comuna': 'Santiago',
                'region': 'Metropolitana'
            },
            {
                'id': 2,
                'nombre': 'Ferremas Maipú',
                'password': 'maipu123',
                'calle': 'Av. Pajaritos',
                'numeracion': '5678',
                'comuna': 'Maipú',
                'region': 'Metropolitana'
            },
            {
                'id': 3,
                'nombre': 'Ferremas Las Condes',
                'password': 'condes123',
                'calle': 'Av. Apoquindo',
                'numeracion': '9012',
                'comuna': 'Las Condes',
                'region': 'Metropolitana'
            }
        ]
        
        for sucursal_data in sucursales_data:
            sucursal, created = Sucursal.objects.get_or_create(
                id=sucursal_data['id'],
                defaults=sucursal_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Sucursal "{sucursal.nombre}" creada exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Sucursal "{sucursal.nombre}" ya existe')
                )
        
        # Crear administrador
        try:
            # Crear usuario administrador si no existe
            admin_user, created = User.objects.get_or_create(
                username='admin_ferremas',
                defaults={
                    'email': 'admin@ferremas.cl',
                    'first_name': 'Admin',
                    'last_name': 'Ferremas',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                admin_user.set_password('admin2024')
                admin_user.save()
                self.stdout.write(
                    self.style.SUCCESS('Usuario administrador creado exitosamente')
                )
            
            # Crear administrador de Ferremas
            admin_ferremas, created = Administrador.objects.get_or_create(
                usuario=admin_user,
                defaults={'password_admin': 'admin123'}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Administrador de Ferremas creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Administrador de Ferremas ya existe')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear administrador: {str(e)}')
            )
        
        # Crear productos de ejemplo
        productos_data = [
            {
                'id_producto': 'TALADRO-001',
                'marca': 'Bosch',
                'modelo': 'GSB 13 RE',
                'nombre': 'Taladro Percutor 13mm 600W',
                'categoria': 'herramientas',
                'descripcion': 'Taladro percutor profesional con cable, ideal para trabajos pesados',
                'precio': 89990,
                'inventarios': [
                    {'sucursal_id': 1, 'cantidad': 25},
                    {'sucursal_id': 2, 'cantidad': 15},
                    {'sucursal_id': 3, 'cantidad': 30}
                ]
            },
            {
                'id_producto': 'SIERRA-002',
                'marca': 'DeWalt',
                'modelo': 'DWE575',
                'nombre': 'Sierra Circular 7-1/4" 1600W',
                'categoria': 'herramientas',
                'descripcion': 'Sierra circular profesional con disco de 7-1/4 pulgadas',
                'precio': 129990,
                'inventarios': [
                    {'sucursal_id': 1, 'cantidad': 12},
                    {'sucursal_id': 2, 'cantidad': 8},
                    {'sucursal_id': 3, 'cantidad': 20}
                ]
            },
            {
                'id_producto': 'TORNILLO-003',
                'marca': 'Hilti',
                'modelo': 'X-U 6x60',
                'nombre': 'Tornillo Autoperforante 6x60mm (Caja 100 unidades)',
                'categoria': 'tornillos',
                'descripcion': 'Tornillos autoperforantes para metal, caja de 100 unidades',
                'precio': 12990,
                'inventarios': [
                    {'sucursal_id': 1, 'cantidad': 50},
                    {'sucursal_id': 2, 'cantidad': 35},
                    {'sucursal_id': 3, 'cantidad': 40}
                ]
            },
            {
                'id_producto': 'PINTURA-004',
                'marca': 'Sipa',
                'modelo': 'Látex Premium',
                'nombre': 'Pintura Látex Blanco Semi-Mate 1 Galón',
                'categoria': 'materiales',
                'descripcion': 'Pintura látex premium para interiores y exteriores',
                'precio': 19990,
                'inventarios': [
                    {'sucursal_id': 1, 'cantidad': 100},
                    {'sucursal_id': 2, 'cantidad': 75},
                    {'sucursal_id': 3, 'cantidad': 85}
                ]
            },
            {
                'id_producto': 'CABLE-005',
                'marca': 'Procobre',
                'modelo': 'NYA 12 AWG',
                'nombre': 'Cable Eléctrico NYA 12 AWG (Metro)',
                'categoria': 'materiales',
                'descripcion': 'Cable eléctrico de cobre para instalaciones domiciliarias',
                'precio': 890,
                'inventarios': [
                    {'sucursal_id': 1, 'cantidad': 500},
                    {'sucursal_id': 2, 'cantidad': 300},
                    {'sucursal_id': 3, 'cantidad': 450}
                ]
            },
            {
                'id_producto': 'CASCO-006',
                'marca': '3M',
                'modelo': 'H-700',
                'nombre': 'Casco de Seguridad Industrial',
                'categoria': 'seguridad',
                'descripcion': 'Casco de seguridad industrial con barboquejo ajustable',
                'precio': 15990,
                'inventarios': [
                    {'sucursal_id': 1, 'cantidad': 40},
                    {'sucursal_id': 2, 'cantidad': 25},
                    {'sucursal_id': 3, 'cantidad': 35}
                ]
            }
        ]
        
        for producto_data in productos_data:
            try:
                # Crear producto
                producto, created = Producto.objects.get_or_create(
                    id_producto=producto_data['id_producto'],
                    defaults={
                        'marca': producto_data['marca'],
                        'modelo': producto_data['modelo'],
                        'nombre': producto_data['nombre'],
                        'categoria': producto_data['categoria'],
                        'descripcion': producto_data['descripcion']
                    }
                )
                
                if created:
                    # Crear precio
                    PrecioProducto.objects.create(
                        producto=producto,
                        valor=producto_data['precio'],
                        fecha=datetime.now()
                    )
                    
                    # Crear inventarios
                    for inventario_data in producto_data['inventarios']:
                        sucursal = Sucursal.objects.get(id=inventario_data['sucursal_id'])
                        InventarioProducto.objects.create(
                            producto=producto,
                            sucursal=sucursal,
                            cantidad=inventario_data['cantidad'],
                            ultima_actualizacion=datetime.now()
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Producto "{producto.nombre}" creado exitosamente')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Producto "{producto.nombre}" ya existe')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al crear producto {producto_data["id_producto"]}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('¡Poblado de datos completado exitosamente!')
        )
        self.stdout.write(
            self.style.SUCCESS('Credenciales de administrador:')
        )
        self.stdout.write(
            self.style.SUCCESS('  - Usuario Django: admin_ferremas / admin2024')
        )
        self.stdout.write(
            self.style.SUCCESS('  - Password Admin API: admin123')
        )
        self.stdout.write(
            self.style.SUCCESS('Credenciales de sucursales:')
        )
        self.stdout.write(
            self.style.SUCCESS('  - Sucursal 1: centro123')
        )
        self.stdout.write(
            self.style.SUCCESS('  - Sucursal 2: maipu123')
        )
        self.stdout.write(
            self.style.SUCCESS('  - Sucursal 3: condes123')
        )
