"""
Configuración de MongoDB para Ferremas API
"""
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import mongoengine

# Configuración de MongoDB Atlas
MONGODB_SETTINGS = {
    'host': 'mongodb+srv://Admin:Admin@integracionpl.jwyptq0.mongodb.net/?retryWrites=true&w=majority&appName=IntegracionPl',
    'db': 'Ferremas',
    'connect': False,  # Para evitar problemas con threading en Django
}

# Cliente MongoDB para operaciones directas
def get_mongo_client():
    """Obtiene el cliente de MongoDB"""
    uri = "mongodb+srv://Admin:Admin@integracionpl.jwyptq0.mongodb.net/?retryWrites=true&w=majority&appName=IntegracionPl"
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        # Ping para verificar conexión
        client.admin.command('ping')
        print("✅ Conexión exitosa a MongoDB Atlas")
        return client
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return None

# Configurar MongoEngine para Django
def configure_mongoengine():
    """Configura MongoEngine para Django"""
    try:
        # Desconectar cualquier conexión existente
        mongoengine.disconnect()
        
        # Conectar con configuración optimizada
        mongoengine.connect(
            db='Ferremas',
            host='mongodb+srv://Admin:Admin@integracionpl.jwyptq0.mongodb.net/?retryWrites=true&w=majority&appName=IntegracionPl',
            connect=False,
            maxPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000
        )
        print("✅ MongoEngine configurado correctamente")
    except Exception as e:
        print(f"❌ Error configurando MongoEngine: {e}")

# Obtener base de datos
def get_database():
    """Obtiene la base de datos de Ferremas"""
    client = get_mongo_client()
    if client:
        return client["Ferremas"]
    return None
