# Generated by Django 5.2.1 on 2025-05-26 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carrito', '0002_boleta_detalleboleta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='boleta',
            name='usuario',
        ),
        migrations.AddField(
            model_name='boleta',
            name='usuario_id_unico',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
