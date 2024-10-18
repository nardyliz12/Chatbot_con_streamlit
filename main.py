import pandas as pd
import streamlit as st
from datetime import datetime
from copy import deepcopy
from groq import Groq
#import openai
#from openai import OpenAI
import csv
import re
import pytz
import json
import logging
# Configura el logger
# Define la API Key directamente en el código
api_key = "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"

# Inicializamos el cliente de Groq con la API Key
client = Groq(api_key=api_key)

# Configuración inicial de la página
st.set_page_config(page_title="SazónBot", page_icon=":pot_of_food:")
st.title("BotRestaurant - 5 Star Michilini")

# Mensaje de bienvenida
intro = """¡Bienvenido a Sazón Bot, el lugar donde todos tus antojos de almuerzo se hacen realidad!
Comienza a chatear con Sazón Bot y descubre qué puedes pedir, cuánto cuesta y cómo realizar tu pago. ¡Estamos aquí para ayudarte a disfrutar del mejor almuerzo!"""
st.markdown(intro)


# Cargar el menú desde un archivo CSV
def load(file_path):
    """Cargar el menú desde un archivo CSV con columnas Plato, Descripción y Precio."""
    load = pd.read_csv(file_path)
    return load

# Cargar los distritos de reparto desde un archivo CSV
#def load_distritos(file_path):
 #   """Cargar los distritos de reparto desde un archivo CSV."""
  #  distritos = pd.read_csv(file_path)
   # return distritos

def format_menu(menu):
    if menu.empty:
        return "No hay platos disponibles."

    else:
        # Encabezados de la tabla
        table = "| **Plato** | **Descripción** | **Precio** |\n"
        table += "|-----------|-----------------|-------------|\n"  # Línea de separación
        
        # Filas de la tabla
        for idx, row in menu.iterrows():
            table += f"| {row['Plato']} | {row['Descripción']} | S/{row['Precio']:.2f} |\n"
        
        return table


# Mostrar el menú con descripciones
def display_menu(menu):
    """Mostrar el menú con descripciones."""
    menu_text = "Aquí está nuestra carta:\n"
    for index, row in menu.iterrows():
        menu_text += f"{row['Plato']}: {row['Descripción']} - {row['Precio']} soles\n"
    return menu_text

# Mostrar los distritos de reparto
def display_distritos(distritos):
    """Mostrar los distritos de reparto disponibles."""
    distritos_text = "Los distritos de reparto son:\n"
    for index, row in distritos.iterrows():
        distritos_text += f"*{row['Distrito']}*\n"
    return distritos_text

def display_postre(postre):
    """Mostrar el menú con descripciones."""
    postre_text = "Aquí está lista de postres:\n"
    for index, row in postre.iterrows():
        postre_text += f"{row['Postres']}: {row['Descripción']} - {row['Precio']} soles\n"
    return postre_text

def display_bebida(bebida):
    """Mostrar el menú con descripciones."""
    bebida_text = "Aquí está lista de bebidas:\n"
    for index, row in bebida.iterrows():
        bebida_text += f"{row['bebida']}: {row['descripcion']} - {row['precio']} soles\n"
    return bebida_text
		
# Cargar el menú y distritos
menu = load("carta.csv")
distritos = load("distritos.csv")
bebidas= load("Bebidas.csv")
postres= load("Postres.csv")

def display_confirmed_order(order_details):
    """Genera una tabla en formato Markdown para el pedido confirmado."""
    table = "| **Plato** | **Cantidad** | **Precio Total** |\n"
    table += "|-----------|--------------|------------------|\n"
    for item in order_details:
        table += f"| {item['Plato']} | {item['Cantidad']} | S/{item['Precio Total']:.2f} |\n"
    table += "| **Total** |              | **S/ {:.2f}**      |\n".format(sum(item['Precio Total'] for item in order_details))
    return table

##Pendiente


