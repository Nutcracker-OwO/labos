
from .models import MaquinaVirtual, Dominio, Laboratorio, SSHConfiguracion, ConfiguracionRed, LaboratorioPreset
from .forms import MaquinaVirtualForm, DominioForm, LaboratorioForm, SSHConfiguracionForm, ReglaRedForm, ConfiguracionRedForm
from .utils import generar_configuracion, subir_archivo_ssh, ejecutar_pasos_despliegue
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import modelformset_factory
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.storage import default_storage
import json
import yaml
import os

CONFIG_SSH_PATH = "media/configuraciones/config_ssh.json"

# Vista para crear máquinas virtuales asociadas al laboratorio
def crear_maquinas(request, laboratorio_id):
    laboratorio = get_object_or_404(Laboratorio, id=laboratorio_id)

    if request.method == 'POST':
        # Recibimos los datos de las máquinas virtuales
        form = MaquinaVirtualForm(request.POST)
        if form.is_valid():
            maquina_virtual = form.save(commit= False)  # Guardamos la máquina virtual
            maquina_virtual.save()
            
            laboratorio.maquinas_virtuales.add(maquina_virtual)  # Asociamos la máquina virtual al laboratorio

            # Ahora generamos la configuración del laboratorio
            generar_configuracion(laboratorio.id)

            return redirect('crear_maquinas', laboratorio_id=laboratorio.id)  # Redirigimos a agregar más máquinas
    else:
        form = MaquinaVirtualForm()

    return render(request, 'configurador/crear_maquina.html', {'form': form, 'laboratorio': laboratorio}) 

def eliminar_maquina_virtual(request, id):
    if request.method == "POST":
        # Obtener la máquina virtual a eliminar
        maquina = get_object_or_404(MaquinaVirtual, id=id)
        
        # Obtener el laboratorio al que pertenece la máquina virtual
        laboratorio = maquina.laboratorio  # Esto debería funcionar, ya que cada máquina virtual tiene un laboratorio asignado
        
        # Eliminar la máquina virtual
        maquina.delete()
        
        # Redirigir al usuario a la página de agregar máquinas virtuales del laboratorio correspondiente
        return redirect('crear_maquinas', laboratorio_id=laboratorio.id)
    
    # Si no es POST, redirigir o devolver un error
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def lista_dominios(request):
    dominios = Dominio.objects.all()
    return render(request, 'configurador/lista_dominios.html', {'dominios': dominios})

def agregar_dominio(request):
    if request.method == "POST":
        form = DominioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_dominios')
    else:
        form = DominioForm()
    return render(request, 'configurador/agregar_dominio.html', {'form': form})

def lista_laboratorios(request):
    # Obtener todos los laboratorios creados por el usuario
    laboratorios_creados = Laboratorio.objects.all()

    # Laboratorios predeterminados
    preset_dir = os.path.join(settings.MEDIA_ROOT, 'presets')
    laboratorios_predeterminados = []

    # Añadir la descripción a cada laboratorio creado por el usuario
    for laboratorio in laboratorios_creados:
        archivo_descripcion = os.path.join(settings.MEDIA_ROOT, 'configuraciones', f'configuracion_{laboratorio.id}.json')
        if os.path.exists(archivo_descripcion):
            try:
                with open(archivo_descripcion, 'r') as file:
                    config_data = json.load(file)
                    laboratorio.descripcion = config_data.get('descripcion_lab', 'Descripción no disponible')
            except Exception as e:
                print(f"Error al leer el archivo de descripción: {e}")
                laboratorio.descripcion = 'Descripción no disponible'
        else:
            laboratorio.descripcion = 'Archivo de descripción no encontrado'

    if os.path.exists(preset_dir):
        for archivo in os.listdir(preset_dir):
            if archivo.startswith("laboratorio_") and archivo.endswith(".json"):
                ruta_json = os.path.join(preset_dir, archivo)
                try:
                    with open(ruta_json, 'r') as f:
                        data = json.load(f)
                        nombre_lab = data.get('nombre_lab', 'Laboratorio sin nombre')
                        descripcion = data.get('descripcion_lab', 'Descripción no disponible')
                        
                        # Intentar localizar el archivo de configuración .yml
                        base_name = archivo.replace("laboratorio_", "").replace(".json", "")
                        config_file = f"{base_name}-config.yml"
                        config_path = os.path.join(preset_dir, config_file)
                        
                        if os.path.exists(config_path):
                            config_file_url = os.path.join('media/presset', config_file)
                        else:
                            config_file_url = None

                        laboratorios_predeterminados.append({
                            'nombre': nombre_lab,
                            'descripcion': descripcion,
                            'config_file_url': config_file_url,
                            'upload_url': f"/subir_configuracion_predeterminada/{base_name}/",  # Debes crear esta vista
                        })
                except Exception as e:
                    print(f"Error al leer el laboratorio predeterminado {archivo}: {e}")

    return render(request, 'configurador/lista_laboratorios.html', {
        'laboratorios_creados': laboratorios_creados,
        'laboratorios_predeterminados': laboratorios_predeterminados
    })

