from django.urls import path
from .views import lista_laboratorios, agregar_laboratorio, guardar_laboratorio, crear_laboratorio, descargar_config, eliminar_laboratorio, crear_maquinas, eliminar_maquina_virtual, subir_configuracion, configurar_ssh, guardar_config_ssh, configurar_red, api_desplegar_laboratorio

urlpatterns = [
    path('', lista_laboratorios, name='lista_laboratorios'),  # Lista de laboratorios
    path('agregar_laboratorio/', agregar_laboratorio, name='agregar_laboratorio'),  # Crear nuevo laboratorio
    path('crear_maquinas/<int:laboratorio_id>/', crear_maquinas, name='crear_maquinas'),  # Crear máquinas virtuales
    path('configurar_red/<int:laboratorio_id>/', configurar_red, name='configurar_red'),
    path('guardar_laboratorio/', guardar_laboratorio, name='guardar_laboratorio'),  # Guardar laboratorio
    path('crear_laboratorio/', crear_laboratorio, name='crear_laboratorio'),  # Crear formulario
    path('eliminar_laboratorio/<int:id>/', eliminar_laboratorio, name='eliminar_laboratorio'),  # Eliminar laboratorio
    path('descargar_config/<int:id>/', descargar_config, name='descargar_config'),  # Descargar configuración
    path('eliminar_maquina_virtual/<int:id>/', eliminar_maquina_virtual, name='eliminar_maquina_virtual'),
    path('configurar_ssh/', configurar_ssh, name='configurar_ssh'),
    path('subir_configuracion/<int:laboratorio_id>/', subir_configuracion, name='subir_configuracion'),
    path('guardar_config_ssh/', guardar_config_ssh, name= 'guardar_config_ssh'),
    path('api/desplegar_laboratorio/<int:lab_id>/', api_desplegar_laboratorio, name='despliegue_laboratorio'),

] 
