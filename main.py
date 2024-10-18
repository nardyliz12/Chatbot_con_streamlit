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
    menus = {}
    for menu_type in ['platos', 'bebidas', 'postres']:
        try:
            menus[menu_type] = pd.read_csv(f'menu_{menu_type}.csv')
        except FileNotFoundError:
            st.error(f"No se pudo encontrar el archivo del menú de {menu_type}.")
            menus[menu_type] = pd.DataFrame(columns=['Item', 'Precio'])
    return menus

# Verificar si el pedido es válido (item está en la carta)
def verificar_pedido(mensaje, menus):
    mensaje = mensaje.lower()  # Convertir todo a minúsculas
    for menu_type, menu in menus.items():
        productos_en_menu = menu['Item'].str.lower().tolist()
        for producto in productos_en_menu:
            if producto in mensaje:
                return producto, menu_type
    return None, None

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

# Inicializamos el historial de chat y el pedido actual
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.carta_mostrada = False
    st.session_state.menu_actual = None
    st.session_state.pedido_actual = {}
    st.session_state.total_pedido = 0

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
    st.session_state.menu_actual = None
    st.session_state.pedido_actual = {}
    st.session_state.total_pedido = 0

# Mostrar mensajes de chat desde el historial
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Mostrar campo de entrada de prompt
prompt = st.chat_input("¿Qué quieres saber?")

# Cargar el menú
menus = cargar_menus()

# Función para mostrar el menú
def mostrar_menu(tipo):
    if tipo in menus:
        st.write(f"Menú de {tipo.capitalize()}:")
        st.write(menus[tipo])
    else:
        st.write(f"Lo siento, no tenemos un menú de {tipo}.")

# Función para procesar el pedido
def procesar_pedido(mensaje, menus):
    palabras = mensaje.lower().split()
    cantidades = {'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10}
    cantidad = 1
    item = None
    menu_type = None
    
    # Buscar palabras que indiquen cantidades numéricas
    for i, palabra in enumerate(palabras):
        if palabra.isdigit():
            cantidad = int(palabra)
        elif palabra in cantidades:
            cantidad = cantidades[palabra]

        # Verificar si el pedido se refiere a algún producto en el menú
        item, menu_type = verificar_pedido(' '.join(palabras[i:]), menus)
        if item:
            break
    
    if item and menu_type:
        # Extraer el precio del ítem
        precio = menus[menu_type][menus[menu_type]['Item'].str.lower() == item]['Precio'].values[0]
        total = precio * cantidad
        
        # Actualizar el pedido actual
        if item in st.session_state.pedido_actual:
            st.session_state.pedido_actual[item]["cantidad"] += cantidad
            st.session_state.pedido_actual[item]["subtotal"] += total
        else:
            st.session_state.pedido_actual[item] = {"cantidad": cantidad, "precio": precio, "subtotal": total}
        
        st.session_state.total_pedido += total
        
        # Mostrar el detalle del pedido y el total actual
        return (f"Has agregado {cantidad} {item}(s) a tu pedido. El total actual es de ${st.session_state.total_pedido:.2f}.")
    return None

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
            elif "menú" in prompt.lower() or "carta" in prompt.lower():  # Corrección aplicada aquí
                if "platos" in prompt.lower():
                    mostrar_menu('platos')
                    respuesta = "Aquí está el menú de platos. ¿Qué te gustaría ordenar?"
                    st.session_state.menu_actual = 'platos'
                elif "bebidas" in prompt.lower():
                    mostrar_menu('bebidas')
                    respuesta = "Aquí está el menú de bebidas. ¿Qué te gustaría ordenar?"
                    st.session_state.menu_actual = 'bebidas'
                elif "postres" in prompt.lower():
                    mostrar_menu('postres')
                    respuesta = "Aquí está el menú de postres. ¿Qué te gustaría ordenar?"
                    st.session_state.menu_actual = 'postres'
                else:
                    for menu_type in menus:
                        mostrar_menu(menu_type)
                    respuesta = "Te he mostrado todos nuestros menús. ¿Qué te gustaría ordenar?"

            # Procesar pedidos cuando se detecte la palabra "pedir" o "ordenar"
            elif "pedir" in prompt.lower() or "ordenar" in prompt.lower():
                resultado_pedido = procesar_pedido(prompt, menus)
                if resultado_pedido:
                    respuesta = resultado_pedido
                else:
                    respuesta = "Lo siento, no entendí tu pedido. ¿Podrías especificar qué te gustaría pedir?"
            
            # Verificar distrito de reparto
            distrito = verificar_distrito(prompt)
            if distrito:
                respuesta += f" Repartimos en {distrito}."
            elif "reparto" in prompt.lower() or "entrega" in prompt.lower():
                respuesta += f" No repartimos en esa zona. Zonas de reparto: {', '.join(DISTRITOS_REPARTO)}."

            st.chat_message("assistant").markdown(respuesta)
