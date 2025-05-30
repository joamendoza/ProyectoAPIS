# Generated by Django 5.2.1 on 2025-05-26 20:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carrito', '0001_initial'),
        ('inventario', '0002_alter_producto_precio'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Boleta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20, unique=True)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DetalleBoleta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField()),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10)),
                ('boleta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='carrito.boleta')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.producto')),
            ],
        ),
    ]