# Vista para agregar un laboratorio
def agregar_laboratorio(request):
    if request.method == 'POST':
        form = LaboratorioForm(request.POST)
        if form.is_valid():
            laboratorio = form.save()  # Guardamos el laboratorio
            # Crear el archivo de configuración del laboratorio
            crear_archivo_laboratorio(laboratorio)
            return redirect('crear_maquinas', laboratorio_id=laboratorio.id)  # Redirigimos a la vista de máquinas virtuales
    else:
        form = LaboratorioForm()
    return render(request, 'configurador/agregar_laboratorio.html', {'form': form})

def crear_archivo_laboratorio(laboratorio):
    # Definir el nombre del archivo de configuración en formato JSON
    archivo_nombre = f"configuracion_{laboratorio.id}.json"
    archivo_ruta = os.path.join(settings.MEDIA_ROOT, 'configuraciones', archivo_nombre)

    # Crear el directorio si no existe
    os.makedirs(os.path.dirname(archivo_ruta), exist_ok=True)

    # Crear el contenido del archivo JSON
    contenido = {
        "nombre_lab": laboratorio.nombre,
        "descripcion_lab": laboratorio.descripcion
    }

    # Escribir el contenido en el archivo JSON
    with open(archivo_ruta, 'w') as archivo:
        json.dump(contenido, archivo, indent=4)

    # Asignar la ruta del archivo de configuración al laboratorio
    laboratorio.configuracion = archivo_ruta
    laboratorio.save()

def crear_laboratorio(request):
    if request.method == 'POST':
        laboratorio_form = LaboratorioForm(request.POST)
        MaquinaVirtualFormSet = modelformset_factory(MaquinaVirtual, form=MaquinaVirtualForm, extra=1)  # Formset para máquinas virtuales
        formset = MaquinaVirtualFormSet(request.POST)
        
        if laboratorio_form.is_valid() and formset.is_valid():
            # Crear el laboratorio
            laboratorio = laboratorio_form.save()

            # Guardar o actualizar las máquinas virtuales
            for form in formset:
                maquina = form.save(commit=False)
                if maquina.id:  # Si la máquina tiene un ID, es una actualización
                    maquina.save()  # Guardamos los cambios de la máquina virtual
                else:
                    # Si la máquina no tiene ID, es una nueva máquina, así que la asociamos al laboratorio
                    maquina.laboratorio = laboratorio
                    maquina.save()
            
            return redirect('lista_laboratorios')  # Redirigir a la lista de laboratorios
    else:
        laboratorio_form = LaboratorioForm()
        MaquinaVirtualFormSet = modelformset_factory(MaquinaVirtual, form=MaquinaVirtualForm, extra=1)
        formset = MaquinaVirtualFormSet(queryset=MaquinaVirtual.objects.none())  # No cargamos máquinas virtuales de momento
    
    return render(request, 'configurador/crear_laboratorio.html', {
        'laboratorio_form': laboratorio_form,
        'formset': formset,
    })

@csrf_exempt
def guardar_laboratorio(request):
    if request.method == "POST":
        data = json.loads(request.body)

        nombre_lab = data.get("nombreLab")
        descripcion_lab = data.get("descripcionLab")
        vms_ids = data.get("vms", [])

        # Crear el laboratorio en la base de datos
        laboratorio = Laboratorio.objects.create(
            nombre=nombre_lab,
            descripcion=descripcion_lab
        )

        # Asociar máquinas virtuales
        maquinas = MaquinaVirtual.objects.filter(id__in=vms_ids)
        for vm in maquinas:
            vm.laboratorio = laboratorio
            vm.save()

        # Guardar en YAML
        lab_info = {
            "id": laboratorio.id,
            "nombre": laboratorio.nombre,
            "descripcion": laboratorio.descripcion,
        }

        filename = f"laboratorio_info_{laboratorio.id}.yml"
        with open(filename, "w") as file:
            yaml.dump(lab_info, file, default_flow_style=False, allow_unicode=True)

        return JsonResponse({"mensaje": "Laboratorio guardado", "id": laboratorio.id})

    return JsonResponse({"error": "Método no permitido"}, status=405)

