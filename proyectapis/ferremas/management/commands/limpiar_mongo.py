"""
Comando para limpiar y reconfigurar MongoDB
"""
from django.core.management.base import BaseCommand
from ferremas.mongo_config import configure_mongoengine, get_mongo_client
import mongoengine

class Command(BaseCommand):
    help = 'Limpia y reconfigura MongoDB para evitar errores de índices'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧹 Iniciando limpieza de MongoDB...'))
        
        try:
            # Desconectar MongoEngine
            mongoengine.disconnect()
            self.stdout.write(self.style.SUCCESS('✅ Desconectado MongoEngine'))
            
            # Obtener cliente directo de MongoDB
            client = get_mongo_client()
            if client:
                db = client["Ferremas"]
                
                # Eliminar todas las colecciones
                collections = db.list_collection_names()
                for collection in collections:
                    db.drop_collection(collection)
                    self.stdout.write(self.style.SUCCESS(f'✅ Colección {collection} eliminada'))
                
                self.stdout.write(self.style.SUCCESS('✅ Base de datos limpiada'))
                client.close()
            
            # Reconfigurar MongoEngine
            configure_mongoengine()
            self.stdout.write(self.style.SUCCESS('✅ MongoEngine reconfigurado'))
            
            self.stdout.write(self.style.SUCCESS('🎉 Limpieza completada. Ejecuta "python manage.py poblar_mongo" para repoblar'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error durante la limpieza: {e}'))
