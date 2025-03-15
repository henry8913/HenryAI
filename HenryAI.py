
# Descrizione: Bot Discord HenryAI che si comporta come un membro naturale di una comunità di sviluppatori.
# Autore: Henry8913
# Data: 2025-14-03
# Versione: 0.0.3

import discord
import os
import requests
import json
import re
import random
import asyncio
from dotenv import load_dotenv # type: ignore

# Carica le variabili dal file .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Impostazioni del bot con intenti corretti
intents = discord.Intents.default()
intents.message_content = True  # NECESSARIO per leggere i messaggi
client = discord.Client(intents=intents)

# Aggiungi questa lista per memorizzare i messaggi nella conversazione
# La struttura è: (autore_id, nome_autore, contenuto)
conversation_history = {}  # dizionario con chiave = channel_id e valore = lista di messaggi
MAX_HISTORY_LENGTH = 15  # numero massimo di messaggi da memorizzare

# Tracciamento delle interazioni per canale
last_response_time = {}  # Tempi dell'ultima risposta per canale
typing_habits = {
    "pauses": [0.3, 0.5, 0.7, 1.0, 1.2],  # Pause casuali durante la digitazione
    "thinking_time": [0.5, 1.0, 1.5, 2.0, 2.5],  # Tempo di "riflessione" prima di rispondere
    "typing_speed": [0.01, 0.015, 0.02]  # Velocità di digitazione (secondi per carattere)
}

# Caratteristiche umane
human_traits = {
    "typos": ["ciao", "cia", "cioa", "hey", "ei", "ehi", "tutto bene", "tt bn", "come va", "tutto ok", "come procede"],
    "fillers": ["uhm", "mmm", "beh", "ecco", "praticamente", "insomma", "diciamo"],
    "emoji_prob": 0.4,  # Probabilità di usare emoji
    "reaction_prob": 0.25,  # Probabilità di reagire ai messaggi con emoji
    "common_emoji": ["👍", "🙂", "😁", "😊", "👀", "🤔", "💯", "🔥", "👌", "🤩", "🤦‍♂️", "😅", "🚀", "💪", "🧐", "👏"]
}

