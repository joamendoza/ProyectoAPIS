from django.shortcuts import render, redirect, get_object_or_404
from inventario.models import Producto
from .models import Carrito

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'carrito/lista_productos.html', {'productos': productos})

def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito_item, created = Carrito.objects.get_or_create(producto=producto)
    if not created:
        carrito_item.cantidad += 1
    carrito_item.save()
    return redirect('ver_carrito')

def ver_carrito(request):
    carrito = Carrito.objects.all()
    total = sum(item.subtotal() for item in carrito)
    return render(request, 'carrito/ver_carrito.html', {'carrito': carrito, 'total': total})

def pagar(request):
    Carrito.objects.all().delete()  # Vacía el carrito después del pago
    return render(request, 'carrito/pago_exitoso.html')
