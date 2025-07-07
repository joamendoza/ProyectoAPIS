"""
Configuración para conexión a MongoDB
Mantiene compatibilidad con la base de datos original de Ferremas
"""

# Configuración de MongoDB
MONGODB_CONFIG = {
    'URI': "mongodb+srv://Admin:Admin@integracionpl.jwyptq0.mongodb.net/?retryWrites=true&w=majority&appName=IntegracionPl",
    'DATABASE': "Ferremas",
    'COLLECTIONS': {
        'PRODUCTOS': 'Productos',
        'SUCURSALES': 'Sucursales'
    }
}

# Función para obtener cliente MongoDB
def get_mongodb_client():
    """
    Retorna un cliente de MongoDB configurado
    Requiere: pip install pymongo
    """
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        
        client = MongoClient(MONGODB_CONFIG['URI'], server_api=ServerApi('1'))
        client.admin.command('ping')
        print("Conexión a MongoDB exitosa!")
        return client
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        return None

# Función para migrar datos desde MongoDB a Django
def migrate_from_mongodb():
    """
    Migra datos desde MongoDB a los modelos Django
    Ejecutar desde Django shell: python manage.py shell
    """
    client = get_mongodb_client()
    if not client:
        return
    
    db = client[MONGODB_CONFIG['DATABASE']]
    
    # Importar modelos Django
    from ferremas.models import ProductoFerremas, PrecioProducto, InventarioProducto, Sucursal
    from datetime import datetime
    
    # Migrar productos
    productos_mongo = db[MONGODB_CONFIG['COLLECTIONS']['PRODUCTOS']].find()
    
    for producto_mongo in productos_mongo:
        try:
            # Crear producto en Django
            producto_django, created = ProductoFerremas.objects.get_or_create(
                id_producto=producto_mongo['_id'],
                defaults={
                    'marca': producto_mongo.get('marca', ''),
                    'modelo': producto_mongo.get('modelo', ''),
                    'nombre': producto_mongo.get('nombre', '')
                }
            )
            
            if created:
                # Migrar precios
                for precio_mongo in producto_mongo.get('precio', []):
                    PrecioProducto.objects.create(
                        producto=producto_django,
                        fecha=precio_mongo.get('fecha', datetime.now()),
                        valor=precio_mongo.get('valor', 0)
                    )
                
                # Migrar inventarios
                for inventario_mongo in producto_mongo.get('inventario', []):
                    try:
                        sucursal = Sucursal.objects.get(id=inventario_mongo['sucursal'])
                        InventarioProducto.objects.create(
                            producto=producto_django,
                            sucursal=sucursal,
                            cantidad=inventario_mongo.get('cantidad', 0),
                            ultima_actualizacion=inventario_mongo.get('ultima_actualizacion', datetime.now())
                        )
                    except Sucursal.DoesNotExist:
                        print(f"Sucursal {inventario_mongo['sucursal']} no encontrada")
                
                print(f"Producto {producto_django.nombre} migrado exitosamente")
            else:
                print(f"Producto {producto_django.nombre} ya existe")
                
        except Exception as e:
            print(f"Error migrando producto {producto_mongo.get('_id', 'unknown')}: {e}")
    
    client.close()
    print("Migración completada")

# Función para sincronizar datos con MongoDB
def sync_to_mongodb():
    """
    Sincroniza datos de Django hacia MongoDB
    Mantiene compatibilidad con la API original
    """
    client = get_mongodb_client()
    if not client:
        return
    
    db = client[MONGODB_CONFIG['DATABASE']]
    
    # Importar modelos Django
    from ferremas.models import ProductoFerremas
    
    # Sincronizar productos
    productos_django = ProductoFerremas.objects.prefetch_related('precios', 'inventarios')
    
    for producto_django in productos_django:
        try:
            # Construir documento MongoDB
            documento_mongo = {
                '_id': producto_django.id_producto,
                'marca': producto_django.marca,
                'modelo': producto_django.modelo,
                'nombre': producto_django.nombre,
                'precio': [
                    {
                        'fecha': precio.fecha.isoformat(),
                        'valor': float(precio.valor)
                    }
                    for precio in producto_django.precios.all()
                ],
                'inventario': [
                    {
                        'sucursal': inventario.sucursal.id,
                        'cantidad': inventario.cantidad,
                        'ultima_actualizacion': inventario.ultima_actualizacion.isoformat()
                    }
                    for inventario in producto_django.inventarios.all()
                ]
            }
            
            # Actualizar o insertar en MongoDB
            db[MONGODB_CONFIG['COLLECTIONS']['PRODUCTOS']].replace_one(
                {'_id': producto_django.id_producto},
                documento_mongo,
                upsert=True
            )
            
            print(f"Producto {producto_django.nombre} sincronizado con MongoDB")
            
        except Exception as e:
            print(f"Error sincronizando producto {producto_django.nombre}: {e}")
    
    client.close()
    print("Sincronización completada")

# Instrucciones de uso:
"""
Para usar estas funciones:

1. Instalar pymongo:
   pip install pymongo

2. Desde Django shell:
   python manage.py shell
   
3. Importar y ejecutar:
   from ferremas.mongodb_utils import migrate_from_mongodb, sync_to_mongodb
   
   # Para migrar desde MongoDB a Django:
   migrate_from_mongodb()
   
   # Para sincronizar desde Django a MongoDB:
   sync_to_mongodb()
"""
