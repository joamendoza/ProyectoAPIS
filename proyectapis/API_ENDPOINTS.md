# 📡 API ENDPOINTS - FERREMAS MONGODB

## 🌐 Base URL
```
http://127.0.0.1:8000/api/
```

## 🔑 Credenciales de Sucursales
```
- Sucursal 1 (Centro): centro123
- Sucursal 2 (Maipú): maipu123  
- Sucursal 3 (Las Condes): condes123
- Administrador: admin123
```

## 📋 Endpoints Principales

### 1. **Información General**
```
GET /api/
```
- **Descripción**: Información básica de la API
- **Respuesta**: Mensaje de bienvenida y versión

### 2. **Productos**

#### 2.1 Consultar Todos los Productos
```
GET /api/productos/
```
- **Descripción**: Obtiene lista completa de productos
- **Parámetros opcionales**:
  - `?productoid=TALADRO-001` - Filtrar por ID de producto
  - `?sucursalid=1` - Filtrar por sucursal
  - `?marca=Bosch` - Filtrar por marca

#### 2.2 Productos para Venta
```
GET /api/productos/venta/
```
- **Descripción**: Productos disponibles para venta con stock > 0
- **Respuesta**: Lista de productos con información de inventario

#### 2.3 Crear Producto (Administrador)
```
POST /api/productos/{sucursal_id}/
```
- **Headers requeridos**:
  ```json
  {
    "Content-Type": "application/json",
    "password": "centro123",
    "adminpassword": "admin123"
  }
  ```
- **Body ejemplo**:
  ```json
  {
    "_id": "PRODUCTO-001",
    "marca": "TestMarca",
    "nombre": "Producto de Prueba",
    "precio": 10000,
    "cantidad": 50
  }
  ```

### 3. **Sucursales**

#### 3.1 Consultar Sucursales
```
GET /api/sucursales/
```
- **Descripción**: Lista todas las sucursales disponibles
- **Respuesta**: Información de sucursales con ubicación

#### 3.2 Inventario por Sucursal
```
GET /api/sucursales/{sucursal_id}/inventario/
```
- **Descripción**: Productos disponibles en una sucursal específica
- **Ejemplo**: `GET /api/sucursales/1/inventario/`

#### 3.3 Producto en Sucursales
```
GET /api/productos/{producto_id}/sucursales/
```
- **Descripción**: Disponibilidad de un producto en todas las sucursales
- **Ejemplo**: `GET /api/productos/TALADRO-001/sucursales/`

#### 3.4 Actualizar Stock
```
POST /api/sucursales/{sucursal_id}/productos/{producto_id}/stock/
```
- **Headers requeridos**:
  ```json
  {
    "Content-Type": "application/json",
    "password": "centro123"
  }
  ```
- **Body ejemplo**:
  ```json
  {
    "cantidad": 25,
    "operacion": "agregar"
  }
  ```

### 4. **Carrito de Compras**

#### 4.1 Agregar al Carrito
```
POST /api/carrito/agregar/
```
- **Body ejemplo**:
  ```json
  {
    "producto_id": "TALADRO-001",
    "cantidad": 2,
    "sucursal_id": 1
  }
  ```

#### 4.2 Ver Carrito
```
GET /api/carrito/ver/
```
- **Descripción**: Contenido actual del carrito

#### 4.3 Actualizar Cantidad
```
POST /api/carrito/actualizar/{item_id}/
```
- **Body ejemplo**:
  ```json
  {
    "cantidad": 3
  }
  ```

#### 4.4 Eliminar del Carrito
```
DELETE /api/carrito/eliminar/{item_id}/
```

#### 4.5 Cambiar Sucursal
```
POST /api/carrito/cambiar-sucursal/{item_id}/
```
- **Body ejemplo**:
  ```json
  {
    "nueva_sucursal": 2
  }
  ```

#### 4.6 Contar Items
```
GET /api/carrito/count/
```
- **Respuesta**: Número total de items en el carrito

#### 4.7 Procesar Compra
```
POST /api/carrito/procesar/
```
- **Body ejemplo**:
  ```json
  {
    "nombre": "Juan Pérez",
    "email": "juan@email.com",
    "direccion": "Calle 123",
    "telefono": "123456789",
    "metodo_pago": "webpay"
  }
  ```

### 5. **Compras y Boletas**

#### 5.1 Compra Exitosa
```
GET /api/compra/exitosa/
```
- **Descripción**: Página de confirmación de compra exitosa

#### 5.2 Compra Rechazada
```
GET /api/compra/rechazada/
```
- **Descripción**: Página de compra rechazada

#### 5.3 Ver Boleta
```
GET /api/boleta/{boleta_codigo}/
```
- **Descripción**: Detalles de una boleta específica

#### 5.4 Generar PDF
```
GET /api/carrito/boleta/{boleta_id}/pdf/
```
- **Descripción**: Descargar boleta en formato PDF

## 📋 Boletas - Consultas y Estadísticas

