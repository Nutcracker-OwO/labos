# admin.py
from django.contrib import admin
from .models import RolAnsible, Dominio, MaquinaVirtual, Laboratorio

admin.site.register(RolAnsible)
admin.site.register(Dominio)
admin.site.register(MaquinaVirtual)
admin.site.register(Laboratorio)
