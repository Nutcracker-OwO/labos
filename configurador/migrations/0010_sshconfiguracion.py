# Generated by Django 5.1.7 on 2025-03-31 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configurador', '0009_remove_laboratorio_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='SSHConfiguracion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host', models.CharField(help_text='IP o nombre del servidor SSH', max_length=255)),
                ('usuario', models.CharField(help_text='Usuario para la conexión SSH', max_length=100)),
                ('contraseña', models.CharField(help_text='Contraseña del usuario SSH (guárdala de forma segura)', max_length=100)),
            ],
        ),
    ]
