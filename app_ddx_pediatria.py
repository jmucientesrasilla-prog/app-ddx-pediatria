import os
import re
import sys
import time
import threading
import urllib.parse
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk
from google import genai
from google.genai import types

# ==========================================
# 1. CONFIGURACIÓN E INSTRUCCIONES
# ==========================================

API_KEY = "AQ.Ab8RN6KcX2WGmFx8tHZIJjHIWaEE7qNhp7G02EFB8uAp2gE5sQ"  # <-- PEGA TU API KEY AQUÍ
client = genai.Client(api_key=API_KEY)

SYSTEM_INSTRUCTIONS = """
Eres un experto Radiólogo Pediátrico adjunto de un hospital de tercer nivel.
Tu objetivo es ayudar a otro radiólogo a generar una lista de diagnósticos diferenciales (DDx) precisos y estructurados a partir de los datos clínicos y radiológicos que te proporcione.

REGLAS DE FORMATO ESTRICTAS:
1. Genera todo el contenido en formato Markdown estándar (sin código LaTeX).
2. Usa tablas y negritas para facilitar la lectura rápida en pantalla.
3. Sé directo, conciso y clínico. Evita introducciones largas.

ESTRUCTURA OBLIGATORIA DE TU RESPUESTA:

# 🧩 Diagnóstico Diferencial: [Breve resumen del caso en 4-5 palabras]

## 1. RESUMEN CLÍNICO-RADIOLÓGICO
- Síntesis de 1-2 viñetas con los hallazgos clave y la edad (factor crítico en pediatría).

## 2. DIAGNÓSTICOS DIFERENCIALES PRINCIPALES (Los más probables)
Crea una tabla con 3 columnas:
| Diagnóstico | Hallazgos radiológicos clave para confirmarlo/descartarlo | Demografía típica / Clínica |

## 3. DIAGNÓSTICOS MENOS FRECUENTES / ATÍPICOS
- Lista con viñetas de patologías más raras pero compatibles, indicando brevemente por qué considerarlas.

## 4. 🚨 RED FLAGS / "NO-MISS DIAGNOSES"
- Diagnósticos críticos que no se pueden pasar por alto (ej. Maltrato infantil / Lesiones no accidentales, tumores malignos, torsión, apendicitis, emergencias neuroquirúrgicas, etc.).
- Indica qué signo radiológico específico descartaría o confirmaría esta urgencia.

## 5. SIGUIENTE PASO RECOMENDADO (WORKUP)
- ¿Qué prueba de imagen complementaria harías? (ej. RM con contraste, Eco Doppler, serie ósea).
- ¿Qué recomendación clínica sugerirías en el informe? (ej. Correlación con laboratorios, biopsia, seguimiento en X semanas).

## 6. REFERENCIAS (Perlas de Radiographics / Pediatr Radiol)
- Menciona 1 o 2 artículos o conceptos clásicos de la literatura radiológica relevantes para este caso.
"""

# ==========================================
# 2. GENERADOR DE ARCHIVO Y CONEXIÓN A OBSIDIAN
# ==========================================

def guardar_y_abrir_markdown(markdown_texto, caso_resumido, ruta_salida):
    """Guarda el texto en .md y fuerza a Obsidian a abrirlo."""
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(markdown_texto)
    
    nombre_boveda = os.path.basename(os.path.dirname(ruta_salida)) 
    nombre_archivo = os.path.basename(ruta_salida) 
    
    vault_codificado = urllib.parse.quote(nombre_boveda)
    file_codificado = urllib.parse.quote(nombre_archivo)
    
    url_obsidian = f"obsidian://open?vault={vault_codificado}&file={file_codificado}"
    
    try:
        webbrowser.open(url_obsidian)
    except:
        os.startfile(os.path.dirname(ruta_salida))

# ==========================================
# 3. INTERFAZ GRÁFICA Y LÓGICA DE LA IA
# ==========================================

def iniciar_generacion():
    # En un tk.Text, se obtiene desde la línea 1, carácter 0 hasta el final
    caso = entrada_tema.get("1.0", tk.END).strip()
    if not caso:
        messagebox.showwarning("Campo vacío", "Por favor, introduce los datos del caso.")
        return

    btn_generar.config(state="disabled")
    barra_progreso.start(10)
    lbl_estado.config(text="Pensando diagnósticos diferenciales...", fg="#184c78")

    def tarea():
        try:
            configuracion = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTIONS,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3, # Punto dulce para DDx clínico
            )

            # Usamos el modelo PRO
            response = client.models.generate_content(
                model="gemini-3.1-pro-preview",
                contents=f"Genera el diagnóstico diferencial radiológico para este caso: {caso}",
                config=configuracion,
            )

            # --- RUTA DINÁMICA PORTÁTIL ---
            if getattr(sys, 'frozen', False):
                carpeta_base = os.path.dirname(sys.executable)
            else:
                carpeta_base = os.path.dirname(os.path.abspath(__file__))
            
            titulo_archivo = caso.replace("\n", " ")[:45]
            nombre_limpio = re.sub(r'[\\/*?:"<>|]', "", titulo_archivo).strip()
            
            ruta_archivo = os.path.join(carpeta_base, f"DDx_Pediatria - {nombre_limpio}.md")

            guardar_y_abrir_markdown(response.text, caso, ruta_archivo)

            lbl_estado.config(text=f"¡Diagnósticos generados con éxito!", fg="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al generar:\n{e}")
            lbl_estado.config(text="Error al generar. Revisa la consola.", fg="red")
        finally:
            barra_progreso.stop()
            btn_generar.config(state="normal")

    threading.Thread(target=tarea, daemon=True).start()

# ==========================================
# 4. INTERFAZ VISUAL
# ==========================================
ventana = tk.Tk()
ventana.title("Asistente DDx - Radiología Pediátrica")
ventana.geometry("580x350") 
ventana.resizable(False, False)
ventana.configure(padx=20, pady=20)

tk.Label(
    ventana,
    text="Buscador de Diagnósticos Diferenciales (DDx)",
    font=("Segoe UI", 13, "bold"),
    fg="#184c78",
).pack(anchor="w")

tk.Label(
    ventana,
    text="Introduce hallazgos, edad, técnica (Rx, Eco, RM) y clínica:",
    font=("Segoe UI", 10),
).pack(anchor="w", pady=(5, 5))

entrada_tema = tk.Text(ventana, font=("Segoe UI", 10), width=65, height=5)
entrada_tema.pack(fill="x", pady=5)
entrada_tema.insert("1.0", "Lactante 8 meses con masa quística multiloculada en lóbulo inferior pulmonar derecho en radiografía. Asintomático.") 
entrada_tema.focus()

barra_progreso = ttk.Progressbar(ventana, mode="indeterminate")
barra_progreso.pack(fill="x", pady=(15, 5))

lbl_estado = tk.Label(ventana, text="Listo para analizar el caso.", font=("Segoe UI", 9, "italic"))
lbl_estado.pack(anchor="w")

btn_generar = tk.Button(
    ventana,
    text=" Obtener Diagnósticos (DDx)",
    font=("Segoe UI", 11, "bold"),
    bg="#184c78",
    fg="white",
    activebackground="#0f304e",
    activeforeground="white",
    cursor="hand2",
    command=iniciar_generacion,
)
btn_generar.pack(fill="x", pady=(10, 0))

ventana.mainloop()