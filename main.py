import streamlit as st
from openai import OpenAI

# Configuración inicial
st.title("Chatbot Personalizado")
openai_api_key = "tu_api_key_aquí"

# Configurar cliente OpenAI
client = OpenAI(api_key=openai_api_key)

# Inicializar estado de la sesión si es necesario
if "messages" not in st.session_state:
    st.session_state.messages = []

# Personalizar nombre del chatbot
bot_name = st.sidebar.text_input("Nombre del Chatbot", value="Asistente AI")

# Muestra los mensajes de la sesión
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada del usuario
prompt = st.chat_input("¿Qué deseas preguntar?")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        # Obtener la respuesta del modelo de OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=False
        )

        # Mostrar respuesta del asistente
        response_text = response['choices'][0]['message']['content']
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    except Exception as e:
        st.error(f"Ocurrió un error al procesar la solicitud: {e}")