def eliminar_laboratorio(request, id):
    # Obtener el laboratorio a eliminar
    laboratorio = get_object_or_404(Laboratorio, id=id)

    # Eliminar el archivo de descripción (configuracion_{laboratorio.id}.json)
    archivo_descripcion = os.path.join(settings.MEDIA_ROOT, 'configuraciones', f'configuracion_{laboratorio.id}.json')
    try:
        if os.path.exists(archivo_descripcion):
            os.remove(archivo_descripcion)
            print(f"Archivo de descripción {archivo_descripcion} eliminado correctamente.")
    except Exception as e:
        print(f"Error al eliminar el archivo de descripción: {e}")

    # Eliminar el archivo de configuración real (laboratorio-config-{laboratorio.id}.yml)
    archivo_configuracion = os.path.join(settings.MEDIA_ROOT, 'configuraciones', f'laboratorio-config-{laboratorio.id}.yml')
    try:
        if os.path.exists(archivo_configuracion):
            os.remove(archivo_configuracion)
            print(f"Archivo de configuración {archivo_configuracion} eliminado correctamente.")
    except Exception as e:
        print(f"Error al eliminar el archivo de configuración: {e}")

    # Eliminar el laboratorio
    laboratorio.delete()

    # Redirigir a la lista de laboratorios
    return redirect('lista_laboratorios')

def descargar_config(request, id):
    """
    Vista para descargar el archivo de configuración de un laboratorio.
    """
    laboratorio = get_object_or_404(Laboratorio, id=id)

    # Verificar si el laboratorio tiene un archivo de configuración
    if not laboratorio.configuracion:
        return JsonResponse({"error": "El archivo de configuración no existe para este laboratorio."}, status=404)

    # Construir la ruta completa del archivo
    archivo_config_path = laboratorio.configuracion.path

    # Verificar si el archivo existe
    if os.path.exists(archivo_config_path):
        # Abrir el archivo y enviarlo como respuesta para su descarga
        with open(archivo_config_path, 'r') as file:
            response = HttpResponse(file.read(), content_type='application/x-yaml')
            response['Content-Disposition'] = f'attachment; filename="configuracion_{laboratorio.id}.yml"'
            return response
    else:
        return JsonResponse({"error": "Archivo no encontrado"}, status=404)
    
def configurar_ssh(request):
    configuracion = SSHConfiguracion.objects.first()  # Tomar la primera configuración si ya existe

    if request.method == "POST":
        form = SSHConfiguracionForm(request.POST, instance=configuracion)
        if form.is_valid():
            form.save()
            return redirect('lista_laboratorios')  # Redirigir a la lista de laboratorios
    else:
        form = SSHConfiguracionForm(instance=configuracion)

    return render(request, 'configurador/configurar_ssh.html', {'form': form})

def guardar_config_ssh(request):
    if request.method == 'POST':
        host = request.POST.get('host')
        usuario = request.POST.get('usuario')
        password = request.POST.get('password')

        if host and usuario and password:
            config_ssh = {
                "host": host,
                "usuario": usuario,
                "password": password
            }

        try:
            with open(CONFIG_SSH_PATH, "w") as file:
                json.dump(config_ssh, file, indent= 4)

            messages.success(request, "Configuración SSH guardad correctamente.")
            return redirect('lista_laboratorios')
        except Exception as e:
            messages.error(request, f"Error al guardar configuración: {e}")

    else:
        messages.error(request, "Todos los campos obligatorios")

    return redirect('configurar.ssh')

def subir_configuracion(request, laboratorio_id):
    print("subiendo archivo")
    archivo_local = f"media/configuraciones/laboratorio-config-{laboratorio_id}.yml"

    if not os.path.exists(archivo_local):
        messages.error(request, "El archivo de configuracion no existe")
        return redirect('lista_laboratorios')
    
    resultado = subir_archivo_ssh(archivo_local, f"laboratorio-config-{laboratorio_id}.yml")

    if "Error" in resultado:
        messages.error(request, resultado)
    else:
        messages.success(request, resultado)

    return redirect('lista_laboratorios')

def configurar_red(request, laboratorio_id):
    laboratorio = get_object_or_404(Laboratorio, id=laboratorio_id)

    # Obtener las reglas de red existentes asociadas al laboratorio
    reglas_existentes = laboratorio.reglas_red.all()

    if request.method == 'POST':
        # Procesamos el formulario
        form = ReglaRedForm(request.POST)
        if form.is_valid():
            # Si el formulario es válido, guardamos la nueva regla
            regla_red = form.save(commit=False)
            regla_red.save()  # Guardamos la nueva regla

            # Asociamos la nueva regla al laboratorio
            laboratorio.reglas_red.add(regla_red)
            messages.success(request, "Regla de red agregada correctamente.")
            return redirect('configurar_red', laboratorio_id=laboratorio.id)  # Redirigimos para seguir agregando reglas

    else:
        form = ReglaRedForm()  # Formulario vacío para una nueva regla

    return render(request, 'configurador/configurar_red.html', {
        'form': form,
        'laboratorio': laboratorio,
        'reglas_existentes': reglas_existentes
    })

def laboratorios_predeterminados(request):
    # Obtener los laboratorios predeterminados activos
    laboratorios = LaboratorioPreset.objects.filter(activo=True)
    
    return render(request, 'laboratorios_predeterminados.html', {'laboratorios': laboratorios})

def api_desplegar_laboratorio(request, lab_id):
    if request.method == "GET":
        resultados = ejecutar_pasos_despliegue(lab_id)
        return JsonResponse(resultados, safe=False)
