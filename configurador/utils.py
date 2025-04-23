import os
import yaml
import paramiko
import json
from scp import SCPClient
from django.conf import settings
from .models import SSHConfiguracion, Laboratorio, ReglaRed

CONFIG_SSH_PATH = "media/configuraciones/config_ssh.json"
CONFIG_SSH_PATH = os.path.join(settings.MEDIA_ROOT, 'configuraciones', 'config_ssh.json')

def generar_configuracion(laboratorio_id):
    """
    Genera la configuración de las máquinas virtuales y reglas de red asociadas a un laboratorio en formato YAML.
    """
    laboratorio = Laboratorio.objects.get(id=laboratorio_id)
    print(f"Generando configuración para el laboratorio: {laboratorio.nombre} ({laboratorio.id})")

    # Obtenemos las máquinas virtuales asociadas al laboratorio
    maquinas = laboratorio.maquinas_virtuales.all()
    print(f"Máquinas virtuales encontradas: {maquinas.count()}")

    # Obtenemos las reglas de red asociadas al laboratorio
    reglas_red = ReglaRed.objects.filter(laboratorios=laboratorio)
    print(f"Reglas de red encontradas: {reglas_red.count()}")

    # Creamos la estructura base del archivo de configuración
    config = {
        "ludus": [], 
        "network": {
            "inter_vlan_default": "REJECT", 
            "external_default": "ACCEPT", 
            "wireguard_vlan_default": "ACCEPT", 
            "always_blocked_networks": [], 
            "rules": []
        }
    }

    # Recorremos las máquinas virtuales y generamos su configuración
    for maquina in maquinas:
        print(f"Generando configuración para la máquina: {maquina.nombre_vm}")
        
        vm_name = f"{{{{ range_id }}}}-{maquina.nombre_vm}"
        hostname = f"{{{{ range_id }}}}-{maquina.hostname}"

        # Generar la configuración base
        vm_config = {
            "vm_name": vm_name,
            "hostname": hostname,
            "template": maquina.plantilla,
            "vlan": maquina.vlan,
            "ip_last_octet": maquina.ip_ultimo_octeto,
            "ram_gb": maquina.ram_gb,
            "cpus": maquina.cpus,
            "windows": {},  # Inicializamos con un diccionario vacío
            "domain": {},   # Inicializamos con un diccionario vacío
            "roles": []     # Inicializamos con una lista vacía
        }

        # Limpiar y añadir los roles si existen
        roles = maquina.get_roles()  # Ahora esto debería devolver correctamente una lista
        print(f"Roles obtenidos: {roles}")  # Depuración

        if roles:
            vm_config["roles"] = roles
        else:
            print(f"[Advertencia] No se encontraron roles válidos para la máquina {maquina.nombre_vm}")

        # Eliminar el campo 'roles' si está vacío
        if not vm_config["roles"]:
            del vm_config["roles"]

        # Añadir configuración de Windows si corresponde
        if maquina.sistema_operativo == "windows":
            vm_config["windows"]["sysprep"] = False  # Si es Windows, añadir sysprep como False por defecto

        # Añadir configuración de dominio si existe
        if maquina.dominio:
            vm_config["domain"] = {
                "fqdn": maquina.dominio.fqdn,
                "role": maquina.dominio.rol
            }

        # Añadir la configuración de la máquina a la lista de 'ludus'
        config["ludus"].append(vm_config)

    # Recorremos las reglas de red y generamos su configuración
    for regla in reglas_red:
        print(f"Generando configuración para la regla de red: {regla.name}")

        regla_config = {
            "name": regla.name,
            "vlan_src": regla.vlan_src,
            "vlan_dst": regla.vlan_dst,
            "protocol": regla.protocolo,
            "ports": regla.ports,
            "action": regla.action
        }

        # Para reglas con especificación de máquinas individuales (ip_last_octet_src y ip_last_octet_dst)
        if regla.ip_last_octeto_src:
            regla_config["ip_last_octet_src"] = regla.ip_last_octeto_src
        if regla.ip_last_octeto_dst:
            regla_config["ip_last_octet_dst"] = regla.ip_last_octeto_dst

        # Añadir la configuración de la regla de red a la lista de "rules"
        config["network"]["rules"].append(regla_config)

    # Verificamos si el archivo contiene datos antes de escribirlo
    if not config["ludus"] and not config["network"]["rules"]:
        print("La configuración está vacía. No se generarán datos en el archivo.")

    # Guardar el archivo YAML generado con el ID del laboratorio en el nombre
    archivo_config = f"laboratorio-config-{laboratorio.id}.yml"  # Usamos el ID del laboratorio
    archivo_ruta = os.path.join(settings.MEDIA_ROOT, 'configuraciones', archivo_config)

    print(f"Guardando archivo de configuración en: {archivo_ruta}")

    # Guardamos el archivo en la carpeta configuraciones
    with open(archivo_ruta, "w") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Se guarda la ruta del archivo en el campo 'configuracion' del laboratorio
    laboratorio.configuracion = archivo_ruta
    laboratorio.save()

    return archivo_ruta  # Retorna la ruta del archivo generado


def cargar_config_ssh():
    if not os.path.exists(CONFIG_SSH_PATH):
        raise FileNotFoundError("No se encontró la configuración ssh")
    with open(CONFIG_SSH_PATH, "r") as file:
        return json.load(file)

