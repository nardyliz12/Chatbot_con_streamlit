import streamlit as st
import time
from groq import Groq
from typing import Generator

st.title("ChatMang")

# Declaramos el cliente de Groq
client = Groq(
    api_key=st.secrets["ngroqAPIKey"],  # Cargamos la API key del .streamlit/secrets.toml
)

# Lista de modelos para elegir
modelos = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

def generate_chat_responses(chat_completion) -> Generator[str, None, None]:   
    """Generated Chat Responses
       Genera respuestas de chat a partir de la información de completado de chat, mostrando caracter por caracter.

       Args: chat_completion (str): La información de completado de chat.

       Yields: str: Cada respuesta generada. 
    """ 
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Inicializamos el historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Manejo de cambios de modelo: reiniciar historial si el modelo cambia
if "selected_model" not in st.session_state:
    st.session_state.selected_model = modelos[0]

parModelo = st.sidebar.selectbox('Modelos', options=modelos, index=modelos.index(st.session_state.selected_model))

# Si el modelo cambia, reinicia el historial
if parModelo != st.session_state.selected_model:
    st.session_state.selected_model = parModelo
    st.session_state.messages = []  # Limpiar el historial de chat al cambiar de modelo

# Botón para reiniciar el chat
if st.sidebar.button("Reiniciar chat"):
    st.session_state.messages = []

# Mostrar mensajes de chat desde el historial
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Mostrar campo de entrada de prompt
prompt = st.chat_input("¿Qué quieres saber?")

# Validación del prompt: no vacío y no demasiado largo
if prompt and len(prompt) > 0:
    if len(prompt) > 2000:  # Limitar el largo del prompt
        st.error("El mensaje es demasiado largo. Por favor, acórtalo.")
    else:
        # Mostrar mensaje de usuario en el contenedor de mensajes de chat
        st.chat_message("user").markdown(prompt)
        # Agregar mensaje de usuario al historial de chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Indicador de carga mientras se genera la respuesta
        with st.spinner("Generando respuesta..."):
            try:
                chat_completion = client.chat.completions.create(
                    model=parModelo,
                    messages=[
                        {
                            "role": m["role"],
                            "content": m["content"]
                        }
                        for m in st.session_state.messages
                    ],  # Entregamos el historial de los mensajes
                    stream=True
                )

                # Mostrar respuesta del asistente en el contenedor de mensajes de chat
                with st.chat_message("assistant"):            
                    chat_responses_generator = generate_chat_responses(chat_completion)
                    # Usamos st.write_stream para simular escritura
                    full_response = st.write_stream(chat_responses_generator)

                # Agregar respuesta del asistente al historial de chat
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Hubo un error al generar la respuesta: {e}")
else:
    if prompt and len(prompt) == 0:
        st.error("Por favor, ingresa un mensaje.")
