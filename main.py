import pandas as pd
import streamlit as st
from datetime import datetime
from copy import deepcopy
from groq import Groq
import re

 Define la API Key directamente en el código
api_key = "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"

# Inicializamos el cliente de Groq con la API Key
client = Groq(api_key=api_key)

# Configuración inicial de la página
st.set_page_config(page_title="SazónBot", page_icon=":pot_of_food:")
st.title("BotRestaurant - 5 Star Michilini")

# Mensaje de bienvenida
intro = """¡Bienvenido a BotRestaurant, tu destino para saborear lo mejor de la comida asiática! Comienza tu aventura y descubre los deliciosos platos que tenemos para ofrecerte de la gastronomia Asiática. 
¡Estamos aquí para ayudarte a disfrutar de una experiencia culinaria única y auténtica!"""
st.markdown(intro)

# Cargar menús desde archivos CSV
def load_menu(csv_file):
    menu = pd.read_csv(csv_file)
    return menu

def load_districts(csv_file):
    districts = pd.read_csv(csv_file)
    return districts['Distrito'].tolist()

def format_menu(menu):
    if menu.empty:
        return "No hay platos disponibles."

    formatted_menu = []
    for idx, row in menu.iterrows():
        formatted_menu.append(
            f"*{row['Plato']}\n{row['Descripción']}\nPrecio:* S/{row['Precio']}"
        )
    return "\n\n".join(formatted_menu)

# Cargar distritos
districts = load_districts("distritos.csv")

# Estado inicial del chatbot
initial_state = [
    {"role": "system", "content": "You are SazónBot. A friendly assistant helping customers with their lunch orders."},
]

# Función para guardar los pedidos
def save_order(order, total_price):
    with open("orders.csv", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp}, {order}, {total_price}\n")

def validate_order(prompt, menu):
    order_details = {}
    total_price = 0
    pattern = r'(\d+)\s*(?:platos|plato)?\s*([a-zA-Z\s]+)'

    prompt = prompt.replace('\n', '').lower().strip()
    matches = re.findall(pattern, prompt)

    for quantity_str, dish_name in matches:
        try:
            quantity = int(quantity_str.strip())
            dish_name = dish_name.strip()
            normalized_dish_name = dish_name.lower()
            if normalized_dish_name in menu['Plato'].str.lower().values:
                price = menu.loc[menu['Plato'].str.lower() == normalized_dish_name, 'Precio'].values[0]
                order_details[dish_name] = quantity
                total_price += price * quantity
            else:
                return None, None
        except ValueError:
            return None, None

    return order_details, total_price

# Verificar si el distrito es válido
def is_valid_district(district, districts):
    return district.lower() in [d.lower() for d in districts]

# Inicializar la conversación si no existe en la sesión
if "messages" not in st.session_state:
    st.session_state["messages"] = deepcopy(initial_state)
    st.session_state["order"] = None
    st.session_state["total_price"] = 0

# Botón para limpiar la conversación
clear_button = st.button("Limpiar Conversación", key="clear")
if clear_button:
    st.session_state["messages"] = deepcopy(initial_state)
    st.session_state["order"] = None
    st.session_state["total_price"] = 0

# Mostrar el historial de la conversación
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"], avatar="🍲" if message["role"] == "assistant" else "👤"):
        st.markdown(message["content"])

# Selección del tipo de menú
menu_type = st.selectbox("¿Qué menú te gustaría ver?", options=["Platos", "Bebidas", "Postres"])

# Cargar el menú correspondiente
if menu_type == "Platos":
    menu = load_menu("platos.csv")
elif menu_type == "Bebidas":
    menu = load_menu("bebidas.csv")
else:  # "Postres"
    menu = load_menu("postres.csv")

# Formatear y mostrar el menú seleccionado
menu_display = format_menu(menu)
st.markdown(menu_display)

# Entrada del usuario para el pedido
if user_input := st.chat_input("¿Qué te gustaría pedir?"):
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Llamar a Groq para obtener una respuesta
    chat_completion = client.chat.completions.create(
        messages=[{"role": "system", "content": "You are a helpful assistant for a food ordering service."},
                  {"role": "user", "content": f"Extrae la cantidad y el plato de la siguiente solicitud: '{user_input}'.Limitate a solo devolver la cantidad y el plato de la solicitud sin un caracter adicional."}],
        model="llama3-8b-8192",
        temperature=0.5,
        max_tokens=150,
        top_p=1,
        stop=None,
        stream=False,
    )

    parsed_message = chat_completion.choices[0].message.content.strip()
    
    # Validar el pedido del usuario
    order_details, total_price = validate_order(parsed_message, menu)

    if order_details:
        st.session_state["order"] = order_details
        st.session_state["total_price"] = total_price
        
        response_text = f"Tu pedido ha sido registrado:\n\n{format_order_table(order_details)}\n\n¿Está correcto? (Sí o No)"
    else:
        response_text = f"Uno o más platos no están disponibles. Aquí está el menú otra vez:\n\n{format_menu(menu)}"

    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(response_text)

# Manejo de confirmación del pedido
if "order" in st.session_state and st.session_state["order"]:
    if confirmation_input := st.chat_input("¿Está correcto? (Sí o No)"):
        with st.chat_message("user", avatar="👤"):
            st.markdown(confirmation_input)

        if confirmation_input.lower() == "si":
            response_text = "Por favor selecciona un distrito de entrega:"
            response_text += f"\n\nEstos son los distritos disponibles: {', '.join(districts)}"
            with st.chat_message("assistant", avatar="🍲"):
                st.markdown(response_text)

            if district_input := st.chat_input("Ingresa el distrito:"):
                with st.chat_message("user", avatar="👤"):
                    st.markdown(district_input)

                if is_valid_district(district_input, districts):
                    response_text = f"Gracias por proporcionar tu distrito: {district_input}. Procederemos a entregar tu pedido allí. ¡Que disfrutes de tu almuerzo!"
                    save_order(st.session_state["order"], st.session_state["total_price"])
                    st.session_state["order"] = None
                    st.session_state["total_price"] = 0
                else:
                    response_text = f"Lo siento, no entregamos en ese distrito. Estos son los distritos disponibles: {', '.join(districts)}"

                with st.chat_message("assistant", avatar="🍲"):
                    st.markdown(response_text)

        elif confirmation_input.lower() == "no":
            response_text = "Entiendo, puedes volver a hacer tu pedido."
            with st.chat_message("assistant", avatar="🍲"):
                st.markdown(response_text)
