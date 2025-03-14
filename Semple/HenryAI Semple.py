import discord
import os
import requests
import json
from dotenv import load_dotenv

# Carica le variabili dal file .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Impostazioni del bot con intenti corretti
intents = discord.Intents.default()
intents.message_content = True  # NECESSARIO per leggere i messaggi
client = discord.Client(intents=intents)

async def ask_openrouter(prompt):
    """Invia una richiesta all'API di OpenRouter AI"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # "model": "mistralai/mistral-7b-instruct",  # Modello gratuito e leggero
    # "model": "mistralai/mistral-7b",  # Versione base di Mistral 7B
    # "model": "mistralai/mixtral-8x7b-instruct",  # Mixtral 8x7B (più potente)
    # "model": "meta-llama/llama-3-8b",  # LLaMA 3 da 8B parametri (Meta)
    # "model": "meta-llama/llama-2-7b-chat",  # LLaMA 2 Chat 7B
    # "model": "gemini/gemini-1.5-flash",  # Google Gemini 1.5 Flash
    # "model": "anthropic/claude-3-haiku",  # Claude 3 Haiku (Anthropic)
    # "model": "deepseek-ai/deepseek-chat",  # DeepSeek Chat (V3) avanzato
    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200 and "choices" in response_data and response_data["choices"]:
            answer = response_data["choices"][0]["message"]["content"]
            print(f"✅ Domanda: {prompt}\n✅ Risposta: {answer}\n")  # Stampa domanda e risposta nel terminale
            return answer
        elif response.status_code == 402:
            print("❌ Crediti esauriti su OpenRouter.\n")  # Stampa errore nel terminale
            return "❌ Crediti esauriti su OpenRouter. Acquista più crediti su https://openrouter.ai/credits"
        else:
            print(f"❌ Errore API ({response.status_code}): {response.text}\n")  # Stampa errore nel terminale
            return f"❌ Errore API ({response.status_code}): {response.text}"

    except Exception as e:
        print(f"❌ Errore durante la richiesta API: {e}\n")  # Stampa errore nel terminale
        return f"❌ Errore durante la richiesta API: {e}"

@client.event
async def on_ready():
    print(f'🤖 {client.user} è online!\n')

@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Evita che il bot risponda a se stesso

    # Stampa ogni messaggio ricevuto nel terminale
    print(f"📩 Messaggio ricevuto: {message.content}")

    # Controlla se il messaggio contiene una menzione diretta al bot
    if client.user in message.mentions:
        prompt = message.content.replace(f"<@{client.user.id}>", "").strip()
        if not prompt:
            await message.channel.send("❌ Devi scrivere una domanda dopo la menzione.")
            return

        await message.channel.send("🧠 Sto pensando...")
        response = await ask_openrouter(prompt)
        await message.channel.send(response)
        return  # Evita che venga elaborato anche come comando !ai

    # Comando tradizionale con !ai
    if message.content.startswith("!ai"):
        prompt = message.content[4:].strip()
        if not prompt:
            await message.channel.send("❌ Devi scrivere una domanda dopo !ai.")
            return

        await message.channel.send("🧠 Sto pensando...")
        response = await ask_openrouter(prompt)
        await message.channel.send(response)

# Avvia il bot
client.run(DISCORD_TOKEN)
