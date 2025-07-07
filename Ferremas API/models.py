
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class Precio(BaseModel):
    fecha: datetime
    valor: float

class InventarioItem(BaseModel):
    sucursal: int
    cantidad: int
    ultima_actualizacion: datetime

class Producto(BaseModel):
    id: str = Field(alias="_id")
    inventario: List[InventarioItem] = []
    marca: str
    modelo: str
    nombre: str
    precio: List[Precio] = []

class ProductoInv(BaseModel):
    id: str = Field(alias="_id")
    cantidad: int
    marca: str
    modelo: str
    nombre: str
    precio: int

class Direccion(BaseModel):
    calle: str
    numeracion: str
    comuna: str
    region: str

class sucursal(BaseModel):
    id: str = Field(alias="_id")
    nombrepila: str
    contra: str = Field(alias="pass")
    direccion: Direccion