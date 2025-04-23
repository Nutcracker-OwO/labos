from django.db import models
from django.conf import settings
import yaml
import os

class RolAnsible(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Dominio(models.Model):
    fqdn = models.CharField(max_length=255, unique=True)
    rol = models.CharField(max_length=50, choices=[
        ('controlador_primario', 'Controlador Primario'),
        ('miembro', 'Miembro del Dominio'),
    ])

    def __str__(self):
        return self.fqdn


class MaquinaVirtual(models.Model):
    TEMPLATES = [
        ('debian-11-x64-server-template ', 'Debian 11'),
        ('debian-12-x64-server-template ', 'Debian 12'),
        ('kali-x64-desktop-template  ', 'Kali Linux'),
        ('win11-22h2-x64-enterprise-template', 'Windows 11 (22H2 Enterprise)'),
        ('win2022-server-x64-template', 'Windows 2022 Server (x64)'),
        ('debian10-template', 'Debian 10'),
        ('rocky-9-x64-server-template', 'Rocky 9 (x64 Server)'),
        ('ubuntu-20.04-x64-server-template', 'Ubuntu 20.04 (x64 Server)'),
        ('ubuntu-22.04-x64-server-template', 'Ubuntu 22.04 (x64 Server)'),
        ('win10-21h1-x64-enterprise-template', 'Windows 10 (21H1 Enterprise)'),
        ('win11-23h2-x64-enterprise-template', 'Windows 11 (23H2 Enterprise)'),
        ('win2012r2-server-x64-template', 'Windows 2012 R2 Server (x64)'),
        ('win2016-server-x64-template', 'Windows 2016 Server (x64)'),
        ('win2019-server-x64-template', 'Windows 2019 Server (x64)'),
        ('commando-vm-template', 'Commando VM (requires ansible role: badsectorlabs.ludus_commandovm)'),
        ('flare-vm-template', 'Flare VM (requires ansible role: badsectorlabs.ludus_flarevm)'),
        ('remnux-template', 'Remnux (requires ansible role: badsectorlabs.ludus_remnux)')
    ]

    ROLES_ANSIBLE = [
        ('badsectorlabs.ludus_vulhub', 'Runs Vulhub environments on a Linux system.'),
        ('badsectorlabs.ludus_adcs', 'Installs ADCS on Windows Server and optionally configures Certified Preowned templates.'),
        ('badsectorlabs.ludus_bloodhound_ce', 'Installs Bloodhound CE on a Debian based system.'),
        ('badsectorlabs.ludus_mssql', 'Installs MSSQL on Windows systems.'),
        ('badsectorlabs.ludus_elastic_container', 'Installs "The Elastic Container Project" on a Linux system.'),
        ('badsectorlabs.ludus_elastic_agent', 'Installs an Elastic Agent on a Windows, Debian, or Ubuntu system'),
        ('badsectorlabs.ludus_xz_backdoor', 'Installs the xz backdoor (CVE-2024-3094) on a Debian host and optionally installs the xzbot tool.'),
        ('badsectorlabs.ludus_commandovm', 'Sets up Commando VM on Windows >= 10 hosts'),
        ('badsectorlabs.ludus_flarevm', 'Installs Flare VM on Windows >= 10 hosts'),
        ('badsectorlabs.ludus_remnux', 'Installs REMnux on Ubuntu 20.04 systems'),
        ('badsectorlabs.ludus_emux', 'Installs EMUX and runs an emulated device on Debian based hosts'),
        ('aleemladha.wazuh_server_install', 'Install Wazuh SIEM Unified XDR and SIEM protection with SOC Fortress Rules'),
        ('aleemladha.ludus_wazuh_agent', 'Deploys Wazuh Agents to Windows systems'),
        ('aleemladha.ludus_exchange', 'Installs Microsoft Exchange Server on a Windows Server host'),
        ('ludus_child_domain', 'Create a child domain and domain controller because ansible\'s microsoft.ad doesn\'t support it'),
        ('ludus_child_domain_join', 'Join a machine to the child domain created from ludus_child_domain'),
        ('ludus-local-users', 'Manages local users and groups for Windows or Linux'),
        ('ludus-gitlab-ce', 'Handles the installation of a Gitlab instance'),
        ('ludus-ad-content', 'Creates content in an Active Directory (OUs, Groups, Users)'),
        ('ludus_tailscale', 'Provision or remove a device to/from a Tailnet'),
        ('ludus_velociraptor_client', 'Install a Velociraptor Agent on a System in Ludus'),
        ('ludus_velociraptor_server', 'Install a Velociraptor Server in Ludus'),
        ('bagelByt3s.ludus_adfs', 'Installs an ADFS deployment with optional configurations.'),
        ('ludus_caldera_server', 'Installs Caldera Server main branch on linux'),
        ('ludus_caldera_agent', 'Installs Caldera Agent on Windows'),
        ('ludus_aurora_agent', 'Installs Aurora Agent on Windows'),
        ('ludus_graylog_server', 'Installs Graylog server on Ubuntu 22.04'),
        ('0xRedpoll.ludus_cobaltstrike_teamserver', 'Install and provision a Cobalt Strike teamserver in Ludus'),
        ('0xRedpoll.ludus_mythic_teamserver', 'Installs and spins up a Mythic Teamserver on a Debian or Ubuntu server'),
        ('ludus-ad-vulns', 'Adds vulnerabilities in an Active Directory.'),
        ('ludus_juiceshop', 'Installs OWASP Juice Shop')
    ]

    nombre_vm = models.CharField(max_length=100)
    hostname = models.CharField(max_length=100)
    plantilla = models.CharField(max_length=100, choices=TEMPLATES)
    vlan = models.IntegerField()
    ip_ultimo_octeto = models.IntegerField()
    ram_gb = models.IntegerField(default=4)
    cpus = models.IntegerField(default=2)
    sistema_operativo = models.CharField(max_length=50, choices=[
        ('windows', 'Windows'),
        ('linux', 'Linux'),
        ('macos', 'MacOS'),
    ])
    dominio = models.ForeignKey(Dominio, on_delete=models.SET_NULL, null=True, blank=True)
    roles = models.ManyToManyField(RolAnsible, blank=True, null= True)
    roles_ansible = models.TextField(blank=True, null=True)  # Almacenará los roles en formato YAML
    # Relación con el laboratorio
    laboratorio = models.ForeignKey('Laboratorio', null=True, blank=True, on_delete=models.SET_NULL, related_name='maquinas')  # Añadir related_name


    def set_roles(self, roles):
        if isinstance(roles, list):
            self.roles_ansible = yaml.safe_dump(roles, default_flow_style=True)
        else:
            self.roles_ansible = yaml.safe_dump([], default_flow_style=True)


    def get_roles(self):
        if not self.roles_ansible:
            return []
        try:
            return yaml.safe_load(self.roles_ansible) or []  # Devolver una lista vacía si la carga falla
        except Exception:
            return []  # En caso de error, devolvemos una lista vacía


    
    def __str__(self):
        return self.nombre_vm

class SSHConfiguracion(models.Model):
    host = models.CharField(max_length=255, help_text="IP o nombre del servidor SSH")
    usuario = models.CharField(max_length=100, help_text="Usuario para la conexión SSH")
    contraseña = models.CharField(max_length=100, help_text="Contraseña del usuario SSH (guárdala de forma segura)")

    def __str__(self):
        return f"{self.usuario}@{self.host}"
    
from django.db import models

class ReglaRed(models.Model):
    name = models.CharField(max_length=100)
    vlan_src = models.IntegerField()
    vlan_dst = models.IntegerField()
    protocolo = models.CharField(max_length=10, choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP'), ('all', 'All')])
    ports = models.CharField(max_length=50)
    action = models.CharField(max_length=10, choices=[('ACCEPT', 'ACCEPT'), ('REJECT', 'REJECT'), ('DROP', 'DROP')])

    def __str__(self):
        return self.name

class ConfiguracionRed(models.Model):
    laboratorio = models.OneToOneField("Laboratorio", on_delete=models.CASCADE)
    inter_vlan_default = models.CharField(max_length=10, default="REJECT")
    external_default = models.CharField(max_length=10, default="ACCEPT")
    always_blocked_networks = models.JSONField(default=list, blank=True, null=True) 
    rules = models.JSONField(default=list, blank=True, null=True)

class Laboratorio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    maquinas_virtuales = models.ManyToManyField('MaquinaVirtual', blank=True, related_name='laboratorios')  # Añadir related_name
    configuracion = models.FileField(upload_to='configuraciones/', null=True, blank=True)
    reglas_red = models.ManyToManyField(ReglaRed, related_name='laboratorios', blank=True)

    def __str__(self):
        return self.nombre
    
class LaboratorioPreset(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    # Otros campos relevantes

    def __str__(self):
        return self.nombre

    
