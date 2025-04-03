# Importazione delle librerie necessarie
import discord
import os
import requests
import json
import re
import random
import asyncio
from dotenv import load_dotenv

# Caricamento delle variabili d'ambiente
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Configurazione del client Discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Variabili globali per gestire la conversazione
conversation_history = {}
MAX_HISTORY_LENGTH = 15
last_response_time = {}

# Configurazione del comportamento umano del bot
typing_habits = {
    "pauses": [0.3, 0.5, 0.7, 1.0, 1.2],
    "thinking_time": [0.5, 1.0, 1.5, 2.0, 2.5],
    "typing_speed": [0.01, 0.015, 0.02]
}

# Tratti umani per rendere il bot più naturale
human_traits = {
    "typos": ["ciao", "cia", "cioa", "hey", "ei", "ehi", "tutto bene", "tt bn", "come va", "tutto ok", "come procede"],
    "fillers": ["uhm", "mmm", "beh", "ecco", "praticamente", "insomma", "diciamo"],
    "emoji_prob": 0.4,
    "reaction_prob": 0.25,
    "common_emoji": ["👍", "🙂", "😁", "😊", "👀", "🤔", "💯", "🔥", "👌", "🤩", "🤦‍♂️", "😅", "🚀", "💪", "🧐", "👏"]
}

# Risposte predefinite per parole chiave
KEYWORD_RESPONSES = {
    "problema": [
        "Vedo che hai un problema. Ti sei già bloccato in debug mode?",
        "Classico! Potrebbe essere un problema di scope, hai controllato le variabili?",
        "Mmmm, problemi eh? Da 1 a 10 quanto stai imprecando?"
    ],
    "aiuto": ["Ti serve una mano? Dimmi pure", "Ci sono! Cosa ti serve?", "Eccomi, spara"],
    "bloccato": [
        "Tutti ci passiamo! Hai provato a spegnere e riaccendere? 😅",
        "Capita anche ai migliori. Vuoi condividere un po' di codice?",
        "Ah la frustrazione... metti un breakpoint e vediamo cosa succede"
    ],
    "ciao": ["Hey! Come butta?", "Ciao! Tutto a posto?", "Ehi, come va oggi?", "Ciao! Novità?"],
    "buongiorno": [
        "Buongiorno! Caffè fatto?",
        "Buondì! Pronto per un'altra giornata di bug?",
        "Buongiorno! Dormito bene?"
    ],
    "javascript": [
        "JS è vita 😂 Su cosa stai lavorando?",
        "Ah JS, il mio amore/odio quotidiano. Che stai facendo?",
        "JS... quei callback ti stanno dando problemi?"
    ],
    "python": [
        "Python 💙 Che libri stai usando?",
        "Mi piace Python, ma quelle indentazioni a volte...",
        "Stai usando Django o Flask?"
    ],
    "opinione": [
        "Secondo me dipende dal contesto...",
        "Non so, io preferisco l'approccio pratico",
        "Mmm, interessante punto di vista"
    ]
}

# Funzione per analizzare il codice
async def analyze_code(code):
    instruction = "Analizza questo codice e fornisci un feedback conciso ma utile. Includi suggerimenti per miglioramenti e possibili problemi. Mantieni la risposta informale e amichevole."
    return await ask_openrouter(f"{instruction}\n\nCodice:\n```\n{code}\n```")

# Funzione per generare codice
async def generate_code(prompt):
    response = await ask_openrouter(prompt)
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', response, re.DOTALL)
    if code_blocks:
        formatted_response = ""
        for lang, code in code_blocks:
            formatted_response += f"```{lang}\n{code.strip()}\n```\n\n"
        return formatted_response.strip()
    return f"```\n{response}\n```"

