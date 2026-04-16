import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# --- CONFIGURACIÓN DE CONEXIÓN (SECRETS) ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="CRM Automotriz", layout="wide")

# --- FUNCIONES DE AYUDA ---
def get_vendedores():
    res = supabase.table("vendedores").select("*").execute()
    return res.data

def get_contactos_pendientes():
    res = supabase.table("contactos").eq("estado", "Pendiente").execute()
    return res.data

# --- INTERFAZ ---
st.sidebar.title("Gestión Comercial")
menu = st.sidebar.radio("Módulos", [
    "1. Call Center (Captura)", 
    "2. Confirmación (24hs)", 
    "3. Agenda Vendedor", 
    "4. Post-Venta (48hs)",
    "5. Reportería"
])

# --- MÓDULO 1: CALL CENTER ---
if menu == "1. Call Center (Captura)":
    st.header("📞 Captura de Prospectos")
    
    with st.form("form_contacto"):
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre")
            apellido = st.text_input("Apellido")
            email = st.text_input("Email")
            domicilio = st.text_input("Domicilio")
        with c2:
            modelo = st.text_input("Modelo Auto Actual")
            anio = st.number_input("Año", min_value=1900, max_value=2026, value=2018)
            km = st.number_input("Kilometraje", min_value=0)
            interes = st.selectbox("¿Interesa propuesta?", ["Pendiente", "Si", "No"])

        st.divider()
        st.subheader("Agendar Cita (Si aplica)")
        vendedores = get_vendedores()
        dict_vend = {v['nombre']: v['id'] for v in vendedores}
        vendedor_sel = st.selectbox("Asignar Vendedor", list(dict_vend.keys()))
        fecha = st.date_input("Fecha Cita")
        hora = st.time_input("Hora Cita")

        if st.form_submit_button("Registrar Gestión"):
            # 1. Insertar Contacto
            new_contact = {
                "nombre": nombre, "apellido": apellido, "email": email, 
                "domicilio": domicilio, "auto_actual_modelo": modelo,
                "auto_actual_anio": anio, "auto_actual_km": km,
                "estado": "Agendado" if interes == "Si" else "No Interesa"
            }
            contact_res = supabase.table("contactos").insert(new_contact).execute()
            
            # 2. Si agendó, crear turno
            if interes == "Si" and contact_res.data:
                c_id = contact_res.data[0]['id']
                dt_cita = datetime.datetime.combine(fecha, hora).isoformat()
                supabase.table("turnos").insert({
                    "contacto_id": c_id,
                    "vendedor_id": dict_vend[vendedor_sel],
                    "fecha_hora": dt_cita
                }).execute()
                st.success("Cita agendada correctamente.")

# --- MÓDULO 2: CONFIRMACIÓN 24HS ---
elif menu == "2. Confirmación (24hs)":
    st.header("⏳ Bandeja de Confirmación (Mañana)")
    manana = datetime.date.today() + datetime.timedelta(days=1)
    
    # Consulta turnos de mañana que no han sido confirmados
    res = supabase.table("turnos")\
        .select("*, contactos(nombre, apellido, telefono)")\
        .gte("fecha_hora", manana.isoformat())\
        .lt("fecha_hora", (manana + datetime.timedelta(days=1)).isoformat())\
        .execute()
    
    if res.data:
        df = pd.json_normalize(res.data)
        st.table(df[['contactos.nombre', 'contactos.apellido', 'fecha_hora', 'estado_turno']])
        # Aquí podrías agregar botones para marcar como "Confirmado" o "Reprogramar"
    else:
        st.write("No hay citas para confirmar mañana.")

# --- MÓDULO 3: AGENDA VENDEDOR ---
elif menu == "3. Agenda Vendedor":
    st.header("🚗 Gestión de Piso (Vendedores)")
    # El vendedor selecciona su nombre para ver su agenda
    vendedores = get_vendedores()
    v_sel = st.selectbox("Seleccione su nombre", [v['nombre'] for v in vendedores])
    
    st.subheader(f"Citas pendientes para {v_sel}")
    # Aquí filtraríamos por el ID del vendedor y estado_turno != 'Asistio'
    st.info("Aquí el vendedor marca: Vino / No vino y el resultado de la venta.")

# --- MÓDULO 4: POST-VENTA (48HS) ---
elif menu == "4. Post-Venta (48hs)":
    st.header("🔄 Seguimiento y Calidad")
    tab1, tab2 = st.tabs(["Recuperación (No Asistieron)", "Encuesta Satisfacción"])
    
    with tab1:
        st.write("Contactar para re-agendar a quienes faltaron hace 48hs.")
    with tab2:
        st.write("Llamar para encuesta de satisfacción a quienes asistieron.")

# --- MÓDULO 5: REPORTERÍA ---
elif menu == "5. Reportería":
    st.header("📈 Indicadores de Gestión")
    # Ejemplo de métrica simple
    st.metric("Total Contactos", "3500", "+12%")
