from fastapi import FastAPI, HTTPException, Header, status
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from typing import Annotated, List, Optional
from datetime import datetime

from models import Producto, ProductoInv

app = FastAPI()

## MongoDB connection
# Conexión a MongoDB
uri = "mongodb+srv://Admin:Admin@integracionpl.jwyptq0.mongodb.net/?retryWrites=true&w=majority&appName=IntegracionPl"
try:
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
# DB connection
db = client["Ferremas"]

## root endpoint
@app.get("/")
def root():
    return {"message": "API de Ferremas"}

## Endpoint para leer productos 
@app.get("/productos", response_model=List[Producto])
def read_productos_by_sucursal(
    sucursalid: Optional[int] = None,
    productoid: Optional[str] = None
):
    """
    Endpoint flexible para consultar productos con 4 opciones:
    1. Sin parámetros: Todos los productos sin inventario
    2. Solo productoid: Documento completo del producto
    3. Solo sucursalid: Inventario de la sucursal especificada
    4. Ambos: Inventario del producto en la sucursal especificada
    """
    try:
        # Opción 1: Mostrar todos los productos sin inventario
        if sucursalid is None and productoid is None:
            pipeline = [
                {"$project": {
                    "_id": 1,
                    "marca": 1,
                    "modelo": 1,
                    "nombre": 1,
                    "precio": 1,
                    "inventario": []  # Forzamos array vacío
                }}
            ]
            productos = db.Productos.aggregate(pipeline)
            return [Producto(**producto) for producto in productos]
        
        # Opción 2: Solo productoid - Documento completo
        elif productoid and not sucursalid:
            producto = db.Productos.find_one({"_id": productoid})
            if not producto:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            return [Producto(**producto)]
        
        # Opción 3: Solo sucursalid - Inventario de esa sucursal
        elif sucursalid and not productoid:
            pipeline = [
                {"$match": {"inventario.sucursal": sucursalid}},
                {"$addFields": {
                    "inventario": {
                        "$filter": {
                            "input": "$inventario",
                            "as": "item",
                            "cond": {"$eq": ["$$item.sucursal", sucursalid]}
                        }
                    }
                }}
            ]
            productos = db.Productos.aggregate(pipeline)
            return [Producto(**producto) for producto in productos]
        
        # Opción 4: Ambos - Inventario del producto en la sucursal
        else:
            pipeline = [
                {"$match": {
                    "_id": productoid,
                    "inventario.sucursal": sucursalid
                }},
                {"$addFields": {
                    "inventario": {
                        "$filter": {
                            "input": "$inventario",
                            "as": "item",
                            "cond": {"$eq": ["$$item.sucursal", sucursalid]}
                        }
                    }
                }},
                {"$limit": 1}
            ]
            producto = next(db.Productos.aggregate(pipeline), None)
            if not producto:
                raise HTTPException(
                    status_code=404,
                    detail="Producto no encontrado en la sucursal especificada"
                )
            return [Producto(**producto)]
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la consulta: {str(e)}"
        )

## Endpoint para crear productos (Administrador)
@app.post("/productos/{sucursalid}", response_model=Producto)
def create_producto(
    sucursalid: int,
    producto: ProductoInv,
    password: Annotated[str, Header(description="Contraseña de la sucursal")],
    adminpassword: Annotated[str, Header(description="Contraseña de administrador general")]
):
    """
    Crea un nuevo producto asociado a una sucursal específica con datos simplificados.
    Requiere contraseña de administrador general.
    Completa automáticamente:
    - Fecha actual para el precio
    - Sucursal y fecha para el inventario
    
    Args:
        sucursalid: ID de la sucursal donde se creará el producto
        producto: Datos básicos del producto (precio y cantidad como números simples)
        password: Contraseña de la sucursal (en el header)
    """
    try:
        # 1. Validar que la sucursal y el administrador existen y las contraseñas son correctas
        sucursal = db.Sucursales.find({
            "_id": sucursalid,
            "pass": password  # Las contraseñas se almacenan en texto plano
        })
        admin = db.Sucursales.find({
            "pass": adminpassword,  # Las contraseñas se almacenan en texto plano
            "_id": 0 
        })
        
        if not sucursal:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de sucursal inválidas"
            )
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de administrador inválidas"
            )
        
        # 2. Construir el objeto completo para MongoDB
        now = datetime.now().isoformat()
        producto_completo = {
            "_id": producto.id,
            "marca": producto.marca,
            "modelo": producto.modelo,
            "nombre": producto.nombre,
            "precio": [{
                "fecha": now,
                "valor": producto.precio
            }],
            "inventario": [{
                "sucursal": sucursalid,
                "cantidad": producto.cantidad,
                "ultima_actualizacion": now
            }]
        }
        
        # 3. Insertar en MongoDB
        result = db.Productos.insert_one(producto_completo)
        
        # 4. Retornar el producto creado
        created_product = db.Productos.find_one({"_id": result.inserted_id})
        return Producto(**created_product)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {str(e)}"
        )

