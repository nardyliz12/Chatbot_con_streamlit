import os
import streamlit as st
import pandas as pd
from datetime import datetime
from groq import Groq
from typing import Generator

# Título de la aplicación
st.title("ChatMang - Chatbot de Restaurante")

# Declaramos el cliente de Groq con la API Key desde el archivo .streamlit/secrets.toml
client = Groq(api_key=st.secrets["APIKey_Groq"])

# Lista de modelos para elegir
modelos = ['llama3-8b-8192']

# Función para generar respuestas del chat carácter por carácter
def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Cargar el menú desde un archivo CSV
def cargar_menu():
    return pd.read_csv('menu_restaurante.csv')

# Verificar si el pedido es válido (plato está en la carta)
def verificar_pedido(mensaje, menu_restaurante):
    productos_en_menu = menu_restaurante['Plato'].str.lower().tolist()
    for producto in productos_en_menu:
        if producto in mensaje.lower():
            return True
    return False

# Verificar distrito de reparto
DISTRITOS_REPARTO = ["Distrito1", "Distrito2", "Distrito3"]

def verificar_distrito(mensaje):
    for distrito in DISTRITOS_REPARTO:
        if distrito.lower() in mensaje.lower():
            return distrito
    return None

# Guardar pedido con timestamp y monto
def guardar_pedido(pedido, monto):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_pedido = pd.DataFrame([[timestamp, pedido, monto]], columns=['Timestamp', 'Pedido', 'Monto'])
    
    if not os.path.exists('pedidos.csv'):
        nuevo_pedido.to_csv('pedidos.csv', index=False)
    else:
        nuevo_pedido.to_csv('pedidos.csv', mode='a', header=False, index=False)

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
    st.session_state.messages = []

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
                # Verificar si el usuario pidió la carta o el menú
                if "carta" in prompt.lower() or "menú" in prompt.lower():
                    # Mostrar menú solo cuando se solicita
                    menu = cargar_menu()
                    st.write("Aquí está la carta del restaurante:")
                    st.dataframe(menu)

                # Verificar si el pedido es válido
                elif verificar_pedido(prompt, cargar_menu()):
                    chat_completion = client.chat.completions.create(
                        model=parModelo,
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                        stream=True
                    )

                    # Mostrar respuesta del asistente en el contenedor de mensajes de chat
                    with st.chat_message("assistant"):            
                        chat_responses_generator = generate_chat_responses(chat_completion)
                        # Simular escritura de la respuesta
                        full_response = st.write_stream(chat_responses_generator)

                    # Agregar respuesta del asistente al historial de chat
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                    # Guardar pedido
                    pedido = prompt.lower()
                    item = cargar_menu()[cargar_menu()['Plato'].str.lower() == pedido]['Plato'].values[0]
                    monto = cargar_menu()[cargar_menu()['Plato'].str.lower() == pedido]['Precio'].values[0]
                    guardar_pedido(item, monto)

                else:
                    st.error("El plato solicitado no está en el menú. Por favor revisa la carta.")

                # Verificar si se menciona un distrito válido para el reparto
                distrito = verificar_distrito(prompt)
                if distrito:
                    st.write(f"Repartimos en tu distrito: {distrito}")
                else:
                    st.write("Lo siento, no repartimos en ese distrito.")

            except Exception as e:
                st.error(f"Hubo un error al generar la respuesta: {e}")
else:
    if prompt and len(prompt) == 0:
        st.error("Por favor, ingresa un mensaje.")
