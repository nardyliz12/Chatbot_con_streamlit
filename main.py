import streamlit as st
import pandas as pd
from datetime import datetime
import os
from groq import Groq
from typing import Generator

# Título de la aplicación
st.title("ChatMang - Comida Asiática")

# Define la API Key directamente en el código
api_key = "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"

# Inicializamos el cliente de Groq con la API Key
client = Groq(api_key=api_key)

# Lista de modelos para elegir
modelos = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

# Función para generar respuestas del chat carácter por carácter
def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Cargar los menús desde varios archivos CSV
@st.cache_data
def cargar_menus():
    try:
        platos = pd.read_csv('menu_platos.csv')
        bebidas = pd.read_csv('menu_bebidas.csv')
        postres = pd.read_csv('menu_postres.csv')
        menu_completo = pd.concat([platos, bebidas, postres], ignore_index=True)
        st.sidebar.write("Menú cargado:", menu_completo.shape)
        return menu_completo
    except FileNotFoundError as e:
        st.error(f"No se pudo encontrar un archivo del menú. Error: {e}")
        return pd.DataFrame(columns=['Producto', 'Precio'])

# Cargar distritos de reparto desde un archivo CSV
@st.cache_data
def cargar_distritos():
    try:
        distritos = pd.read_csv('distritos')['Distrito'].tolist()
        st.sidebar.write("Distritos de reparto cargados:", len(distritos))
        return distritos
    except FileNotFoundError:
        st.error("No se pudo encontrar el archivo de distritos de reparto")
        return []

# Verificar si el pedido es válido (producto está en la carta)
def verificar_pedido(mensaje, menu_completo):
    productos_en_menu = menu_completo['Producto'].str.lower().tolist()
    for producto in productos_en_menu:
        if producto in mensaje.lower():
            return producto
    return None

# Verificar si el distrito está en la lista de distritos de reparto
def verificar_distrito(mensaje, distritos_reparto):
    return next((distrito for distrito in distritos_reparto if distrito.lower() in mensaje.lower()), None)

# Guardar pedido con timestamp y monto
def guardar_pedido(pedido, monto):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_pedido = pd.DataFrame([[timestamp, pedido, monto]], columns=['Timestamp', 'Pedido', 'Monto'])
    
    if not os.path.exists('pedidos.csv'):
        nuevo_pedido.to_csv('pedidos.csv', index=False)
    else:
        nuevo_pedido.to_csv('pedidos.csv', mode='a', header=False, index=False)

# Función para manejar saludos
def manejar_saludo(mensaje):
    saludos = ["hola", "buenas", "saludos"]
    return any(saludo in mensaje.lower() for saludo in saludos)

# Inicializamos el historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.carta_mostrada = False

# Manejo de cambios de modelo
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
    st.session_state.carta_mostrada = False

# Mostrar mensajes de chat desde el historial
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Mostrar campo de entrada de prompt
prompt = st.chat_input("¿Qué quieres saber?")

# Cargar los menús y distritos
menu_completo = cargar_menus()
distritos_reparto = cargar_distritos()

# Validación del prompt: no vacío y no demasiado largo
if prompt:
    if len(prompt) > 2000:
        st.error("El mensaje es demasiado largo. Por favor, acórtalo.")
    else:
        # Mostrar mensaje de usuario en el contenedor de mensajes de chat
        st.chat_message("user").markdown(prompt)
        # Agregar mensaje de usuario al historial de chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Indicador de carga mientras se genera la respuesta
        with st.spinner("Generando respuesta..."):
            try:
                # Mostrar el menú si el usuario menciona "menú" o "carta" en su mensaje
                if manejar_saludo(prompt):
                    respuesta = "¡Hola! Bienvenido a nuestro restaurante. ¿En qué puedo ayudarte? Puedes pedir nuestra carta si deseas ver el menú."
                elif "menú" in prompt.lower() or "carta" in prompt.lower():
                    if not st.session_state.carta_mostrada:
                        st.write("Aquí tienes el menú del restaurante:")
                        st.write(menu_completo)
                        respuesta = "Aquí tienes el menú completo. ¿Qué te gustaría ordenar?"
                        st.session_state.carta_mostrada = True
                    else:
                        respuesta = "Ya te mostré el menú. ¿Te gustaría pedir algo?"
                else:
                    pedido = verificar_pedido(prompt, menu_completo)
                    if pedido:
                        # Busca el precio del pedido
                        monto = menu_completo[menu_completo['Producto'].str.lower() == pedido]['Precio'].values
                        if monto:
                            monto = monto[0]
                            guardar_pedido(pedido, monto)
                            respuesta = f"¡Excelente elección! Has pedido {pedido} por ${monto}. ¿Deseas algo más?"
                        else:
                            respuesta = "Lo siento, ocurrió un error al procesar el precio del pedido."
                    else:
                        respuesta = "Lo siento, no entendí tu pedido. ¿Podrías repetirlo o pedir la carta para ver nuestras opciones?"

                # Verificar si se menciona un distrito válido para el reparto
                distrito = verificar_distrito(prompt, distritos_reparto)
                if distrito:
                    respuesta += f" Y sí, repartimos en tu distrito: {distrito}."
                elif "reparto" in prompt.lower() or "entrega" in prompt.lower():
                    respuesta += " Lo siento, no repartimos en ese distrito. Nuestras zonas de reparto son: " + ", ".join(distritos_reparto)

                # Mostrar respuesta del asistente
                st.chat_message("assistant").markdown(respuesta)
                # Agregar respuesta del asistente al historial de chat
                st.session_state.messages.append({"role": "assistant", "content": respuesta})

            except Exception as e:
                st.error(f"Hubo un error al procesar tu solicitud: {e}")
else:
    if "messages" not in st.session_state:
        st.chat_message("assistant").markdown("¡Bienvenido! ¿En qué puedo ayudarte hoy?")
        st.session_state.messages.append({"role": "assistant", "content": "¡Bienvenido! ¿En qué puedo ayudarte hoy?"})

