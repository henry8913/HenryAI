
# HenryAI - Bot Discord con comportamento umano

HenryAI è un bot Discord che simula il comportamento di un membro umano di una community di sviluppatori. A differenza dei bot tradizionali, HenryAI è progettato per partecipare alle conversazioni in modo naturale, mostrando personalità e comportamenti tipicamente umani.

<p align="center">
    <img src="./img/cover.jpg" alt="Cover" width="100%" />
</p>

## Caratteristiche principali

- 🧠 **Comportamento umano**: Risponde in modo informale, usa espressioni colloquiali, fa errori di battitura occasionali e mostra emozioni.
- 💬 **Risposte contestuali**: Tiene traccia della cronologia della conversazione per fornire risposte pertinenti al contesto.
- 🔑 **Risponde a parole chiave**: Rileva automaticamente parole chiave come "problema", "aiuto", "javascript", ecc.
- 👋 **Interazione naturale**: Reagisce ai messaggi, fa domande di follow-up e menziona gli utenti.
- 🤖 **Powered by Claude AI**: Utilizza l'API di OpenRouter per accedere a modelli avanzati come Claude 3 Haiku.

## Requisiti

- Python 3.8+
- Token Discord Bot
- API Key di OpenRouter

## Installazione

### 1. Clona il repository 

#### Opzione 1: Clona localmente
```bash
git clone https://github.com/henry8913/HenryAI.git
cd HenryAI
```

### 2. Configurazione delle variabili d'ambiente

Crea un file `.env` nella directory principale del progetto con i seguenti valori:

```
DISCORD_TOKEN=il_tuo_token_discord
OPENROUTER_API_KEY=la_tua_api_key_openrouter
```

In alternativa, puoi usare lo strumento "Secrets" di Replit:
1. Vai nella scheda "Secrets" nel tuo repl
2. Aggiungi una chiave `DISCORD_TOKEN` con il tuo token Discord Bot
3. Aggiungi una chiave `OPENROUTER_API_KEY` con la tua API key di OpenRouter

### 3. Installa le dipendenze

Le dipendenze sono elencate nel file `requirements.txt`. Per installarle:

```bash
pip3 install -r requirements.txt
```

### 4. Avvia il bot

Esegui il file principale:

```bash
python3 HenryAI.py
```

## Come ottenere i token necessari

### Discord Token
1. Vai su [Discord Developer Portal](https://discord.com/developers/applications)
2. Crea una nuova applicazione
3. Vai nella sezione "Bot" e crea un bot
4. Copia il token
5. Nelle sezioni "Privileged Gateway Intents", abilita "Message Content Intent"

### OpenRouter API Key
1. Registrati su [OpenRouter](https://openrouter.ai/)
2. Vai nella sezione API Keys
3. Genera e copia la tua API key

## Personalizzazione

Puoi personalizzare il comportamento del bot modificando le seguenti sezioni in `HenryAI.py`:

### Comportamento umano
Modifica le variabili nel dizionario `human_traits` per cambiare la frequenza di errori di battitura, l'uso di emoji e le espressioni di riempimento.

```python
human_traits = {
    "typos": ["ciao", "cia", "cioa", "hey", "ei", "ehi"],
    "fillers": ["uhm", "mmm", "beh", "ecco", "praticamente"],
    "emoji_prob": 0.4,  # Probabilità di usare emoji
    "reaction_prob": 0.25,  # Probabilità di reagire ai messaggi con emoji
    "common_emoji": ["👍", "🙂", "😁", "😊", "👀", "🤔", "💯"]
}
```

### Parole chiave
Aggiungi o modifica le risposte a parole chiave nel dizionario `KEYWORD_RESPONSES`:

```python
KEYWORD_RESPONSES = {
    "problema": [
        "Vedo che hai un problema. Ti sei già bloccato in debug mode?",
        "Classico! Potrebbe essere un problema di scope, hai controllato le variabili?"
    ],
    # Aggiungi altre parole chiave qui
}
```

### Modello AI
Cambia il modello AI utilizzato modificando il parametro `model` nella funzione `ask_openrouter`:

```python
data = {
    "model": "anthropic/claude-3-haiku",  # Cambia con un altro modello supportato da OpenRouter
    "messages": messages,
    "temperature": 0.85,  # Controlla la creatività delle risposte
    "max_tokens": 500     # Lunghezza massima della risposta
}
```

## Contribuire

Questo progetto è open source. Sentiti libero di:
1. Forkare il repository
2. Creare un branch per le tue modifiche
3. Inviare una pull request

## Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file LICENSE per i dettagli.

---

## 🤝 Contributi
Le contribuzioni sono sempre benvenute! Apri una **issue** o invia un **pull request** per suggerire modifiche.

---

## 👤 Autore
[Henry](https://github.com/henry8913)
