import discord
from discord.ext import commands
from groq import Groq
import requests
import os # Biblioteca para ler as chaves escondidas
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "O bot guloso está online e a enganar o sistema!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# Em vez de ter o texto colado aqui, ele vai puxar do servidor do Render!
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# O resto do teu código continua igual para baixo...
# O link do seu Firebase guloso
FIREBASE_URL = "https://batatadocegamer-bot-default-rtdb.firebaseio.com"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
groq_client = Groq(api_key=GROQ_API_KEY)

# --- SISTEMA DE BANCO DE DADOS (FIREBASE) ---
def get_user_data(user_id):
    # Puxa os dados do cara lá do Firebase
    url = f"{FIREBASE_URL}/users/{user_id}.json"
    resposta = requests.get(url)
    dados = resposta.json()
    
    if dados is None:
        # Se o cara não existir, cria ele com 1k bom e 0 ruim
        novos_dados = {"good_points": 1000, "bad_points": 0}
        requests.put(url, json=novos_dados)
        return novos_dados
        
    return dados

def add_bad_points(user_id, points):
    dados_atuais = get_user_data(user_id)
    novos_pontos_ruins = dados_atuais["bad_points"] + points
    
    # Atualiza só os pontos ruins lá no banco
    url = f"{FIREBASE_URL}/users/{user_id}.json"
    requests.patch(url, json={"bad_points": novos_pontos_ruins})
    
    return novos_pontos_ruins

# --- EVENTOS DO BOT ---
@bot.event
async def on_ready():
    print(f"🔥 {bot.user} tá online, conectado no Firebase e pronto pra punir os betas!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # MÓDULO DE MODERAÇÃO
    mod_prompt = f"Você é um moderador de Discord. A mensagem a seguir contém ofensas graves, racismo, spam ou quebra de regras? Responda APENAS com 'SIM' ou 'NAO'. Mensagem: '{message.content}'"
    mod_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": mod_prompt}],
        model="llama3-8b-8192",
        max_tokens=10
    )
    
    is_toxic = "SIM" in mod_response.choices[0].message.content.upper()

    if is_toxic:
        total_bad = add_bad_points(message.author.id, 2500)
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}, você falou merda. +2500 pontos ruins. (Total: {total_bad}/10000)")

        if total_bad >= 10000:
            try:
                await message.author.timeout(timedelta(days=28), reason="Atingiu 10.000 pontos ruins.")
                await message.channel.send(f"🔨 {message.author.mention} foi de base! Bateu 10k de pontos ruins e tomou silêncio no servidor inteiro. Beta demais.")
            except Exception as e:
                print(f"Erro ao tentar mutar: {e}")

    # MÓDULO DE CONVERSA (Groq)
    elif bot.user in message.mentions:
        clean_msg = message.content.replace(f'<@{bot.user.id}>', '').strip()
        chat_prompt = f"Você é um bot administrador super inteligente, gentil e útil de um servidor do Discord. Responda a esta mensagem na língua do usuário ajudando no que for preciso para o bem do servidor: {clean_msg}"
        
        chat_response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": chat_prompt}],
            model="llama3-70b-8192"
        )
        await message.channel.send(chat_response.choices[0].message.content)

    await bot.process_commands(message)
keep_alive()
def run():
    # O Render vai dar a porta certa, se não der, a gente usa a 8080
    porta = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=porta)
