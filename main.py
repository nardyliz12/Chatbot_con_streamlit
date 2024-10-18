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
    st.session_state.menu_actual = None  # Agregamos para manejar qué menú se está mostrando

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
    st.session_state.menu_actual = None  # Reiniciar también la selección del menú

# Mostrar mensajes de chat desde el historial
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Mostrar campo de entrada de prompt
prompt = st.chat_input("¿Qué quieres saber?")

# Cargar el menú
menu_platos, menu_bebidas, menu_postres = cargar_menus()

# Función para mostrar el menú
def mostrar_menu(tipo):
    if tipo == 'platos':
        st.write("Menú de Platos:")
        st.write(menu_platos)
    elif tipo == 'bebidas':
        st.write("Menú de Bebidas:")
        st.write(menu_bebidas)
    elif tipo == 'postres':
        st.write("Menú de Postres:")
        st.write(menu_postres)

# Validación del prompt
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Generando respuesta..."):
        try:
            # Manejar saludo
            if manejar_saludo(prompt):
                respuesta = "¡Bienvenido a BotRestaurant! ¿Deseas ver el menú? Tenemos platos, bebidas y postres."
                st.session_state.menu_actual = None

            # Mostrar menú según la solicitud
            elif any(palabra in prompt.lower() for palabra in ["menú", "carta"]):  # Reconocer "menú" o "carta"
                if "platos" in prompt.lower():
                    mostrar_menu('platos')
                    respuesta = "Aquí está el menú de platos. Si deseas ver bebidas o postres, por favor indícalo."
                    st.session_state.menu_actual = 'platos'
                elif "bebidas" in prompt.lower():
                    mostrar_menu('bebidas')
                    respuesta = "Aquí está el menú de bebidas. Si deseas ver platos o postres, por favor indícalo."
                    st.session_state.menu_actual = 'bebidas'
                elif "postres" in prompt.lower():
                    mostrar_menu('postres')
                    respuesta = "Aquí está el menú de postres. Si deseas ver platos o bebidas, por favor indícalo."
                    st.session_state.menu_actual = 'postres'
                else:
                    if st.session_state.menu_actual == 'platos':
                        mostrar_menu('platos')
                    elif st.session_state.menu_actual == 'bebidas':
                        mostrar_menu('bebidas')
                    elif st.session_state.menu_actual == 'postres':
                        mostrar_menu('postres')
                    respuesta = "Te mostré el último menú que pediste. Si quieres cambiar, puedes pedirme platos, bebidas o postres."

            # Procesar pedidos
            else:
                pedido = verificar_pedido(prompt, menu_platos)
                if pedido:
                    monto = menu_platos[menu_platos['Plato'].str.lower() == pedido]['Precio'].values
                    if monto:
                        monto = monto[0]
                        guardar_pedido(pedido, monto)
                        respuesta = f"¡Has pedido {pedido} por ${monto}. ¿Deseas algo más?"
                    else:
                        respuesta = "Ocurrió un error con el precio de tu pedido."
                else:
                    respuesta = "Lo siento, no entendí tu pedido. ¿Podrías repetirlo o pedir la carta para ver nuestras opciones?"

            distrito = verificar_distrito(prompt)
            if distrito:
                respuesta += f" Repartimos en {distrito}."
            elif "reparto" en prompt.lower() or "entrega" in prompt.lower():
                respuesta += f" No repartimos en esa zona. Zonas de reparto: {', '.join(DISTRITOS_REPARTO)}."

            st.chat_message("assistant").markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})

        except Exception as e:
            st.error(f"Hubo un error al procesar tu solicitud: {e}")
