import streamlit as st
import pandas as pd
from datetime import datetime
from groq import Groq
from typing import Generator

# Título de la aplicación
st.title("ChatMang - Comida Asiática")

# Define la API Key directamente en el código
api_key = "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"

# Inicializamos el cliente de Groq con la API Key
client = Groq(api_key=api_key)

# Lista de modelos para elegir
modelos=['llama3-8b-8192','llama3-70b-8192','mixtral-8x7b-32768']

# Mensaje de bienvenida
intro = """¡Bienvenido a Sazón Bot, el lugar donde todos tus antojos de almuerzo se hacen realidad!
Comienza a chatear con Sazón Bot y descubre qué puedes pedir, cuánto cuesta y cómo realizar tu pago. ¡Estamos aquí para ayudarte a disfrutar del mejor almuerzo!"""
st.markdown(intro)

# Cargar menú y distritos desde archivos CSV
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
            f"{row['Plato']}\n{row['Descripción']}\n*Precio:* S/{row['Precio']}"
        )
    return "\n\n".join(formatted_menu)

# Cargar el menú y distritos
menu = load_menu("carta.csv")
districts = load_districts("distritos.csv")

# Estado inicial del chatbot
initial_state = [
    {"role": "system", "content": "You are SazónBot. A friendly assistant helping customers with their lunch orders."},
    {
        "role": "assistant",
        "content": f"👨‍🍳¿Qué te puedo ofrecer?\n\nEste es el menú del día:\n\n{format_menu(menu)}",
    },
]

# Función para guardar los pedidos
def save_order(order, total_price):
    with open("orders.csv", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp}, {order}, {total_price}\n")

def validate_order(prompt, menu):
    order_details = {}
    total_price = 0
    pattern = r'(\d+)\s*(?:platos|plato)?\s*([a-zA-Z\s]+)'   # Regex actualizado

    prompt = prompt.replace('\n', '').lower().strip()  # Normalizar el prompt a minúsculas
    matches = re.findall(pattern, prompt)

    for quantity_str, dish_name in matches:
        try:
            quantity = int(quantity_str.strip())
            dish_name = dish_name.strip()
            # Normalizar el nombre del plato
            normalized_dish_name = dish_name.lower()
            # Comparar con el menú
            if normalized_dish_name in menu['Plato'].str.lower().values:
                price = menu.loc[menu['Plato'].str.lower() == normalized_dish_name, 'Precio'].values[0]
                order_details[dish_name] = quantity
                total_price += price * quantity
            else:
                return None, None  # Plato no existe
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

def format_order_table(order_details):
    table = "| Cantidad | Plato |\n"
    table += "|----------|-------|\n"
    
    for dish, quantity in order_details.items():
        if dish and quantity:
            table += f"| {quantity}        | {dish}  |\n"
    
    return table

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
        # Guardar el pedido en el estado
        st.session_state["order"] = order_details
        st.session_state["total_price"] = total_price
        
        # Solicitar confirmación del pedido
        response_text = f"Tu pedido ha sido registrado:\n\n{format_order_table(order_details)}\n\n¿Está correcto? (Sí o No)"
    else:
        # Si el plato no existe, mostrar el menú de nuevo
        response_text = f"Uno o más platos no están disponibles. Aquí está el menú otra vez:\n\n{format_menu(menu)}"

    # Mostrar la respuesta del asistente
    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(response_text)

# Manejo de confirmación del pedido
if "order" in st.session_state and st.session_state["order"]:
    if confirmation_input := st.chat_input("¿Está correcto? (Sí o No)"):
        with st.chat_message("user", avatar="👤"):
            st.markdown(confirmation_input)

        # Confirmar pedido
        if confirmation_input.lower() == "si":
            response_text = "Por favor selecciona un distrito de entrega:"
            response_text += f"\n\nEstos son los distritos disponibles: {', '.join(districts)}"
            with st.chat_message("assistant", avatar="🍲"):
                st.markdown(response_text)

            if district_input := st.chat_input("Ingresa el distrito:"):
                with st.chat_message("user", avatar="👤"):
                    st.markdown(district_input)

                # Verificar si el distrito es válido
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
