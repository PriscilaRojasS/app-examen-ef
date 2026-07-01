import streamlit as st
import os
import pymongo
import google.generativeai as genai
import cohere
import PyPDF2

# ============================================================
# CONFIGURACIÓN — lee todo desde variables de entorno
# NUNCA van las claves directas en el código
# ============================================================
MONGODB_URI = os.environ.get("MONGODB_URI")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
USER = os.environ.get("USER", "Priscila Rojas")

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Buscador de PDFs :)",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Plataforma de búsqueda y analítica de PDFs - priscilita")
st.markdown(f"**Usuario:** {USER}")
st.markdown("---")

# ============================================================
# CONEXIÓN A MONGODB
# ============================================================
def get_db():
    if not MONGODB_URI:
        st.error("❌ MONGODB_URI no configurada")
        st.stop()
    client = pymongo.MongoClient(MONGODB_URI)
    return client["pdf_platform"]

# ============================================================
# CONFIGURAR GEMINI
# ============================================================
def get_gemini():
    if not GEMINI_API_KEY:
        st.error("❌ GEMINI_API_KEY no configurada")
        st.stop()
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-pro")

# ============================================================
# CONFIGURAR COHERE
# ============================================================
def get_cohere():
    if not COHERE_API_KEY:
        st.error("❌ COHERE_API_KEY no configurada")
        st.stop()
    return cohere.Client(COHERE_API_KEY)

# ============================================================
# SECCIÓN 1: SUBIR PDF
# ============================================================
st.header("📤 Subir documento PDF")

uploaded_file = st.file_uploader(
    "Selecciona un PDF",
    type=["pdf"]
)

if uploaded_file:
    # Extraer texto del PDF
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    texto = ""
    for page in pdf_reader.pages:
        texto += page.extract_text()

    st.success(f"✅ PDF cargado: {uploaded_file.name}")
    st.info(f"📊 Páginas: {len(pdf_reader.pages)} | Caracteres: {len(texto)}")

    # Guardar en MongoDB
    db = get_db()
    coleccion = db["documentos"]
    doc = {
        "nombre": uploaded_file.name,
        "texto": texto,
        "paginas": len(pdf_reader.pages),
        "usuario": USER
    }
    resultado = coleccion.insert_one(doc)
    st.success(f"✅ Guardado en MongoDB con ID: {resultado.inserted_id}")

    # Mostrar preview del texto
    with st.expander("Ver texto extraído"):
        st.write(texto[:1000] + "..." if len(texto) > 1000 else texto)

# ============================================================
# SECCIÓN 2: CHATBOT CON GEMINI
# ============================================================
st.markdown("---")
st.header("🤖 Chatbot — Pregunta sobre el documento")

pregunta = st.text_input("Escribe tu pregunta:")

if st.button("Preguntar a Gemini") and pregunta:
    if not uploaded_file:
        st.warning("⚠️ Primero sube un PDF")
    else:
        with st.spinner("Consultando Gemini..."):
            modelo = get_gemini()
            prompt = f"""
            Basándote en este documento:
            {texto[:3000]}

            Responde esta pregunta:
            {pregunta}
            """
            respuesta = modelo.generate_content(prompt)
            st.markdown("**Respuesta de Gemini:**")
            st.write(respuesta.text)

            # Guardar consulta en MongoDB
            db = get_db()
            db["consultas"].insert_one({
                "pregunta": pregunta,
                "respuesta": respuesta.text,
                "documento": uploaded_file.name,
                "usuario": USER
            })

# ============================================================
# SECCIÓN 3: VER DOCUMENTOS GUARDADOS
# ============================================================
st.markdown("---")
st.header("📋 Documentos guardados en MongoDB")

if st.button("Cargar documentos"):
    db = get_db()
    docs = list(db["documentos"].find())
    if docs:
        for doc in docs:
            st.write(f"📄 **{doc['nombre']}** | Páginas: {doc['paginas']} | Usuario: {doc['usuario']}")
    else:
        st.info("No hay documentos guardados aún")
