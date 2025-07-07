from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
import json

from .models import ProductoFerremas, PrecioProducto, InventarioProducto, Sucursal, Administrador
from datetime import datetime


class FerremasAPITestCase(TestCase):
    """Pruebas para la API de Ferremas"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        
        # Crear sucursales de prueba
        self.sucursal1 = Sucursal.objects.create(
            id=1,
            nombre='Sucursal Test 1',
            password='test123',
            calle='Calle Test',
            numeracion='123',
            comuna='Comuna Test',
            region='Region Test'
        )
        
        self.sucursal2 = Sucursal.objects.create(
            id=2,
            nombre='Sucursal Test 2',
            password='test456',
            calle='Calle Test 2',
            numeracion='456',
            comuna='Comuna Test 2',
            region='Region Test 2'
        )
        
        # Crear administrador de prueba
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='adminpass'
        )
        
        self.admin_ferremas = Administrador.objects.create(
            usuario=self.admin_user,
            password_admin='admin123'
        )
        
        # Crear producto de prueba
        self.producto = ProductoFerremas.objects.create(
            id_producto='TEST-001',
            marca='Marca Test',
            modelo='Modelo Test',
            nombre='Producto Test'
        )
        
        # Crear precio de prueba
        self.precio = PrecioProducto.objects.create(
            producto=self.producto,
            valor=10000,
            fecha=datetime.now()
        )
        
        # Crear inventario de prueba
        self.inventario = InventarioProducto.objects.create(
            producto=self.producto,
            sucursal=self.sucursal1,
            cantidad=50,
            ultima_actualizacion=datetime.now()
        )
    
    def test_root_endpoint(self):
        """Prueba el endpoint raíz"""
        response = self.client.get(reverse('ferremas:root'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('API de Ferremas', response.json()['message'])
    
    def test_read_productos_sin_parametros(self):
        """Prueba consultar todos los productos sin inventario"""
        response = self.client.get(reverse('ferremas:read_productos'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['_id'], 'TEST-001')
        self.assertEqual(data[0]['inventario'], [])
    
    def test_read_productos_con_productoid(self):
        """Prueba consultar un producto específico"""
        response = self.client.get(
            reverse('ferremas:read_productos'),
            {'productoid': 'TEST-001'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['_id'], 'TEST-001')
        self.assertEqual(len(data[0]['inventario']), 1)
    
    def test_read_productos_con_sucursalid(self):
        """Prueba consultar inventario de una sucursal"""
        response = self.client.get(
            reverse('ferremas:read_productos'),
            {'sucursalid': 1}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['inventario'][0]['sucursal'], 1)
    
    def test_read_productos_con_ambos_parametros(self):
        """Prueba consultar producto específico en sucursal específica"""
        response = self.client.get(
            reverse('ferremas:read_productos'),
            {'productoid': 'TEST-001', 'sucursalid': 1}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['_id'], 'TEST-001')
        self.assertEqual(data[0]['inventario'][0]['sucursal'], 1)
    
    def test_create_producto_exitoso(self):
        """Prueba crear un producto exitosamente"""
        data = {
            '_id': 'NUEVO-001',
            'marca': 'Nueva Marca',
            'modelo': 'Nuevo Modelo',
            'nombre': 'Nuevo Producto',
            'precio': 15000,
            'cantidad': 25
        }
        
        response = self.client.post(
            reverse('ferremas:create_producto', kwargs={'sucursal_id': 1}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_PASSWORD='test123',
            HTTP_ADMINPASSWORD='admin123'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que el producto fue creado
        producto = ProductoFerremas.objects.get(id_producto='NUEVO-001')
        self.assertEqual(producto.marca, 'Nueva Marca')
        self.assertEqual(producto.precios.first().valor, 15000)
        self.assertEqual(producto.inventarios.first().cantidad, 25)
    
    def test_create_producto_credenciales_invalidas(self):
        """Prueba crear producto con credenciales inválidas"""
        data = {
            '_id': 'NUEVO-002',
            'marca': 'Marca',
            'modelo': 'Modelo',
            'nombre': 'Producto',
            'precio': 10000,
            'cantidad': 10
        }
        
        response = self.client.post(
            reverse('ferremas:create_producto', kwargs={'sucursal_id': 1}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_PASSWORD='password_incorrecta',
            HTTP_ADMINPASSWORD='admin123'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_inventario_exitoso(self):
        """Prueba crear inventario exitosamente"""
        # Crear otro producto sin inventario en sucursal 2
        producto2 = ProductoFerremas.objects.create(
            id_producto='TEST-002',
            marca='Marca 2',
            modelo='Modelo 2',
            nombre='Producto 2'
        )
        
        data = {
            'productoid': 'TEST-002',
            'cantidad': 30
        }
        
        response = self.client.post(
            reverse('ferremas:create_inventario', kwargs={'sucursal_id': 2}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_PASSWORD='test456'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que el inventario fue creado
        inventario = InventarioProducto.objects.get(
            producto=producto2,
            sucursal=self.sucursal2
        )
        self.assertEqual(inventario.cantidad, 30)
    
    def test_update_inventario_exitoso(self):
        """Prueba actualizar inventario exitosamente"""
        data = {'cantidad': 75}
        
        response = self.client.put(
            reverse('ferremas:update_inventario', kwargs={
                'sucursal_id': 1,
                'producto_id': 'TEST-001'
            }),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_PASSWORD='test123'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el inventario fue actualizado
        inventario = InventarioProducto.objects.get(
            producto=self.producto,
            sucursal=self.sucursal1
        )
        self.assertEqual(inventario.cantidad, 75)
    
    def test_delete_producto_exitoso(self):
        """Prueba eliminar producto exitosamente"""
        response = self.client.delete(
            reverse('ferremas:delete_producto', kwargs={'producto_id': 'TEST-001'}),
            HTTP_ADMINPASSWORD='admin123'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el producto fue eliminado
        with self.assertRaises(ProductoFerremas.DoesNotExist):
            ProductoFerremas.objects.get(id_producto='TEST-001')
    
    def test_delete_producto_credenciales_invalidas(self):
        """Prueba eliminar producto con credenciales inválidas"""
        response = self.client.delete(
            reverse('ferremas:delete_producto', kwargs={'producto_id': 'TEST-001'}),
            HTTP_ADMINPASSWORD='password_incorrecta'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verificar que el producto no fue eliminado
        producto = ProductoFerremas.objects.get(id_producto='TEST-001')
        self.assertIsNotNone(producto)


class FerremasModelsTestCase(TestCase):
    """Pruebas para los modelos de Ferremas"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.sucursal = Sucursal.objects.create(
            nombre='Sucursal Test',
            password='test123',
            calle='Calle Test',
            numeracion='123',
            comuna='Comuna Test',
            region='Region Test'
        )
        
        self.producto = ProductoFerremas.objects.create(
            id_producto='TEST-001',
            marca='Marca Test',
            modelo='Modelo Test',
            nombre='Producto Test'
        )
    
    def test_crear_sucursal(self):
        """Prueba crear una sucursal"""
        self.assertEqual(self.sucursal.nombre, 'Sucursal Test')
        self.assertEqual(str(self.sucursal), 'Sucursal Test - Comuna Test')
    
    def test_crear_producto(self):
        """Prueba crear un producto"""
        self.assertEqual(self.producto.marca, 'Marca Test')
        self.assertEqual(str(self.producto), 'Marca Test Modelo Test - Producto Test')
    
    def test_crear_precio(self):
        """Prueba crear un precio"""
        precio = PrecioProducto.objects.create(
            producto=self.producto,
            valor=12500,
            fecha=datetime.now()
        )
        
        self.assertEqual(precio.valor, 12500)
        self.assertEqual(precio.producto, self.producto)
    
    def test_crear_inventario(self):
        """Prueba crear un inventario"""
        inventario = InventarioProducto.objects.create(
            producto=self.producto,
            sucursal=self.sucursal,
            cantidad=100,
            ultima_actualizacion=datetime.now()
        )
        
        self.assertEqual(inventario.cantidad, 100)
        self.assertEqual(inventario.producto, self.producto)
        self.assertEqual(inventario.sucursal, self.sucursal)
    
    def test_unique_constraint_inventario(self):
        """Prueba la restricción de único en inventario"""
        # Crear primer inventario
        InventarioProducto.objects.create(
            producto=self.producto,
            sucursal=self.sucursal,
            cantidad=50,
            ultima_actualizacion=datetime.now()
        )
        
        # Intentar crear segundo inventario para mismo producto y sucursal
        with self.assertRaises(Exception):
            InventarioProducto.objects.create(
                producto=self.producto,
                sucursal=self.sucursal,
                cantidad=75,
                ultima_actualizacion=datetime.now()
            )