## Endpoint para crear inventario de productos (sucursal)
@app.post("/productos/inventario/{sucursalid}", response_model=Producto)
def create_inventario(
    sucursalid: int,
    productoid: str,
    cantidad: int,
    password: Annotated[str, Header(description="Contraseña de la sucursal")]
):
    """
    Crea un nuevo inventario para un producto en una sucursal específica.
    
    Args:
        sucursalid: ID de la sucursal donde se creará el inventario
        cantidad: cantidad a agregar al inventario
        password: Contraseña de la sucursal (en el header)
    """
    try:
        # 1. Validar que la sucursal existe y la contraseña es correcta
        sucursal = db.Sucursales.find({
            "_id": sucursalid,
            "pass": password  # Las contraseñas se almacenan en texto plano
        })
        
        if not sucursal:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de sucursal inválidas"
            )
        
        # 2. Actualizar el inventario del producto
        now = datetime.now().isoformat()
        result = db.Productos.update_one(
            {
                "_id": productoid,
                "inventario.sucursal": {"$ne": sucursalid}  # Solo si no existe ya
            },
            {
                "$addToSet": {
                    "inventario": {
                        "sucursal": sucursalid,
                        "cantidad": cantidad,
                        "ultima_actualizacion": now
                    }
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto o sucursal no encontrados"
            )
        
        # 3. Retornar el producto actualizado
        updated_product = db.Productos.find_one({"_id": productoid})
        return Producto(**updated_product)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear inventario: {str(e)}"
        )

## Endpoint para actualizar inventario de productos (sucursal)
@app.put("/productos/{sucursalid}/{productoid}", response_model=Producto)
def update_inventario(
    sucursalid: int,
    productoid: str,
    cantidad: int,
    password: Annotated[str, Header(description="Contraseña de la sucursal")]
):
    """
    Actualiza el inventario de un producto en una sucursal específica.
    
    Args:
        sucursalid: ID de la sucursal donde se actualizará el inventario
        productoid: ID del producto a actualizar
        cantidad: nueva cantidad en inventario
        password: Contraseña de la sucursal (en el header)
    """
    try:
        # 1. Validar que la sucursal existe y la contraseña es correcta
        sucursal = db.Sucursales.find({
            "_id": sucursalid,
            "pass": password  # Las contraseñas se almacenan en texto plano
        })
        
        if not sucursal:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de sucursal inválidas"
            )
        
        # 2. Actualizar el inventario del producto
        now = datetime.now().isoformat()
        result = db.Productos.update_one(
            {
                "_id": productoid,
                "inventario.sucursal": sucursalid
            },
            {
                "$set": {
                    "inventario.$.cantidad": cantidad,
                    "inventario.$.ultima_actualizacion": now
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto o sucursal no encontrados"
            )
        
        # 3. Retornar el producto actualizado
        updated_product = db.Productos.find_one({"_id": productoid})
        return Producto(**updated_product)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar inventario: {str(e)}"
        )

## Endpoint para eliminar productos (Administrador)
@app.delete("/productos/{productoid}")
def delete_producto(
    productoid: str,
    adminpassword: Annotated[str, Header(description="Contraseña de administrador general")],
):
    """
    Elimina un producto de la base de datos.
    
    Args:
        productoid: ID del producto a eliminar
        adminpassword: Contraseña de administrador general (en el header)
    """
    try:
        # 1. Validar que el administrador existe y la contraseña es correcta
        admin = db.Sucursales.find({
            "pass": adminpassword,  # Las contraseñas se almacenan en texto plano
            "_id": 0 
        })
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de administrador inválidas"
            )
        
        # 2. Eliminar el producto
        result = db.Productos.delete_one({"_id": productoid})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        return {"message": "Producto eliminado exitosamente"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar producto: {str(e)}"
        )

















