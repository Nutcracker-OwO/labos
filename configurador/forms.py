from django import forms
from .models import MaquinaVirtual, Dominio, RolAnsible, Laboratorio, SSHConfiguracion, ConfiguracionRed, ReglaRed, LaboratorioPreset

# Opciones de roles en español
ROLES_ANSIBLE_OPCIONES = [
    ('badsectorlabs.ludus_vulhub', 'Ejecuta entornos Vulhub en un sistema Linux'),
    ('badsectorlabs.ludus_adcs', 'Instala ADCS en Windows Server y configura plantillas Certified Preowned opcionales'),
    ('badsectorlabs.ludus_bloodhound_ce', 'Instala Bloodhound CE en un sistema basado en Debian'),
    ('badsectorlabs.ludus_mssql', 'Instala MSSQL en sistemas Windows'),
    ('badsectorlabs.ludus_elastic_container', 'Instala "The Elastic Container Project" en un sistema Linux'),
    ('badsectorlabs.ludus_elastic_agent', 'Instala un agente de Elastic en un sistema Windows, Debian o Ubuntu'),
    ('badsectorlabs.ludus_xz_backdoor', 'Instala la puerta trasera xz (CVE-2024-3094) en un host Debian y opcionalmente instala la herramienta xzbot'),
    ('badsectorlabs.ludus_commandovm', 'Configura Commando VM en hosts Windows >= 10'),
    ('badsectorlabs.ludus_flarevm', 'Instala Flare VM en hosts Windows >= 10'),
    ('badsectorlabs.ludus_remnux', 'Instala REMnux en sistemas Ubuntu 20.04'),
    ('badsectorlabs.ludus_emux', 'Instala EMUX y ejecuta un dispositivo emulado en hosts basados en Debian'),
    ('aleemladha.wazuh_server_install', 'Instala Wazuh SIEM Unified XDR y protección SIEM con reglas SOC Fortress'),
    ('aleemladha.ludus_wazuh_agent', 'Despliega agentes de Wazuh en sistemas Windows'),
    ('aleemladha.ludus_exchange', 'Instala Microsoft Exchange Server en un host Windows Server'),
    ('ludus_child_domain', 'Crea un dominio hijo y controlador de dominio'),
    ('ludus_child_domain_join', 'Une una máquina al dominio hijo creado desde ludus_child_domain'),
    ('ludus-local-users', 'Gestiona usuarios y grupos locales para Windows o Linux'),
    ('ludus-gitlab-ce', 'Instala una instancia de Gitlab'),
    ('ludus-ad-content', 'Crea contenido en un Active Directory (OUs, Grupos, Usuarios)'),
    ('ludus_tailscale', 'Provisiona o elimina un dispositivo de/from un Tailnet'),
    ('ludus_velociraptor_client', 'Instala un agente Velociraptor en un sistema'),
    ('ludus_velociraptor_server', 'Instala un servidor Velociraptor'),
    ('bagelByt3s.ludus_adfs', 'Instala un despliegue ADFS con configuraciones opcionales'),
    ('ludus_caldera_server', 'Instala el servidor Caldera en Linux'),
    ('ludus_caldera_agent', 'Instala un agente Caldera en Windows'),
    ('ludus_aurora_agent', 'Instala un agente Aurora en Windows (requiere paquete y licencia válidos)'),
    ('ludus_graylog_server', 'Instala un servidor Graylog en Ubuntu 22.04'),
    ('0xRedpoll.ludus_cobaltstrike_teamserver', 'Instala y provisiona un servidor Cobalt Strike'),
    ('0xRedpoll.ludus_mythic_teamserver', 'Instala y ejecuta un servidor Mythic en un servidor Debian o Ubuntu'),
    ('ludus-ad-vulns', 'Añade vulnerabilidades en un Active Directory'),
    ('ludus_juiceshop', 'Instala OWASP Juice Shop'),
]

# Formulario para el laboratorio
class LaboratorioForm(forms.ModelForm):
    class Meta:
        model = Laboratorio
        fields = ['nombre', 'descripcion']

class MaquinaVirtualForm(forms.ModelForm):
    # Campo para seleccionar múltiples roles de Ansible
    #roles = forms.ModelMultipleChoiceField(
    #    queryset=ROLES_ANSIBLE_OPCIONES.objects.all(), 
    #    required=False,  # Permite no seleccionar roles
    #    widget=forms.CheckboxSelectMultiple
    #)

    # Campo para elegir un solo rol de Ansible
    roles_ansible = forms.MultipleChoiceField(
        choices=ROLES_ANSIBLE_OPCIONES,
        widget=forms.CheckboxSelectMultiple,  # Permite selección múltiple con checkboxes
        required=False,
        label="Roles Ansible"
    )
    # roles_ansible = forms.MultipleChoiceField(choices=RolAnsible.ROLES_ANSIBLE, widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = MaquinaVirtual
        exclude = ['roles', 'laboratorio']  # No incluimos el campo laboratorio

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs and kwargs['instance']:
            self.initial['roles_ansible'] = kwargs['instance'].get_roles()

class DominioForm(forms.ModelForm):
    class Meta:
        model = Dominio
        fields = '__all__'

class SSHConfiguracionForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = SSHConfiguracion
        fields = ['host', 'usuario', 'contraseña']

class ReglaRedForm(forms.ModelForm):
    class Meta:
        model = ReglaRed
        fields = ['name', 'vlan_src', 'vlan_dst', 'protocolo', 'ports', 'action']

class ConfiguracionRedForm(forms.ModelForm):
    inter_vlan_default = forms.ChoiceField(choices=[('REJECT', 'REJECT'), ('ACCEPT', 'ACCEPT')], initial='REJECT')
    external_default = forms.ChoiceField(choices=[('REJECT', 'REJECT'), ('ACCEPT', 'ACCEPT')], initial='ACCEPT')
    always_blocked_networks = forms.CharField(required=False, widget=forms.Textarea)

    # Este campo permite agregar múltiples reglas
    rules = forms.CharField(required=True, widget=forms.Textarea)

    class Meta:
        model = ConfiguracionRed
        fields = ['inter_vlan_default', 'external_default', 'always_blocked_networks', 'rules']

def cargar_laboratorio_predeterminado(laboratorio_id):
    laboratorio_preset = LaboratorioPreset.objects.get(id=laboratorio_id)
    with open(laboratorio_preset.get_archivo(), 'r') as f:
        configuracion = f.read()
    # Aquí puedes usar esta configuración para crear un nuevo laboratorio
    # De acuerdo a cómo lo quieras implementar en tu código