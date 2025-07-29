import os
import openai
import json

openai.api_key = os.getenv("IA_API_KEY")  # O usa os.environ["OPENAI_API_KEY"]

# Simulación de base de datos en memoria
user_threads = {}  # clave: user_id, valor: thread_id

# Assistant ID que creaste (copiar desde platform.openai.com/assistants)
ASSISTANT_ID = os.getenv("IA_ASSISTANT_ID")


def obtener_o_crear_thread(user_id: str) -> str:
    """Devuelve el thread_id correspondiente al usuario, o lo crea si no existe."""
    if user_id in user_threads:
        return user_threads[user_id]

    thread = openai.beta.threads.create()
    user_threads[user_id] = thread.id
    return thread.id


def enviar_mensaje_ia(user_id: str, mensaje: str) -> str:
    """Envía un mensaje al assistant y obtiene la respuesta."""
    thread_id = obtener_o_crear_thread(user_id)

    # 1. Agregar mensaje al hilo
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=mensaje,
    )

    # 2. Ejecutar el assistant
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
        model="gpt-4o-mini"
    )

    # 3. Esperar a que termine
    while True:
      run_status = openai.beta.threads.runs.retrieve(
        run_id=run.id,
        thread_id=thread_id,
      ).status

      if run_status == "completed":
          break
      elif run_status in ["failed", "cancelled", "expired"]:
          raise Exception(f"Fallo en run: {run_status}")
    
    # 4. Obtener respuesta
    messages = openai.beta.threads.messages.list(thread_id)
    for msg in messages.data:
        if msg.role == "assistant":
            try:
                # 5. Convertir respuesta en json { query: str, message: str }
                responseJson = json.loads(msg.content[0].text.value)
                return responseJson
            
            except json.JSONDecodeError:
                return msg.content[0].text.value

    return "No se encontró una respuesta del asistente."


def enviar_mensaje_ia_random(prompt: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        top_p=1.0
    )

    return response.choices[0].message.content