### 6.1 Consultar Boletas
```
GET /api/boletas/
```
- **Descripción**: Consultar boletas con filtros avanzados
- **Parámetros opcionales**:
  - `?codigo=BOL-123456` - Código específico de boleta
  - `?usuario_id=user123` - ID del usuario
  - `?fecha_desde=2024-01-01` - Fecha desde (YYYY-MM-DD)
  - `?fecha_hasta=2024-12-31` - Fecha hasta (YYYY-MM-DD)
  - `?estado=completada` - Estado (completada, pendiente, cancelada)
  - `?sucursal_id=1` - ID de sucursal
  - `?metodo_pago=webpay` - Método de pago (webpay, efectivo, transferencia)
  - `?limit=50` - Límite de resultados (max: 100)
  - `?offset=0` - Offset para paginación

### 6.2 Detalle de Boleta
```
GET /api/boletas/{boleta_codigo}/
```
- **Descripción**: Obtener detalles completos de una boleta específica
- **Ejemplo**: `GET /api/boletas/BOL-1704672000-1234/`

### 6.3 Estadísticas de Boletas
```
GET /api/boletas/estadisticas/
```
- **Descripción**: Obtener estadísticas de ventas y boletas
- **Parámetros opcionales**:
  - `?fecha_desde=2024-01-01` - Fecha desde
  - `?fecha_hasta=2024-12-31` - Fecha hasta
  - `?sucursal_id=1` - Filtrar por sucursal
- **Respuesta incluye**:
  - Total de boletas y ventas
  - Estadísticas por estado
  - Estadísticas por método de pago
  - Estadísticas por sucursal

## 🧪 Ejemplos de Uso (PowerShell)

### Consultar Productos
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/productos/" -Method GET
```

### Crear Producto
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "password" = "centro123"
    "adminpassword" = "admin123"
}
$body = @{
    "_id" = "PRODUCTO-001"
    "marca" = "TestMarca"
    "nombre" = "Producto de Prueba"
    "precio" = 10000
    "cantidad" = 50
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/productos/1/" -Method POST -Headers $headers -Body $body
```

### Agregar al Carrito
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    "producto_id" = "TALADRO-001"
    "cantidad" = 2
    "sucursal_id" = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/carrito/agregar/" -Method POST -Headers $headers -Body $body
```

### Consultar Boletas
```powershell
# Todas las boletas
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/boletas/" -Method GET

# Boletas por fecha
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/boletas/?fecha_desde=2024-01-01&fecha_hasta=2024-12-31" -Method GET

# Boletas por sucursal
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/boletas/?sucursal_id=1" -Method GET

# Boletas completadas con límite
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/boletas/?estado=completada&limit=10" -Method GET
```

### Detalle de Boleta
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/boletas/BOL17046720001234/" -Method GET
```

### Estadísticas de Boletas
```powershell
# Estadísticas generales
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/boletas/estadisticas/" -Method GET

# Estadísticas por periodo
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/boletas/estadisticas/?fecha_desde=2024-01-01&fecha_hasta=2024-01-31" -Method GET
```

## 📊 Códigos de Respuesta

- **200**: Éxito
- **201**: Creado exitosamente
- **400**: Error en los datos enviados
- **401**: No autorizado (credenciales incorrectas)
- **404**: Recurso no encontrado
- **500**: Error interno del servidor

## 🔧 Notas Técnicas

1. **Sesiones**: El carrito se mantiene por sesión de usuario
2. **Cookies**: Necesarias para el funcionamiento del carrito
3. **CORS**: Configurado para desarrollo local
4. **Autenticación**: Basada en passwords de sucursal en headers
5. **Base de Datos**: MongoDB Atlas (sin migraciones requeridas)

## 🐛 Debugging

Para debugging de APIs, puedes usar:
- **Postman** para pruebas de endpoints
- **Browser DevTools** para inspeccionar requests
- **Django Debug Toolbar** (si está instalado)
- **Logs del servidor** en la consola donde ejecutas `runserver`

## 💳 Tarjetas de Prueba Webpay

Para testing de pagos en ambiente sandbox:

### ✅ Tarjetas Aprobadas
```
VISA:
- Número: 4051 8856 0000 0005
- CVV: 123
- Vencimiento: Cualquier fecha futura

MASTERCARD:
- Número: 5186 0595 0000 0000
- CVV: 123
- Vencimiento: Cualquier fecha futura
```

### ❌ Tarjetas Rechazadas
```
VISA:
- Número: 4051 8842 3993 7763
- CVV: 123
- Vencimiento: Cualquier fecha futura

MASTERCARD:
- Número: 5186 0395 0000 0000
- CVV: 123
- Vencimiento: Cualquier fecha futura
```

### 👤 Datos del Tarjetahabiente
```
RUT: 11.111.111-1
Nombre: Cualquier nombre
Email: test@test.com
Teléfono: 123456789
```

⚠️ **Nota**: Solo para ambiente de testing, NO usar en producción.