def get_system_prompt(menu, distritos):
    """Define el prompt del sistema para el bot de Sazón incluyendo el menú y distritos."""
    lima_tz = pytz.timezone('America/Lima')  # Define la zona horaria de Lima
    hora_lima = datetime.now(lima_tz).strftime("%Y-%m-%d %H:%M:%S")  # Obtiene la hora actual en Lima
    system_prompt = f"""
    Eres el bot de pedidos de Sazón, amable y servicial. Ayudas a los clientes a hacer sus pedidos y siempre confirmas que solo pidan platos que están en el menú oficial. Aquí tienes el menú para mostrárselo a los clientes:\n{display_menu(menu)}\n
    También repartimos en los siguientes distritos: {display_distritos(distritos)}.\n
    Primero, saluda al cliente y ofrécele el menú. Asegúrate de que el cliente solo seleccione platos que están en el menú actual y explícales que no podemos preparar platos fuera del menú.
    **IMPORTANTE: Validación de cantidad solicitada**
    - El cliente puede indicar la cantidad en texto (por ejemplo, "dos") o en números (por ejemplo, "2").
    - Interpreta y extrae las cantidades independientemente de si están en números o en palabras y asócialas correspondientemente.
    - Por ejemplo, si el cliente escribe "quiero dos arroz con pollo y diez pachamanca de pollo", interpreta esto como "2 unidades de arroz con pollo" y "10 unidades de pachamanca de pollo".
    - Si la cantidad solicitada está en el rango de 1 a 100 (inclusive), acepta el pedido sin mostrar advertencias.
    - Si la cantidad solicitada es mayor que 100, muestra el siguiente mensaje:
      "Lamento informarte que el límite máximo de cantidad por producto es de 100 unidades. Por favor, reduce la cantidad para procesar tu pedido."
      
    Después de que el cliente haya seleccionado sus platos, pregunta si desea recoger su pedido en el local o si prefiere entrega a domicilio. Asegurate que ingrese metodo de entrega.
     - Si elige entrega, pregúntale al cliente a qué distrito desea que se le envíe su pedido, confirma que el distrito esté dentro de las zonas de reparto y verifica el distrito de entrega con el cliente.
     - Si el pedido es para recoger, invítalo a acercarse a nuestro local ubicado en UPCH123.
    
    Usa solo español peruano en tus respuestas, evitando palabras como "preferís" y empleando "prefiere" en su lugar.
    
    Antes de continuar, confirma que el cliente haya ingresado un método de entrega válido. Luego, resume el pedido en la siguiente tabla:\n
    | **Plato**      | **Cantidad** | **Precio Total** |\n
    |----------------|--------------|------------------|\n
    |                |              |                  |\n
    | **Total**      |              | **S/ 0.00**      |\n
    
    Aclara que el monto total del pedido no acepta descuentos ni ajustes de precio.
    
    Después, pregunta al cliente si quiere añadir una bebida o postre.
	- Si responde bebida, muéstrale únicamente la carta de bebidas:{display_bebida(bebidas)}
	- Si responde postre, muéstrale solo la carta de postres:{display_postre(postres)}
    *Después de que el cliente agrega bebidas o postres, pregúntale si desea agregar algo más.* Si el cliente desea agregar más platos, bebidas o postres, permite que lo haga. Si no desea agregar más, continúa con el proceso.

    Si el cliente agrega más ítems, actualiza la tabla de resumen del pedido, recalculando el monto total con precisión.

    Antes de terminar, pregúntale al cliente: "¿Estás de acuerdo con el pedido?" y espera su confirmación.

    **Luego de confirmar el pedido, pregunta explícitamente al cliente por el método de pago.** Solicita el método de pago preferido (tarjeta, efectivo, Yape u otra opción disponible) y **verifica que el cliente haya ingresado una opción válida antes de continuar**.
   
    Luego de verificar el método de pago, confirma el pedido al cliente incluyendo todos los detalles. Incluye explícitamente:
    	El pedido confirmado será:\n
    	{display_confirmed_order([{'Plato': '', 'Cantidad': 0, 'Precio Total': 0}])}\n
	- *Método de pago*: el método que el cliente eligió.
	- *Lugar de entrega*: el distrito de entrega o indica que recogerá en el local.
	- *Timestamp Confirmacion*: hora exacta de confirmación del pedido, el valor '{hora_lima}'.
         
    Recuerda siempre confirmar que el pedido, el metodo de pago y el lugar de entrega estén hayan sido ingresados, completos y correctos antes de registrarlo.
    """
    return system_prompt.replace("\n", " ")
   
