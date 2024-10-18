import streamlit as st
import pandas as pd
from datetime import datetime
from groq import Groq
from typing import Generator
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
        return (pd.DataFrame(columns=['Plato', 'Precio']), 
                pd.DataFrame(columns=['Bebida', 'Precio']), 
                pd.DataFrame(columns=['Postre', 'Precio']))

# Verificar si el pedido es válido (producto está en la carta)
def verificar_pedido(mensaje, menu_restaurante):
    productos_en_menu = menu_restaurante['Plato'].str.lower().tolist()
    for producto in productos_en_menu:
        if producto in mensaje.lower():
            return producto
    return None

# Guardar pedido con timestamp y monto
def guardar_pedido(pedido, monto, cantidad):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_pedido = pd.DataFrame([[timestamp, pedido, cantidad, monto]], 
                                columns=['Timestamp', 'Pedido', 'Cantidad', 'Monto'])
    
    if not os.path.exists('pedidos.csv'):
        nuevo_pedido.to_csv('pedidos.csv', index=False)
    else:
        nuevo_pedido.to_csv('pedidos.csv', mode='a', header=False, index=False)

# Inicializamos el historial de chat y la lista de pedidos acumulados
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.carta_mostrada = False
    st.session_state.menu_actual = "platos"
    st.session_state.pedido_acumulado = []

# Manejo de cambios de modelo
if "selected_model" not in st.session_state:
    st.session_state.selected_model = modelos[0]

parModelo = st.sidebar.selectbox('Modelos', options=modelos, index=modelos.index(st.session_state.selected_model))

# Si el modelo cambia, reinicia el historial
if parModelo != st.session_state.selected_model:
    st.session_state.selected_model = parModelo
    st.session_state.messages = []
    st.session_state.pedido_acumulado = []

# Botón para reiniciar el chat
if st.sidebar.button("Reiniciar chat"):
    st.session_state.messages = []
    st.session_state.carta_mostrada = False
    st.session_state.menu_actual = "platos"
    st.session_state.pedido_acumulado = []

# Mostrar mensajes de chat desde el historial
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Mostrar campo de entrada de prompt
prompt = st.chat_input("¿Qué te gustaría pedir o consultar?")

# Cargar el menú
menu_platos, menu_bebidas, menu_postres = cargar_menus()

# Función para procesar el pedido y acumular
def procesar_pedido(prompt, menu_actual):
    cantidad = None
    for palabra in prompt.split():
        if palabra.isdigit():
            cantidad = int(palabra)
            break

    if menu_actual == "platos":
        producto = verificar_pedido(prompt, menu_platos)
        menu = menu_platos
    elif menu_actual == "bebidas":
        producto = verificar_pedido(prompt, menu_bebidas)
        menu = menu_bebidas
    elif menu_actual == "postres":
        producto = verificar_pedido(prompt, menu_postres)
        menu = menu_postres

    if producto and cantidad:
        precio_unitario = menu[menu['Plato'].str.lower() == producto]['Precio'].values[0]
        total_precio = cantidad * precio_unitario

        st.session_state.pedido_acumulado.append({
            "Producto": producto, 
            "Cantidad": cantidad, 
            "Precio unitario": precio_unitario, 
            "Total": total_precio
        })

        return f"Has pedido {cantidad} {producto}(s). Precio total: ${total_precio}."
    else:
        return "Lo siento, no entendí tu pedido. Por favor, intenta de nuevo."

# Validación del prompt: no vacío y no demasiado largo
if prompt:
    if len(prompt) > 2000:
        st.error("El mensaje es demasiado largo. Por favor, acórtalo.")
    else:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Generando respuesta..."):
            try:
                if "menú" in prompt.lower() or "carta" in prompt.lower():
                    if "platos" in prompt.lower():
                        st.write("Aquí tienes el menú de platos:")
                        st.write(menu_platos)
                        respuesta = "Aquí tienes el menú de platos. Si deseas ver el menú de bebidas o postres, solo pídelo."
                        st.session_state.menu_actual = "platos"
                    elif "bebidas" in prompt.lower():
                        st.write("Aquí tienes el menú de bebidas:")
                        st.write(menu_bebidas)
                        respuesta = "Aquí tienes el menú de bebidas. Si deseas ver el menú de platos o postres, solo pídelo."
                        st.session_state.menu_actual = "bebidas"
                    elif "postres" in prompt.lower():
                        st.write("Aquí tienes el menú de postres:")
                        st.write(menu_postres)
                        respuesta = "Aquí tienes el menú de postres. Si deseas ver el menú de platos o bebidas, solo pídelo."
                        st.session_state.menu_actual = "postres"
                    else:
                        # Repetir menú actual
                        if st.session_state.menu_actual == "platos":
                            st.write("Aquí tienes nuevamente el menú de platos:")
                            st.write(menu_platos)
                            respuesta = "Te muestro nuevamente el menú de platos."
                        elif st.session_state.menu_actual == "bebidas":
                            st.write("Aquí tienes nuevamente el menú de bebidas:")
                            st.write(menu_bebidas)
                            respuesta = "Te muestro nuevamente el menú de bebidas."
                        elif st.session_state.menu_actual == "postres":
                            st.write("Aquí tienes nuevamente el menú de postres:")
                            st.write(menu_postres)
                            respuesta = "Te muestro nuevamente el menú de postres."
                elif "pedido" in prompt.lower() or "quiero" in prompt.lower():
                    respuesta = procesar_pedido(prompt, st.session_state.menu_actual)
                elif "ver total" in prompt.lower():
                    if st.session_state.pedido_acumulado:
                        total = sum(item["Total"] for item in st.session_state.pedido_acumulado)
                        respuesta = f"El total acumulado de tu pedido es: ${total}."
                        for item in st.session_state.pedido_acumulado:
                            respuesta += f"\n- {item['Cantidad']}x {item['Producto']} (${item['Total']})"
                    else:
                        respuesta = "No tienes ningún pedido acumulado todavía."
                else:
                    respuesta = "Lo siento, no entendí tu solicitud. ¿Podrías intentarlo de nuevo?"

                st.chat_message("assistant").markdown(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})

            except Exception as e:
                st.error(f"Hubo un error al procesar tu solicitud: {e}")
else:
    if "messages" not in st.session_state:
        st.chat_message("assistant").markdown("¡Bienvenido! ¿En qué puedo ayudarte hoy?")
        st.session_state.messages.append({"role": "assistant", "content": "¡Bienvenido! ¿En qué puedo ayudarte hoy?"})
