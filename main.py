import streamlit as st
import pandas as pd
from datetime import datetime
from groq import Groq
import os

# Título de la aplicación
st.title("BotRestaurant - 5 Star Michilini")

# Define la API Key directamente en el código
api_key = "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"

# Inicializamos el cliente de Groq con la API Key
client = Groq(api_key=api_key)

# Lista de modelos para elegir
modelos = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

# Cargar los menús desde archivos CSV
@st.cache_data
def cargar_menus():
    try:
        platos = pd.read_csv('menu_platos.csv')
        bebidas = pd.read_csv('menu_bebidas.csv')
        postres = pd.read_csv('menu_postres.csv')
        st.sidebar.write("Menú cargado:", platos.shape, bebidas.shape, postres.shape)
        return platos, bebidas, postres
    except FileNotFoundError:
        st.error("No se pudo encontrar uno de los archivos del menú.")
        return pd.DataFrame(columns=['Plato', 'Precio']), pd.DataFrame(columns=['Bebida', 'Precio']), pd.DataFrame(columns=['Postre', 'Precio'])

# Verificar si el pedido es válido (plato está en la carta)
def verificar_pedido(mensaje, menu_restaurante):
    productos_en_menu = menu_restaurante['Plato'].str.lower().tolist()
    for producto in productos_en_menu:
        if producto in mensaje.lower():
            return producto
    return None

# Verificar distrito de reparto
DISTRITOS_REPARTO = []

@st.cache_data
def cargar_distritos():
    try:
        distritos = pd.read_csv('distritos.csv')
        return distritos['Distrito'].tolist()
    except FileNotFoundError:
        st.error("No se pudo encontrar el archivo de distritos.")
        return []

DISTRITOS_REPARTO = cargar_distritos()

def verificar_distrito(mensaje):
    return next((distrito for distrito in DISTRITOS_REPARTO if distrito.lower() in mensaje.lower()), None)

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

# Mostrar campo de entrada de prompt (inicialización antes del uso)
prompt = st.chat_input("¿Qué quieres saber?")

# Cargar el menú
menu_platos, menu_bebidas, menu_postres = cargar_menus()

# Validación del prompt: no vacío y no demasiado largo
if prompt:
    if len(prompt) > 2000:
        st.error("El mensaje es demasiado largo. Por favor, acórtalo.")
    else:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Generando respuesta..."):
            try:
                if manejar_saludo(prompt):
                    respuesta = "¡Bienvenido a BotRestaurant, tu destino para saborear lo mejor de la comida asiática! ¿En qué puedo ayudarte? ¿Deseas ver el menú?"
                elif "menú" in prompt.lower() or "carta" in prompt.lower():
                    # Mostrar menú de platos inicialmente
                    if not st.session_state.carta_mostrada:
                        st.write("Aquí tienes el menú de los platos:")
                        st.write(menu_platos)
                        respuesta = "Aquí tienes el menú completo de platos. Si deseas, puedes ver el menú de bebidas o postres. ¿Cuál te gustaría ver?"
                        st.session_state.carta_mostrada = True
                    else:
                        respuesta = "Ya te mostré el menú de platos. ¿Te gustaría ver el menú de bebidas o postres?"
                elif "bebidas" in prompt.lower():
                    st.write("Aquí tienes el menú de bebidas:")
                    st.write(menu_bebidas)
                    respuesta = "Aquí está el menú de bebidas. ¿Te gustaría ver el menú de postres también?"
                elif "postres" in prompt.lower():
                    st.write("Aquí tienes el menú de postres:")
                    st.write(menu_postres)
                    respuesta = "Aquí está el menú de postres. ¿Te gustaría volver a ver el menú de platos o bebidas?"
                else:
                    pedido = verificar_pedido(prompt, menu_platos)
                    if pedido:
                        monto = menu_platos[menu_platos['Plato'].str.lower() == pedido]['Precio'].values
                        if monto:
                            monto = monto[0]
                            guardar_pedido(pedido, monto)
                            respuesta = f"¡Excelente elección! Has pedido {pedido} por ${monto}. ¿Deseas algo más?"
                        else:
                            respuesta = "Lo siento, ocurrió un error al procesar el precio del pedido."
                    else:
                        respuesta = "Lo siento, no entendí tu pedido. ¿Podrías repetirlo o pedir la carta para ver nuestras opciones?"

                distrito = verificar_distrito(prompt)
                if distrito:
                    respuesta += f" Y sí, repartimos en tu distrito: {distrito}."
                elif "reparto" in prompt.lower() or "entrega" in prompt.lower():
                    respuesta += " Lo siento, no repartimos en ese distrito. Nuestras zonas de reparto son: " + ", ".join(DISTRITOS_REPARTO)

                st.chat_message("assistant").markdown(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})

            except Exception as e:
                st.error(f"Hubo un error al procesar tu solicitud: {e}")
else:
    if "messages" not in st.session_state:
        st.chat_message("assistant").markdown("¡Bienvenido! ¿En qué puedo ayudarte hoy?")
        st.session_state.messages.append({"role": "assistant", "content": "¡Bienvenido! ¿En qué puedo ayudarte hoy?"})
    