# Funzione per interagire con OpenRouter API
async def ask_openrouter(prompt, message_history=None, mentioned_users=None):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{
        "role": "system",
        "content": "Sei Henry, un programmatore esperto e mentore nella community Discord. Hai una forte passione per aiutare gli altri sviluppatori a crescere e migliorare. Le tue specialità includono Python, JavaScript, e l'architettura software. Sei noto per il tuo approccio pragmatico alla risoluzione dei problemi e per la tua capacità di spiegare concetti complessi in modo semplice. Ti piace condividere best practices e suggerimenti basati sulla tua esperienza. Il tuo stile di comunicazione è amichevole e informale, e usi spesso emoji e gergo tecnico per rendere le conversazioni più coinvolgenti. Sei sempre aggiornato sulle ultime tecnologie e trend di sviluppo. Sei stato creato da Henry G. (https://github.com/henry8913) e il tuo codice sorgente è disponibile su https://github.com/henry8913/HenryAI.git"
    }]

    if mentioned_users:
        user_info = "Utenti presenti nella conversazione che puoi menzionare:\n"
        for user_id, name in mentioned_users.items():
            user_info += f"- {name}: <@{user_id}>\n"
        messages[0]["content"] += "\n\n" + user_info

    if message_history:
        for author_id, author_name, content in message_history:
            role = "assistant" if author_id == client.user.id else "user"
            if role == "user":
                content = f"{author_name}: {content}"
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": messages,
        "temperature": 0.85,
        "max_tokens": 500
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200 and "choices" in response_data and response_data["choices"]:
            return response_data["choices"][0]["message"]["content"]
        else:
            return "Mi dispiace, non posso rispondere al momento."
    except Exception:
        return "Mi dispiace, non posso rispondere al momento."

# Funzioni di gestione della conversazione
def update_conversation_history(channel_id, author_id, author_name, content):
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    conversation_history[channel_id].append((author_id, author_name, content))
    if len(conversation_history[channel_id]) > MAX_HISTORY_LENGTH:
        conversation_history[channel_id] = conversation_history[channel_id][-MAX_HISTORY_LENGTH:]

def get_active_users(channel_id):
    active_users = {}
    if channel_id in conversation_history:
        recent_history = conversation_history[channel_id][-20:]
        for author_id, author_name, _ in recent_history:
            if author_id != client.user.id:
                active_users[author_id] = author_name
    return active_users

# Funzioni per rendere il bot più umano
def get_random_response(keyword):
    responses = KEYWORD_RESPONSES.get(keyword, [])
    if responses:
        return random.choice(responses)
    return None

def maybe_add_typo(text):
    if random.random() < 0.15:
        words = text.split()
        if not words:
            return text
        idx = random.randint(0, len(words) - 1)
        word = words[idx]
        if len(word) <= 2:
            return text
        typo_type = random.choice(["swap", "omit", "duplicate", "replace"])
        if typo_type == "swap" and len(word) > 2:
            pos = random.randint(0, len(word) - 2)
            word = word[:pos] + word[pos + 1] + word[pos] + word[pos + 2:]
        elif typo_type == "omit" and len(word) > 3:
            pos = random.randint(0, len(word) - 1)
            word = word[:pos] + word[pos + 1:]
        elif typo_type == "duplicate":
            pos = random.randint(0, len(word) - 1)
            word = word[:pos] + word[pos] + word[pos:]
        elif typo_type == "replace" and len(word) > 2:
            keyboard = {
                'a': 'sqzw', 'b': 'vghn', 'c': 'xdfv', 'd': 'sfxce',
                'e': 'wrsdf', 'f': 'dcgvr', 'g': 'ftbhy', 'h': 'gyujn',
                'i': 'uojkl', 'j': 'huikm', 'k': 'jiolm', 'l': 'kop',
                'm': 'njk', 'n': 'bhjm', 'o': 'iklp', 'p': 'ol',
                'q': 'wa', 'r': 'edft', 's': 'awedxz', 't': 'rfgy',
                'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc',
                'y': 'tghu', 'z': 'asx'
            }
            pos = random.randint(0, len(word) - 1)
            char = word[pos].lower()
            if char in keyboard:
                replacement = random.choice(keyboard[char])
                if word[pos].isupper():
                    replacement = replacement.upper()
                word = word[:pos] + replacement + word[pos + 1:]
        words[idx] = word
        return ' '.join(words)
    return text

def maybe_add_filler(text):
    if random.random() < 0.3:
        filler = random.choice(human_traits["fillers"])
        return f"{filler}, {text.lower()}" if random.random() < 0.5 else f"{filler}... {text}"
    return text

