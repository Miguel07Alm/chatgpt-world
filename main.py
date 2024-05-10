import json
import os
from random import randint
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored  
load_dotenv()
GPT_MODEL = "gpt-3.5-turbo-0613"
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)
def clear_console():
    if os.name == 'nt':  # nt significa Windows
        os.system('cls')  # Comando para limpiar consola en Windows
    else:
        os.system('clear')  # Comando para limpiar consola en Unix/Linux/MacOS

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            n=1,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e
def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }
    
    for message in messages:
        if "role" in message:
            if message["role"] == "system":
                print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "user":
                print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and message.get("function_call"):
                print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and not message.get("function_call"):
                print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "tool":
                print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "La ciudad o el estado estrictamente, ejemplo: San Francisco, CA",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "La unidad de temperatura. Deducela por la ubicacion del usuario.",
                    },
                },
                "required": ["location", "format"],
            },
        }
    },
]

messages = []
messages.append({"role": "system", "content": "Pide aclaraciones si una petición del usuario es ambigua. 'location' es la ciudad o el estado y 'format' la unidad de temperatura que tienes que inferir en base a dicha ciudad o estado si es grados o fahrenheit."})

while True:  
    user_content = str(input("Escribe un mensaje al asistente (0 para pararla): "))
    if (user_content.strip() == "0"):
        break
    messages.append({"role": "user", "content": user_content})

    chat_response = chat_completion_request(
        messages, tools=tools
    )
    assistant_message = chat_response.choices[0].message
    if not assistant_message.tool_calls:
        messages.append({"role": assistant_message.role, "content": assistant_message.content})
    else:
        messages.append(assistant_message)
    if assistant_message.tool_calls:
        for toolCall in assistant_message.tool_calls:
            if (toolCall.function.name == "get_current_weather"):
                tiempo_inventado = randint(-20, 40)
                argumentos = json.loads(toolCall.function.arguments)
                print("Argumentos: ", argumentos)
                print("Message tool: ", json.dumps({
                    "tool_call_id": toolCall.id,
                    "role": "tool",
                    "name": toolCall.function.name,
                    "content": json.dumps({
                        "location": argumentos.get("location"),
                        "temperature": tiempo_inventado,
                        "format": argumentos.get("format")
                    })
                }))
                messages.append({
                    "tool_call_id": toolCall.id,
                    "role": "tool",
                    "name": toolCall.function.name,
                    "content": json.dumps({
                        "location": argumentos.get("location"),
                        "temperature": tiempo_inventado,
                        "format": argumentos.get("format")
                    })
                })
                chat_response = chat_completion_request(messages, tools)
                assistant_message_with_tool = chat_response.choices[0].message
                print(assistant_message_with_tool)
                messages.append({"role": assistant_message_with_tool.role, "content": assistant_message_with_tool.content})

    clear_console()
    pretty_print_conversation(messages=messages)
    
print("Se ha finalizado la conversación...")