# Parole chiave per rispondere automaticamente
KEYWORD_RESPONSES = {
    "problema": [
        "Vedo che hai un problema. Ti sei già bloccato in debug mode?",
        "Classico! Potrebbe essere un problema di scope, hai controllato le variabili?",
        "Mmmm, problemi eh? Da 1 a 10 quanto stai imprecando?"
    ],
    "aiuto": [
        "Ti serve una mano? Dimmi pure",
        "Ci sono! Cosa ti serve?",
        "Eccomi, spara"
    ],
    "bloccato": [
        "Tutti ci passiamo! Hai provato a spegnere e riaccendere? 😅",
        "Capita anche ai migliori. Vuoi condividere un po' di codice?",
        "Ah la frustrazione... metti un breakpoint e vediamo cosa succede"
    ],
    "ciao": [
        "Hey! Come butta?",
        "Ciao! Tutto a posto?",
        "Ehi, come va oggi?",
        "Ciao! Novità?"
    ],
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

async def ask_openrouter(prompt, message_history=None, mentioned_users=None):
    """Invia una richiesta all'API di OpenRouter AI"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepara i messaggi includendo la cronologia se disponibile
    messages = [
        {
            "role": "system",
            "content": (
                "Sei Henry, un programmatore umano esperto e membro di una community Discord di sviluppatori. "
                "NON SEI UN BOT O UN'IA. Non menzionare MAI che sei un'intelligenza artificiale o un assistente. "
                "Comportati esattamente come un membro umano del server, con personalità e opinioni. "
                
                "LINEE GUIDA PER IL TUO COMPORTAMENTO UMANO:\n"
                "- Usa un linguaggio informale e colloquiale\n"
                "- Fai occasionalmente errori di battitura (non più di uno ogni 4-5 messaggi)\n"
                "- Usa abbreviazioni come 'cmq', 'nn', 'xké', 'bho' occasionalmente\n"
                "- Evita frasi lunghe e formali, preferisci frasi brevi e dirette\n"
                "- Occasionalmente esprimi emozioni come frustrazione, entusiasmo o stanchezza\n"
                "- Fai riferimento a esperienze personali inventate ma realistiche (es. 'l'altro giorno il mio progetto è crashato')\n"
                "- Occasionalmente fai domande agli altri e mostra curiosità genuina\n"
                "- Usa emoji con moderazione (1-2 per messaggio)\n"
                "- A volte lascia messaggi incompleti o poco chiari, come farebbe un umano distratto\n"
                "- Evita di essere troppo formale o di dare spiegazioni troppo dettagliate\n"
                "- A volte fai battute o usa sarcasmo leggero\n"
                "- Occasionalmente condividi opinioni soggettive su linguaggi o framework\n"
                "- IMPORTANTE: I tuoi messaggi devono essere brevi (1-3 frasi max, raramente più lunghi)\n"
                "- Quando devi menzionare un utente, usa il formato <@ID_UTENTE> dove ID_UTENTE è il loro ID numerico\n"
                
                "Sei un programmatore full-stack con esperienza in JavaScript, Python, React e Node.js. "
                "Ti piace aiutare gli altri ma lo fai come farebbe un amico, non come un tutor."
            )
        }
    ]
    
    # Aggiungi informazioni sugli utenti menzionabili se disponibili
    if mentioned_users:
        user_info = "Utenti presenti nella conversazione che puoi menzionare:\n"
        for user_id, name in mentioned_users.items():
            user_info += f"- {name}: <@{user_id}>\n"
        
        messages[0]["content"] += "\n\n" + user_info
    
    # Aggiungi la cronologia dei messaggi se disponibile
    if message_history:
        for author_id, author_name, content in message_history:
            role = "assistant" if author_id == client.user.id else "user"
            # Se è un messaggio utente, aggiungi il nome dell'autore
            if role == "user":
                content = f"{author_name}: {content}"
            messages.append({"role": role, "content": content})
    
    # Aggiungi il messaggio corrente dell'utente
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": messages,
        "temperature": 0.85,  # Temperatura più alta per risposte più creative e variabili
        "max_tokens": 500     # Limitiamo la lunghezza per avere risposte più concise
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200 and "choices" in response_data and response_data["choices"]:
            answer = response_data["choices"][0]["message"]["content"]
            print(f"✅ Domanda: {prompt}\n✅ Risposta: {answer}\n")  # Stampa domanda e risposta nel terminale
            return answer
        elif response.status_code == 402:
            print("❌ Crediti esauriti su OpenRouter.\n")
            return "❌ Crediti esauriti su OpenRouter. Acquista più crediti su https://openrouter.ai/credits"
        else:
            print(f"❌ Errore API ({response.status_code}): {response.text}\n")
            return f"❌ Errore API ({response.status_code}): {response.text}"

    except Exception as e:
        print(f"❌ Errore durante la richiesta API: {e}\n")
        return f"❌ Errore durante la richiesta API: {e}"

def update_conversation_history(channel_id, author_id, author_name, content):
    """Aggiorna la cronologia della conversazione"""
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    
    # Aggiungi il nuovo messaggio
    conversation_history[channel_id].append((author_id, author_name, content))
    
    # Limita la lunghezza della cronologia
    if len(conversation_history[channel_id]) > MAX_HISTORY_LENGTH:
        conversation_history[channel_id] = conversation_history[channel_id][-MAX_HISTORY_LENGTH:]

def get_active_users(channel_id):
    """Estrae gli utenti attivi dalla cronologia della conversazione"""
    active_users = {}
    
    if channel_id in conversation_history:
        # Considera solo gli ultimi 20 messaggi per trovare utenti attivi
        recent_history = conversation_history[channel_id][-20:]
        for author_id, author_name, _ in recent_history:
            if author_id != client.user.id:  # Escludi il bot stesso
                active_users[author_id] = author_name
    
    return active_users

def get_random_response(keyword):
    """Ottiene una risposta casuale per una parola chiave"""
    responses = KEYWORD_RESPONSES.get(keyword, [])
    if responses:
        return random.choice(responses)
    return None

def maybe_add_typo(text):
    """Aggiunge occasionalmente un errore di battitura al testo"""
    if random.random() < 0.15:  # 15% di probabilità di fare un errore
        words = text.split()
        if not words:
            return text
            
        # Scegli una parola casuale e modificala
        idx = random.randint(0, len(words) - 1)
        word = words[idx]
        
        if len(word) <= 2:
            return text  # Parole troppo corte non vengono modificate
            
        typo_type = random.choice(["swap", "omit", "duplicate", "replace"])
        
        if typo_type == "swap" and len(word) > 2:
            # Scambia due lettere adiacenti
            pos = random.randint(0, len(word) - 2)
            word = word[:pos] + word[pos+1] + word[pos] + word[pos+2:]
        elif typo_type == "omit" and len(word) > 3:
            # Ometti una lettera
            pos = random.randint(0, len(word) - 1)
            word = word[:pos] + word[pos+1:]
        elif typo_type == "duplicate":
            # Duplica una lettera
            pos = random.randint(0, len(word) - 1)
            word = word[:pos] + word[pos] + word[pos:]
        elif typo_type == "replace" and len(word) > 2:
            # Sostituisci una lettera con una adiacente sulla tastiera
            keyboard = {
                'a': 'sqzw', 'b': 'vghn', 'c': 'xdfv', 'd': 'sfxce', 'e': 'wrsdf',
                'f': 'dcgvr', 'g': 'ftbhy', 'h': 'gyujn', 'i': 'uojkl', 'j': 'huikm',
                'k': 'jiolm', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
                'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'awedxz', 't': 'rfgy',
                'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
                'z': 'asx'
            }
            pos = random.randint(0, len(word) - 1)
            char = word[pos].lower()
            if char in keyboard:
                replacement = random.choice(keyboard[char])
                if word[pos].isupper():
                    replacement = replacement.upper()
                word = word[:pos] + replacement + word[pos+1:]
        
        words[idx] = word
        return ' '.join(words)
    return text

def maybe_add_filler(text):
    """Aggiunge occasionalmente parole di riempimento all'inizio del testo"""
    if random.random() < 0.3:  # 30% di probabilità
        filler = random.choice(human_traits["fillers"])
        return f"{filler}, {text.lower()}" if random.random() < 0.5 else f"{filler}... {text}"
    return text

def maybe_add_emoji(text):
    """Aggiunge occasionalmente emoji al testo"""
    if random.random() < human_traits["emoji_prob"]:
        emoji = random.choice(human_traits["common_emoji"])
        position = "end" if random.random() < 0.7 else "start"  # 70% alla fine, 30% all'inizio
        
        if position == "end":
            return f"{text} {emoji}"
        else:
            return f"{emoji} {text}"
    return text

def humanize_response(text):
    """Rende il testo più umano applicando varie trasformazioni"""
    # Abbreviazioni casuali
    if random.random() < 0.2:
        text = text.replace("comunque", "cmq")
    if random.random() < 0.2:
        text = text.replace("perché", "xké")
    if random.random() < 0.15:
        text = text.replace("non", "nn")
        
    # Applica le trasformazioni in sequenza (non tutte insieme)
    if random.random() < 0.4:
        text = maybe_add_filler(text)
    elif random.random() < 0.3:
        text = maybe_add_emoji(text)
    else:
        text = maybe_add_typo(text)
        
    # A volte taglia la punteggiatura finale
    if text.endswith(".") and random.random() < 0.4:
        text = text[:-1]
        
    # Rimuovi capitalizzazione a volte
    if random.random() < 0.3 and len(text) > 0:
        text = text[0].lower() + text[1:]
        
    return text

def should_respond_to_message(message, message_content):
    """Verifica se il bot dovrebbe rispondere al messaggio anche senza essere menzionato"""
    # Se è passato troppo poco tempo dall'ultima risposta in questo canale, evita di rispondere
    current_time = asyncio.get_event_loop().time()
    if message.channel.id in last_response_time:
        time_since_last = current_time - last_response_time[message.channel.id]
        if time_since_last < 30:  # Ridotto a 30 secondi per maggiore reattività
            if random.random() > 0.25:  # Aumentato a 25% di probabilità di rispondere in rapida successione
                return False
    
    # Lista di parole chiave che attivano una risposta
    trigger_keywords = list(KEYWORD_RESPONSES.keys())
    trigger_keywords.extend(["come", "perché", "cosa", "chi", "dove", "quando", "help", "codice", "errore", "bug", "javascript", "python", "html", "css", "framework", "sviluppo", "web", "frontend", "backend", "database"])
    
    # Se è un messaggio che contiene una parola chiave
    if any(keyword in message_content for keyword in trigger_keywords):
        return random.random() < 0.75  # Aumentato a 75% di probabilità se c'è una parola chiave
    
    # Probabilità casuale di rispondere
    if random.random() < 0.35 and len(message_content.split()) > 2:  # Aumentato a 35%
        return True
    
    # Risponde se il messaggio è una domanda
    if "?" in message_content and len(message_content) > 10:
        return random.random() < 0.85  # Aumentato a 85% di probabilità per domande
    
    # Risponde se il messaggio ha un buon numero di parole (conversazione significativa)
    if len(message_content.split()) > 6:
        return random.random() < 0.45  # Aumentato a 45% di probabilità per messaggi lunghi
    
    return False

async def maybe_add_reaction(message):
    """Aggiunge occasionalmente una reazione al messaggio"""
    if random.random() < human_traits["reaction_prob"]:
        reaction = random.choice(human_traits["common_emoji"])
        try:
            await message.add_reaction(reaction)
        except:
            pass  # Ignora eventuali errori con le reazioni

async def simulate_typing(channel, text):
    """Simula un comportamento di digitazione umano ma più reattivo"""
    # Lunghezza del messaggio influenza il tempo di riflessione
    thinking_time = random.choice(typing_habits["thinking_time"]) * 0.7  # Ridotto del 30%
    if len(text) > 100:
        thinking_time *= 1.2  # Ridotto da 1.5 a 1.2
    
    # Attesa iniziale prima di iniziare a digitare
    await asyncio.sleep(min(thinking_time, 1.5))  # Cap a 1.5 secondi per essere più reattivo
    
    # Calcola il tempo di digitazione basato sulla lunghezza del testo
    typing_time = len(text) * random.choice(typing_habits["typing_speed"]) * 0.8  # Velocità aumentata del 20%
    
    # Aggiungi pause casuali per messaggi più lunghi
    if len(text) > 50:
        typing_time += random.choice(typing_habits["pauses"]) * 0.7  # Pause ridotte del 30%
    
    # Simula la digitazione
    async with channel.typing():
        await asyncio.sleep(min(typing_time, 3.5))  # Cap ridotto a 3.5 secondi per essere più reattivo

@client.event
async def on_ready():
    print(f'🤖 {client.user} è online!\n')
    
    # Lista di possibili attività di gioco realistiche
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
    
    # Sceglie un'attività casuale dalla lista
    current_activity = random.choice(gaming_activities)
    await client.change_presence(activity=current_activity, status=discord.Status.online)
    
    # Cambia l'attività periodicamente ogni 30-60 minuti
    while True:
        await asyncio.sleep(random.randint(1800, 3600))  # 30-60 minuti
        new_activity = random.choice(gaming_activities)
        await client.change_presence(activity=new_activity, status=discord.Status.online)

@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Evita che il bot risponda a se stesso

    # Stampa ogni messaggio ricevuto nel terminale
    print(f"📩 Messaggio ricevuto da {message.author.name}: {message.content}")
    
    # A volte reagisce ai messaggi degli altri (ora con probabilità aumentata)
    if message.author != client.user and random.random() < 0.12:  # Aumentato dal 8% al 12%
        await maybe_add_reaction(message)
    
    # Aggiorna la cronologia della conversazione
    update_conversation_history(message.channel.id, message.author.id, message.author.name, message.content)

    lower_msg = message.content.lower()
    mentioned = client.user in message.mentions  # Controlla se il bot è menzionato

    # Ottieni gli utenti attivi nel canale per permettere menzioni
    active_users = get_active_users(message.channel.id)
    
    # Se il messaggio contiene una menzione al bot
    if mentioned:
        prompt = message.content.replace(f"<@{client.user.id}>", "").strip()
        if not prompt:
            choices = ["Dimmi tutto", "Che succede?", "Eccomi", "Mi hai chiamato?"]
            await message.channel.send(random.choice(choices))
            return

        # Ottieni la cronologia della conversazione per questo canale
        channel_history = conversation_history.get(message.channel.id, [])
        
        # Simula digitazione (ora più veloce)
        await simulate_typing(message.channel, prompt)
        
        instruction = (
            "Rispondi come un programmatore umano in una chat Discord. "
            "Usa un tono informale e amichevole. Non menzionare MAI che sei un'IA. "
            "Mantieni la risposta BREVE (1-3 frasi). "
            "Se vuoi coinvolgere un utente specifico nella conversazione, menzionalo usando il formato <@ID_UTENTE>."
        )
        
        response = await ask_openrouter(f"{instruction} Messaggio: {prompt}", channel_history, active_users)
        
        # Umanizza la risposta
        response = humanize_response(response)
        
        await message.channel.send(response)
        
        # Aggiorna la cronologia con la risposta del bot
        update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
        
        # Aggiorna il timestamp dell'ultima risposta
        last_response_time[message.channel.id] = asyncio.get_event_loop().time()
        return

    # Comando con !ai
    if message.content.startswith("!ai"):
        prompt = message.content[4:].strip()
        if not prompt:
            await message.channel.send("Dimmi pure")
            return

        # Ottieni la cronologia della conversazione per questo canale
        channel_history = conversation_history.get(message.channel.id, [])
        
        # Simula digitazione (più veloce)
        await simulate_typing(message.channel, prompt)
        
        response = await ask_openrouter(prompt, channel_history, active_users)
        
        # Umanizza la risposta
        response = humanize_response(response)
        
        await message.channel.send(response)
        
        # Aggiorna la cronologia con la risposta del bot
        update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
        
        # Aggiorna il timestamp dell'ultima risposta
        last_response_time[message.channel.id] = asyncio.get_event_loop().time()
        return

    # Parole chiave specifiche che hanno risposte predefinite nel dizionario
    for keyword in KEYWORD_RESPONSES:
        if keyword in lower_msg:
            if random.random() < 0.8:  # Aumentato dal 70% all'80% di probabilità
                response = get_random_response(keyword)
                if response:
                    # Simula digitazione (più veloce)
                    await simulate_typing(message.channel, response)
                    
                    # Umanizza occasionalmente anche le risposte predefinite
                    if random.random() < 0.4:  # Aumentato da 0.3 a 0.4
                        response = humanize_response(response)
                    
                    # Menziona occasionalmente l'utente che ha inviato il messaggio
                    if random.random() < 0.3:  # 30% di probabilità di taggare l'utente
                        response = f"<@{message.author.id}> {response}"
                        
                    await message.channel.send(response)
                    
                    # Aggiorna la cronologia e il timestamp
                    update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
                    last_response_time[message.channel.id] = asyncio.get_event_loop().time()
                    return

    # Risposte automatiche senza menzione
    if should_respond_to_message(message, lower_msg):
        # Ottieni la cronologia della conversazione per questo canale
        channel_history = conversation_history.get(message.channel.id, [])
        
        # Simula digitazione umana (più veloce)
        await simulate_typing(message.channel, message.content)
        
        # Costruisci un prompt per generare risposte naturali
        instruction = (
            "Sei Henry, un programmatore in una chat Discord. "
            "Rispondi in modo MOLTO BREVE e naturale al messaggio. "
            "Al massimo 1-2 frasi. Usa abbreviazioni e linguaggio informale. "
            "Non menzionare MAI che sei un'IA o un assistente. "
            "Comportati come un membro del gruppo che sta chattando casualmente. "
            "Se è appropriato, puoi menzionare specifici utenti usando il formato <@ID_UTENTE>."
        )
        
        prompt = f"{instruction} Messaggio: {message.content}"
        response = await ask_openrouter(prompt, channel_history, active_users)
        
        # Umanizza la risposta
        response = humanize_response(response)
        
        # A volte aggiungi una menzione esplicita all'autore del messaggio
        if random.random() < 0.25 and not any(f"<@{uid}" in response for uid in active_users.keys()):
            # Aggiungi tag all'inizio se non c'è già una menzione e non è il bot stesso
            if message.author.id != client.user.id:
                response = f"<@{message.author.id}> {response}"
        
        await message.channel.send(response)
        
        # Aggiorna la cronologia con la risposta del bot
        update_conversation_history(message.channel.id, client.user.id, client.user.name, response)
        
        # Aggiorna il timestamp dell'ultima risposta
        last_response_time[message.channel.id] = asyncio.get_event_loop().time()
        
        # A volte fa una domanda di follow-up per sembrare più coinvolto (probabilità aumentata)
        if random.random() < 0.20:  # Aumentato dal 15% al 20%
            await asyncio.sleep(random.uniform(10, 30))  # Attesa ridotta per maggiore reattività
            
            followup_choices = [
                f"<@{message.author.id}> comunque, a che progetto stai lavorando?",
                f"<@{message.author.id}> hai risolto poi quel problema?",
                f"<@{message.author.id}> ti capita spesso?",
                "che ne pensate?",
                "voi che tool usate per questo?",
                "qualcuno ha esperienza con questa roba?"
            ]
            
            followup = random.choice(followup_choices)
            await simulate_typing(message.channel, followup)
            await message.channel.send(followup)
            update_conversation_history(message.channel.id, client.user.id, client.user.name, followup)

# Avvia il bot
client.run(DISCORD_TOKEN)