def maybe_add_emoji(text):
    if random.random() < human_traits["emoji_prob"]:
        emoji = random.choice(human_traits["common_emoji"])
        return f"{text} {emoji}" if random.random() < 0.7 else f"{emoji} {text}"
    return text

def humanize_response(text):
    if random.random() < 0.2:
        text = text.replace("comunque", "cmq")
    if random.random() < 0.2:
        text = text.replace("perché", "xké")
    if random.random() < 0.15:
        text = text.replace("non", "nn")

    if random.random() < 0.4:
        text = maybe_add_filler(text)
    elif random.random() < 0.3:
        text = maybe_add_emoji(text)
    else:
        text = maybe_add_typo(text)

    if text.endswith(".") and random.random() < 0.4:
        text = text[:-1]

    if random.random() < 0.3 and len(text) > 0:
        text = text[0].lower() + text[1:]

    return text

def should_respond_to_message(message, message_content):
    current_time = asyncio.get_event_loop().time()
    if message.channel.id in last_response_time:
        time_since_last = current_time - last_response_time[message.channel.id]
        if time_since_last < 60:
            return False

    trigger_keywords = list(KEYWORD_RESPONSES.keys())
    trigger_keywords.extend(["help", "codice", "errore", "bug"])

    if any(keyword in message_content for keyword in trigger_keywords):
        return random.random() < 0.15

    if "?" in message_content and len(message_content) > 10:
        return random.random() < 0.20

    return random.random() < 0.05

async def maybe_add_reaction(message):
    if random.random() < human_traits["reaction_prob"]:
        reaction = random.choice(human_traits["common_emoji"])
        try:
            await message.add_reaction(reaction)
        except:
            pass

async def simulate_typing(channel, text):
    thinking_time = random.choice(typing_habits["thinking_time"]) * 0.7
    if len(text) > 100:
        thinking_time *= 1.2

    await asyncio.sleep(min(thinking_time, 1.5))

    typing_time = len(text) * random.choice(typing_habits["typing_speed"]) * 0.8

    if len(text) > 50:
        typing_time += random.choice(typing_habits["pauses"]) * 0.7

    async with channel.typing():
        await asyncio.sleep(min(typing_time, 3.5))

# Eventi del bot
@client.event
async def on_ready():
    print(f'\n🤖 {client.user} è online!\n')
    print('📊 Statistiche del Bot:')
    print(f'├── Server totali: {len(client.guilds)}')
    print(f'└── Utenti totali: {len(set(client.get_all_members()))}')
    
    print('\n📋 Lista dei Server:')
    for guild in client.guilds:
        print(f'├── {guild.name} (ID: {guild.id})')
        print(f'│   ├── Owner: {guild.owner}')
        print(f'│   └── Membri: {guild.member_count}')
    
    gaming_activities = [
        discord.Game("Minecraft"),
        discord.Game("Fortnite"),
        discord.Game("Call of Duty: Warzone"),
        discord.Game("League of Legends"),
        discord.Game("Valorant"),
        discord.Game("Apex Legends"),
        discord.Game("Among Us"),
        discord.Game("Rocket League"),
        discord.Activity(type=discord.ActivityType.playing, name="Visual Studio Code"),
        discord.Activity(type=discord.ActivityType.playing, name="con React"),
        discord.Activity(type=discord.ActivityType.listening, name="Spotify"),
        discord.Activity(type=discord.ActivityType.watching, name="tutorial su YouTube")
    ]

    current_activity = random.choice(gaming_activities)
    await client.change_presence(activity=current_activity, status=discord.Status.online)

    while True:
        await asyncio.sleep(random.randint(1800, 3600))
        new_activity = random.choice(gaming_activities)
        await client.change_presence(activity=new_activity, status=discord.Status.online)