def extract_order_json(response):
    """Extrae el pedido confirmado en formato JSON desde la respuesta del bot solo si todos los campos tienen valores completos."""
    prompt = f"""
		A partir de la siguiente respuesta del asistente, extrae la información del pedido confirmado.

		Respuesta del asistente:
		'''{response}'''

		Proporciona un JSON con el siguiente formato:

		{{
    			"Platos": [
        			{{"Plato": "Nombre del plato", "Cantidad": cantidad, "Precio Total": precio_total}},
        			...
    				],
    			"Total": total_pedido,
    			"Metodo de Pago": "metodo_de_pago",
    			"Lugar de Entrega": "lugar_entrega",
    			"Timestamp Confirmacion": "timestamp_confirmacion"
		}}

		Si algún campo no aparece en la respuesta, asígnale el valor null.

		Si el pedido no está confirmado explícitamente en la respuesta, devuelve un JSON vacío: {{}}.
  		Responde *solo* con el JSON, sin explicaciones adicionales.
    		"""
    #prompt = f"Extrae la información del pedido confirmado solo de la siguiente respuesta: '{response}'. Si el pedido está confirmado, proporciona una salida en formato JSON con las siguientes claves: 'Platos' (contiene los platos, cada uno con su cantidad y precio_total), 'Total', 'metodo de pago', 'lugar_entrega', y 'timestamp_confirmacion'. Si algún campo como 'metodo de pago' o 'lugar_entrega'o 'timestamp_confirmacion' no está presente, asígnale el valor null. Si el pedido no está confirmado, devuelve un diccionario vacio."
    #prompt = f"Extrae la información del pedido de la siguiente respuesta: '{response}'. Si el pedido está confirmado proporciona una salida en formato JSON con las claves: Platos(contine los platos con la cantidad y precio_total),Total,metodo de pago,lugar_entrega y timestamp_confirmacion. Si el pedido no está confirmado devuelve una diccionario vacio."

    extraction = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Eres un asistente que extrae información de pedidos en formato JSON a partir de la respuesta proporcionada."},
            {"role": "user", "content": prompt}
        ],
        model="gpt-3.5-turbo",
        temperature=0,
        max_tokens=300,
        top_p=1,
        stop=None,
        stream=False,
    )
#"gemma2-9b-it"
    response_content = extraction.choices[0].message.content
    
    # Intenta cargar como JSON
    try:
        order_json = json.loads(response_content)
        #st.markdown(order_json)
        #st.markdown(type(order_json))
        # Verifica si el JSON es un diccionario
        if isinstance(order_json, dict):
            if all(order_json[key] not in (None, '', [], {}) for key in order_json):
                return order_json
            else:
                print("Advertencia: Hay claves con valores nulos o vacíos en el pedido.")
                return {}
            # Verifica que todas las claves en order_json tengan valores no nulos
            #return order_json if order_json else {}
        
        # Si el JSON es una lista, devuelves un diccionario vacío o manejas la lista de otro modo
        elif isinstance(order_json, list):
            print("Advertencia: Se recibió una lista en lugar de un diccionario.")
            return {}
        
        # Si no es ni lista ni diccionario, retorna un diccionario vacío
        else:
            return {}
    
    except json.JSONDecodeError:
        # Manejo de error en caso de que el JSON no sea válido
        return {}

def generate_response(prompt, temperature=0,max_tokens=1000):
    """Enviar el prompt a Groq y devolver la respuesta con un límite de tokens."""
    st.session_state["messages"].append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state["messages"],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    response = completion.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": response})
    # Extraer JSON del pedido confirmado
    order_json = extract_order_json(response)
    #st.markdown(order_json)
    #st.markdown(type(order_json))
    logging.info(json.dumps(order_json, indent=4) if order_json else '{}')
    return response

# Función para verificar contenido inapropiado
def check_for_inappropriate_content(prompt):
    """Verifica si el prompt contiene contenido inapropiado utilizando la API de Moderación de OpenAI."""
    try:
        response = client.moderations.create(input=prompt)
        logging.info(f"Moderation API response: {response}")
         # Acceso correcto a los resultados de la respuesta de moderación
        moderation_result = response.results[0]
        
        # Verifica si está marcado como inapropiado
        if moderation_result.flagged:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error al llamar a la API de Moderación: {e}")
        return False
	
# Ajustar el tono del bot
def adjust_tone(tone="friendly"):
    """Ajustar el tono del bot según las preferencias del cliente."""
    if tone == "formal":
        st.session_state["tone"] = "formal"
        return "Eres un asistente formal y educado."
    else:
        st.session_state["tone"] = "friendly"
        return "Eres un asistente amigable y relajado."

        
initial_state = [
    {"role": "system", "content": get_system_prompt(menu,distritos)},
    {
        "role": "assistant",
        "content": f"¡Hola! Bienvenido a Sazón Bot. Este es el menú del día:\n\n{format_menu(menu)}\n\n¿Qué te puedo ofrecer?",
    },
]


if "messages" not in st.session_state:
    st.session_state["messages"] = deepcopy(initial_state)

# eliminar conversación
clear_button = st.button("Eliminar conversación", key="clear")
if clear_button:
    st.session_state["messages"] = deepcopy(initial_state)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    elif message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="👨‍🍳"):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"], avatar="👤"):
            st.markdown(message["content"])

if prompt := st.chat_input():
    # Verificar si el contenido es inapropiado
    if check_for_inappropriate_content(prompt):
        with st.chat_message("assistant", avatar="👨‍🍳"):
            st.markdown("Por favor, mantengamos la conversación respetuosa.")
		
    else:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        output = generate_response(prompt)
        with st.chat_message("assistant", avatar="👨‍🍳"):
            st.markdown(output)
    