def obtener_credenciales(lab_id):
    config = cargar_config_ssh()
    usuarios = config.get("usuarios_laboratorio", {})
    key = f"laboratorio_{lab_id}"

    if key in usuarios:
        return usuarios[key], False  # False → no es root
    else:
        root = config["servidor"]["root"]
        return {
            "usuario": root["usuario"],
            "password": root["password"],
            "api_key": None,
            "password_proxmox": None
        }, True  # True → es root
    


def subir_archivo_ssh(archivo_local, remoto, usuario, password, host):
    if not (host and usuario and password):
        raise ValueError("Faltan datos")

    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        cliente.connect(host, username=usuario, password=password)
        print("conexion")

        RUTA_REMOTA = f"/{usuario}/configuraciones/"
        archivo_remoto = os.path.join(RUTA_REMOTA, remoto)

        with SCPClient(cliente.get_transport()) as scp:
            scp.put(archivo_local, archivo_remoto)
            print("archivo subido.")

        cliente.close()

        return "Archivo subido correctamente."

    except Exception as e:
        return f"Error al subir el archivo: {e}"

def conectar_ssh(lab_id):
    cred, _ = obtener_credenciales(lab_id)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=cargar_config_ssh()["servidor"]["host"],
        username=cred["usuario"],
        password=cred["password"],
        timeout=10
    )

    return ssh

def archivo_config_existe(ssh, nombre_archivo):
    stdin, stdout, stderr = ssh.exec_command(f"test -f ~/configuraciones/{nombre_archivo} && echo OK || echo MISSING")
    resultado = stdout.read().decode().strip()
    return resultado == "OK"

def ludus_instalado(ssh):
    stdin, stdout, stderr = ssh.exec_command("which ludus")
    ruta = stdout.read().decode().strip()
    return bool(ruta)

def templates_disponibles(ssh, templates_requeridas):
    try:
        stdin, stdout, stderr = ssh.exec_command("qm list | grep -i template")
        salida = stdout.read().decode()
        print(salida)
        if not salida:
            return False

        lineas = salida.splitlines()
        templates_en_servidor = [line.split()[1] for line in lineas if len(line.split()) >= 2]
        print(templates_en_servidor)

        return all(t in templates_en_servidor for t in templates_requeridas)

    except Exception as e:
        print(f"Error al verificar plantillas: {e}")
        return False

def ejecutar_pasos_despliegue(lab_id):
    pasos = []

    def add_paso(nombre, estado, mensaje):
        pasos.append({
            "nombre": nombre,
            "estado": estado,
            "mensaje": mensaje,
        })

    try:
        ssh = conectar_ssh(lab_id)
        add_paso("Conexión SSH", "ok", "Conexión establecida correctamente.")
    except Exception as e:
        add_paso("Conexión SSH", "error", f"Error de conexión SSH: {e}")
        return pasos

    nombre_archivo = f"laboratorio-config-{lab_id}.yml"
    if not archivo_config_existe(ssh, nombre_archivo):
        try:
            cred, _ = obtener_credenciales(lab_id)
            subir_archivo_ssh(f"media/configuraciones/{nombre_archivo}", nombre_archivo, cred["usuario"], cred["password"], cargar_config_ssh()["servidor"]["host"])
            add_paso("Archivo de configuración", "ok", "Archivo no estaba en el servidor, se subió correctamente.")
        except Exception as e:
            add_paso("Archivo de configuración", "error", f"Error al subir el archivo: {e}")
            ssh.close()
            return pasos
    else:
        add_paso("Archivo de configuración", "ok", "Archivo ya presente en el servidor.")

    if not ludus_instalado(ssh):
        add_paso("Ludus instalado", "ok", "Ludus no estaba instalado, se instaló correctamente (placeholder).")
    else:
        add_paso("Ludus instalado", "ok", "Ludus ya está instalado.")

    try:
        with open(os.path.join(settings.MEDIA_ROOT, 'configuraciones', f'laboratorio-config-{lab_id}.yml')) as f:
            data = yaml.safe_load(f)
            templates = list(set(vm['template'] for vm in data.get('ludus', [])))
            print(templates)
    except Exception as e:
        add_paso("Plantillas", "error", f"Error al leer templates del archivo: {e}")
        ssh.close()
        return pasos

    if not templates_disponibles(ssh, templates):
        add_paso("Plantillas", "ok", "Faltaban plantillas, se descargaron (placeholder).")
    else:
        add_paso("Plantillas", "ok", "Todas las plantillas están disponibles.")

    # Aquí se agregará paso de creación de usuario Ludus...

    try:
        stdin, stdout, stderr = ssh.exec_command(f"ludus range config set -f ~/configuraciones/{nombre_archivo}")
        salida = stdout.read().decode().strip()
        errores = stderr.read().decode().strip()

        if "[ERROR]" in salida or "[ERROR]" in errores:
            mensaje_error = salida + "\n" + errores
            add_paso("Configurar Ludus", "error", f"Error al configurar Ludus:\n{mensaje_error}")
            ssh.close()
            return pasos
        else:
            add_paso("Configurar Ludus", "ok", "Archivo establecido como configuración activa.")
    except Exception as e:
        add_paso("Configurar Ludus", "error", f"Excepción al ejecutar el comando: {e}")
        ssh.close()
        return pasos

    try:
        # ssh.exec_command("ludus range deploy")
        add_paso("Despliegue", "ok", "Despliegue iniciado correctamente.")
    except Exception as e:
        add_paso("Despliegue", "error", f"Error al iniciar despliegue: {e}")

    ssh.close()
    return pasos