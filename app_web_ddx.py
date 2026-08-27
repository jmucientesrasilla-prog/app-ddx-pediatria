import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="DDx Radiología Pediátrica",
    page_icon="👶",
    layout="centered"
)

SYSTEM_INSTRUCTIONS = """
Eres un experto Radiólogo Pediátrico adjunto de un hospital de tercer nivel.
Tu objetivo es ayudar a otro radiólogo a generar una lista de diagnósticos diferenciales (DDx) precisos y estructurados a partir de los datos clínicos y radiológicos que te proporcione.

REGLAS DE FORMATO ESTRICTAS:
1. Genera todo el contenido en formato Markdown estándar.
2. NO uses formato matemático LaTeX.
3. Sé directo, conciso y clínico. Evita introducciones largas.

ESTRUCTURA OBLIGATORIA DE TU RESPUESTA:
# 🧩 Diagnóstico Diferencial
## 1. RESUMEN CLÍNICO-RADIOLÓGICO
- Síntesis de 1-2 viñetas.
## 2. DIAGNÓSTICOS DIFERENCIALES PRINCIPALES
| Diagnóstico | Hallazgos clave | Demografía típica / Clínica |
## 3. DIAGNÓSTICOS ATÍPICOS
- Lista con viñetas.
## 4. 🚨 RED FLAGS / "NO-MISS DIAGNOSES"
- Diagnósticos críticos.
## 5. SIGUIENTE PASO RECOMENDADO (WORKUP)
- Prueba de imagen complementaria y recomendación.
## 6. REFERENCIAS
- 1 o 2 artículos clásicos de Radiographics/Pediatr Radiol.
"""

# ==========================================
# 2. INTERFAZ VISUAL WEB
# ==========================================
st.title("👶 Asistente DDx Pediátrico")
st.markdown("Generador de diagnósticos diferenciales basado en IA con literatura médica actualizada.")

# Cuadro de texto para introducir el caso
caso = st.text_area(
    "Introduce los datos del caso (Hallazgos, edad, técnica, clínica):",
    height=150,
    placeholder="Ej: Lactante de 8 meses con masa quística multiloculada en lóbulo inferior derecho..."
)

# ==========================================
# 3. LÓGICA DE GENERACIÓN
# ==========================================
if st.button("Generar Diagnósticos (DDx)", type="primary"):
    if not caso.strip():
        st.warning("Por favor, introduce los datos del caso.")
    else:
        with st.spinner("🧠 Analizando el caso y buscando literatura médica..."):
            try:
                # La API Key ahora se lee de los "secretos" de la web por seguridad
                API_KEY = st.secrets["GEMINI_API_KEY"]
                client = genai.Client(api_key=API_KEY)

                configuracion = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.3,
                )

                # Llamada al modelo PRO
                response = client.models.generate_content(
                    model="gemini-3.1-pro-preview",
                    contents=f"Genera el diagnóstico diferencial radiológico para este caso: {caso}",
                    config=configuracion,
                )

                st.success("¡Diagnóstico generado!")
                
                # Mostramos el resultado en la web
                st.markdown("---")
                st.markdown(response.text)
                st.markdown("---")
                
                # Botón para descargar como archivo .md si quieres guardarlo en Obsidian luego
                st.download_button(
                    label="📥 Descargar en formato Markdown (.md)",
                    data=response.text,
                    file_name="DDx_Pediatria.md",
                    mime="text/markdown"
                )

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")