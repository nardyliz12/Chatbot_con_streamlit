import streamlit as st

from openai import OpenAI



# titulo

st.title("Chatbot")

openai_api_key = "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"

  

# el openia

client = OpenAI(api_key=openai_api_key)



  # Crear

if "messages" not in st.session_state:

    st.session_state.messages = []



  # mensages

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

      st.markdown(message["content"])



  #block de text

if prompt := st.chat_input("Que deseas preguntar?"):



    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):

      st.markdown(prompt)

      

    # responde el OpenAI API.

    stream = client.chat.completions.create(

      model="gpt-3.5-turbo",

      messages=[

        {"role": m["role"], "content": m["content"]}

        for m in st.session_state.messages

      ],

      stream=True,

    )



    # 

    with st.chat_message("assistant"):

      response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
