import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Asistente DDx Pediátrico",
    page_icon="👶",
    layout="centered"
)

# ==========================================
# 2. SISTEMA DE CONTRASEÑA
# ==========================================
st.markdown("### 🔒 Acceso Privado")
clave_acceso = st.text_input("Introduce la contraseña para desbloquear la IA:", type="password")

if clave_acceso != st.secrets["PASSWORD_APP"]:
    st.info("App bloqueada. Introduce la clave correcta.")
    st.stop()

st.markdown("---")

# ==========================================
# 3. PROMPT MAESTRO
# ==========================================
SYSTEM_INSTRUCTIONS = """
Eres un experto Radiólogo Pediátrico adjunto de un hospital de tercer nivel.
Tu objetivo es ayudar a otro radiólogo a generar diagnósticos diferenciales (DDx) y responder dudas clínicas como si fuerais colegas consultando un caso.

REGLAS ESTRICTAS:
1. Usa formato Markdown. Cero formato matemático (LaTeX).
2. Sé directo, riguroso y clínico. 
3. Cuando el usuario te pase un caso nuevo inicial, genera OBLIGATORIAMENTE la estructura de 6 apartados (Resumen, DDx Principales en tabla, DDx Atípicos, Red Flags, Workup y Referencias).
4. Cuando el usuario te haga preguntas de seguimiento (durante el chat), responde de forma natural a la pregunta médica, razonando por qué sube o baja la probabilidad de un DDx según los nuevos datos que te dé.
"""

# ==========================================
# 4. GESTIÓN DE LA MEMORIA DEL CHAT
# ==========================================
# Si es la primera vez que se carga la página, creamos una lista vacía para guardar los mensajes
if "mensajes_chat" not in st.session_state:
    st.session_state.mensajes_chat = []

def reiniciar_caso():
    """Borra la memoria para empezar un caso desde cero."""
    st.session_state.mensajes_chat = []

# ==========================================
# 5. LÓGICA DE LA INTERFAZ
# ==========================================

# FASE A: PANTALLA INICIAL (Aún no hay caso)
if len(st.session_state.mensajes_chat) == 0:
    st.title("👶 Asistente DDx Pediátrico")
    st.markdown("Introduce los datos del caso inicial. Una vez analizado, podrás conversar con la IA para refinar el diagnóstico.")
    
    caso = st.text_area("Datos del caso (clínica, edad, hallazgos):", height=120)
    
    if st.button("Generar Diagnóstico Inicial", type="primary"):
        if caso.strip():
            with st.spinner("🧠 Analizando el caso y consultando literatura..."):
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                configuracion = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.3,
                )
                
                # Le damos la orden inicial
                prompt_inicial = f"Genera el diagnóstico diferencial radiológico para este caso: {caso}"
                response = client.models.generate_content(
                    model="gemini-3.1-pro-preview",
                    contents=prompt_inicial,
                    config=configuracion
                )
                
                # Guardamos lo que ha pasado en la memoria
                st.session_state.mensajes_chat.append({"role": "user", "mostrar": f"🩺 **Caso clínico inicial:**\n{caso}", "oculto": prompt_inicial})
                st.session_state.mensajes_chat.append({"role": "model", "mostrar": response.text, "oculto": response.text})
                
                # Recargamos la página para entrar en modo Chat
                st.rerun()
        else:
            st.warning("Introduce los datos del paciente.")

# FASE B: PANTALLA DE CHAT (Ya hay un caso cargado)
else:
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("💬 Sesión Clínica")
    with col2:
        # Botón para borrar todo y empezar un paciente nuevo
        st.button("🔄 Nuevo Paciente", on_click=reiniciar_caso)

    # 1. Pintamos en la pantalla toda la conversación guardada
    for msg in st.session_state.mensajes_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["mostrar"])

    # 2. Cuadro de chat tipo WhatsApp en la parte inferior
    nuevo_mensaje = st.chat_input("Ej: ¿Cambia el diagnóstico si te digo que hay reacción perióstica?")
    
    if nuevo_mensaje:
        # Lo mostramos en la pantalla inmediatamente
        st.session_state.mensajes_chat.append({"role": "user", "mostrar": nuevo_mensaje, "oculto": nuevo_mensaje})
        with st.chat_message("user"):
            st.markdown(nuevo_mensaje)
            
        # Lo enviamos a la IA junto con TODO el historial para que no pierda el contexto
        with st.chat_message("model"):
            with st.spinner("Pensando respuesta..."):
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                configuracion = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.3,
                )
                
                # Reconstruimos la memoria técnica para que Google sepa de qué hablábamos
                historial_tecnico = []
                for m in st.session_state.mensajes_chat[:-1]: # Metemos todo menos el mensaje que acabamos de poner
                    historial_tecnico.append(types.Content(role=m["role"], parts=[types.Part.from_text(text=m["oculto"])]))
                
                # Añadimos la pregunta nueva
                historial_tecnico.append(types.Content(role="user", parts=[types.Part.from_text(text=nuevo_mensaje)]))
                
                # Preguntamos
                response = client.models.generate_content(
                    model="gemini-3.1-pro-preview",
                    contents=historial_tecnico,
                    config=configuracion
                )
                
                # Pintamos la respuesta
                st.markdown(response.text)
                
        # Guardamos la respuesta de la IA en la memoria
        st.session_state.mensajes_chat.append({"role": "model", "mostrar": response.text, "oculto": response.text})