# Gestione dei messaggi
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await maybe_add_reaction(message)

    update_conversation_history(message.channel.id, message.author.id, message.author.name, message.content)

    lower_msg = message.content.lower()
    mentioned = client.user in message.mentions
    active_users = get_active_users(message.channel.id)

    # Gestione menzioni dirette
    if mentioned:
        prompt = message.content.replace(f"<@{client.user.id}>", "").strip()
        if not prompt:
            choices = ["Dimmi tutto", "Che succede?", "Eccomi", "Mi hai chiamato?"]
            await message.channel.send(random.choice(choices))
            return

        # Get server-specific context
        guild_id = message.guild.id if message.guild else None
        channel_history = conversation_history.get(message.channel.id, [])

        # Gestione menzioni Discord
        cleaned_prompt = prompt
        if message.mentions:
            for mention in message.mentions:
                # Skip if it's our own mention
                if mention.id == client.user.id:
                    cleaned_prompt = cleaned_prompt.replace(f'<@{mention.id}>', 'me')
                    continue
                # Only allow mentions for users in the current server
                if guild_id and message.guild.get_member(mention.id):
                    cleaned_prompt = cleaned_prompt.replace(f'<@{mention.id}>', f'@{mention.display_name}')
                else:
                    cleaned_prompt = cleaned_prompt.replace(f'<@{mention.id}>', mention.name)

        await simulate_typing(message.channel, cleaned_prompt)
        response = await ask_openrouter(cleaned_prompt, channel_history, active_users)
        response = humanize_response(response)

        # Gestione menzioni Discord
        if guild_id:
            for member in message.guild.members:
                # Converti vecchi formati tag in nuovi
                old_formats = [
                    f'<@{member.id}>',
                    f'<@!{member.id}>',
                    f'@{member.name}',
                    member.name
                ]
                for old_format in old_formats:
                    if old_format in response:
                        response = response.replace(old_format, f'<@{member.id}>')

            # Assicurati che la risposta inizi con il tag se stiamo rispondendo all'utente
            if message.author.id != client.user.id and not any(response.startswith(prefix) for prefix in ['<@', '@']):
                response = f'<@{message.author.id}> {response}'


        await message.channel.send(response)
        update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
        last_response_time[message.channel.id] = asyncio.get_event_loop().time()
        return

    # Gestione comandi !ai
    if message.content.startswith("!ai"):
        prompt = message.content[4:].strip()
        if not prompt:
            await message.channel.send("Dimmi pure")
            return

        channel_history = conversation_history.get(message.channel.id, [])
        await simulate_typing(message.channel, prompt)
        response = await ask_openrouter(prompt, channel_history, active_users)
        response = humanize_response(response)
        await message.channel.send(response)
        update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
        last_response_time[message.channel.id] = asyncio.get_event_loop().time()
        return

    # Gestione parole chiave
    for keyword in KEYWORD_RESPONSES:
        if keyword in lower_msg:
            if random.random() < 0.8:
                response = get_random_response(keyword)
                if response:
                    await simulate_typing(message.channel, response)
                    if random.random() < 0.4:
                        response = humanize_response(response)
                    if random.random() < 0.3:
                        response = f"@{message.author.display_name} {response}"
                    await message.channel.send(response)
                    update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
                    last_response_time[message.channel.id] = asyncio.get_event_loop().time()
                    return

    # Gestione codice
    code_keywords = ["genera codice", "crea codice", "scrivi codice", "programma", "funzione per", "analizza codice", "controlla codice", "rivedi codice"]
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", message.content, re.DOTALL)

    if any(keyword in lower_msg for keyword in code_keywords) or code_blocks:
        if code_blocks:
            for code in code_blocks:
                response = await analyze_code(code)
                await message.channel.send(humanize_response(response))
        else:
            response = await generate_code(message.content)
            await message.channel.send(humanize_response(response))
        return

    # Gestione risposte automatiche
    if should_respond_to_message(message, lower_msg):
        channel_history = conversation_history.get(message.channel.id, [])
        await simulate_typing(message.channel, message.content)
        response = await ask_openrouter(message.content, channel_history, active_users)
        response = humanize_response(response)

        if random.random() < 0.25 and not any(f"<@{uid}" in response for uid in active_users.keys()):
            if message.author.id != client.user.id:
                response = f"@{message.author.display_name} {response}"

        await message.channel.send(response)
        update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
        last_response_time[message.channel.id] = asyncio.get_event_loop().time()

# Avvio del bot
client.run(DISCORD_TOKEN)