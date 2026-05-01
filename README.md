import discord
from discord.ext import commands
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot online')

def run_web():
    server = HTTPServer(('0.0.0.0', 3000), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()

# ================= CONFIG =================
BOT_AVATAR = "https://media.discordapp.net/attachments/1499137895900909740/1499171139958738995/ChatGPT_Image_29_de_abr._de_2026_16_59_39.png?ex=69f524ed&is=69f3d36d&hm=67f756de4bf1c775963f51e3795221f838613b8bdea31a65133bef5a20b4cb80&=&format=webp&quality=lossless&width=756&height=756"
BANNER = "https://media.discordapp.net/attachments/1499137895900909740/1499171141233807360/29_de_abr._de_2026_13_19_52.png?ex=69f524ed&is=69f3d36d&hm=398dd60719c5d4f3965667f85f482086f8e8ad04d86fb8f5f4f68696c4b9ad9a&=&format=webp&quality=lossless&width=806&height=336"

VALORES = [10000, 5000, 2000, 1000, 700, 500, 300, 200, 100, 70, 30]

PAINEIS = [
    1463209165861425300, 1463209212594229495, 1462602741628276780,
    1462602742907535563, 1463209294370701395, 1463209206038528226,
    1463209298279530615, 1462602747563213021, 1470413163441688667,
    1470413310582198335, 1470413356090523824, 1470413418640048182,
    1463209303409426456, 1462602750146646180, 1463209255875117190
]

CANAL_RANK = 1462602717099720718
CANAL_PIX = 1463562240744755261
CANAL_MED = 1462602782849761310

# ================= BANCO =================
filas = {v: [] for v in VALORES}
ranking = {}
fila_mediadores = []
pix_db = {}

# ================= UTIL =================
def formatar(valor):
    return f"R${valor/100:.2f}"

def salvar():
    with open("dados.json", "w") as f:
        json.dump({
            "ranking": ranking,
            "mediadores": fila_mediadores,
            "pix": pix_db
        }, f)

def carregar():
    global ranking, fila_mediadores, pix_db
    try:
        with open("dados.json") as f:
            data = json.load(f)
            ranking = data.get("ranking", {})
            fila_mediadores = data.get("mediadores", [])
            pix_db = data.get("pix", {})
    except:
        pass

# ================= EMBEDS =================
def embed_fila(valor):
    lista = "🚫 Ninguém na fila" if not filas[valor] else "\n".join([f"<@{j}>" for j in filas[valor]])

    embed = discord.Embed(
        title="🎰 FILA DE APOSTA",
        description=(
            f"💰 Valor: {formatar(valor)}\n"
            f"💸 Pagar: {formatar(valor+5)}\n\n"
            f"👥 Jogadores:\n{lista}\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚙️ Sistema automático • Seguro"
        ),
        color=0x2ecc71
    )

    embed.set_thumbnail(url=BOT_AVATAR)  # corrigido aqui
    embed.set_image(url=BANNER)

    return embed


def embed_mediadores():
    lista = "🚫 Nenhum mediador" if not fila_mediadores else "\n".join([f"<@{m}>" for m in fila_mediadores])

    embed = discord.Embed(
        title="🛠️ Mediadores Online",
        description=lista,
        color=0x3498db
    )

    embed.set_thumbnail(url=BOT_AVATAR)
    embed.set_image(url=BANNER)

    return embed

# ================= FILA =================
class FilaView(discord.ui.View):
    def __init__(self, valor):
        super().__init__(timeout=None)
        self.valor = valor

        self.entrar_btn.custom_id = f"fila_entrar_{valor}"
        self.sair_btn.custom_id = f"fila_sair_{valor}"

    @discord.ui.button(label="🎮 Entrar", style=discord.ButtonStyle.success)
    async def entrar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not fila_mediadores:
            return await interaction.response.send_message("❌ Sem mediador disponível", ephemeral=True)

        if interaction.user.id in filas[self.valor]:
            return await interaction.response.send_message("Você já está na fila", ephemeral=True)

        filas[self.valor].append(interaction.user.id)

        await interaction.response.edit_message(
            embed=embed_fila(self.valor),
            view=self
        )

    @discord.ui.button(label="🚪 Sair", style=discord.ButtonStyle.danger)
    async def sair_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id not in filas[self.valor]:
            return await interaction.response.send_message("Você não está na fila", ephemeral=True)

        filas[self.valor].remove(interaction.user.id)

        await interaction.response.edit_message(
            embed=embed_fila(self.valor),
            view=self
        )

# ================= PIX =================
class PixModal(discord.ui.Modal, title="Configurar PIX"):
    chave = discord.ui.TextInput(label="Chave PIX")
    tipo = discord.ui.TextInput(label="Tipo")
    nome = discord.ui.TextInput(label="Nome")

    async def on_submit(self, interaction: discord.Interaction):
        pix_db[str(interaction.user.id)] = {
            "nome": str(self.nome),
            "tipo": str(self.tipo),
            "chave": str(self.chave)
        }
        salvar()
        await interaction.response.send_message("✅ PIX salvo!", ephemeral=True)

class PixView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💸 Configurar PIX", style=discord.ButtonStyle.success, custom_id="pix_config")
    async def pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PixModal())

# ================= RANK =================
class RankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.page = 0

    def embed(self):
        if not ranking:
            return discord.Embed(description="🚫 Sem ranking ainda", color=0xe74c3c)

        ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

        start = self.page * 10
        end = start + 10
        dados = ordenado[start:end]

        texto = ""
        for i, (user, wins) in enumerate(dados, start=start+1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}°"
            texto += f"{medal} <@{user}> — **{wins} vitórias**\n"

        total = (len(ordenado)-1)//10+1

        embed = discord.Embed(
            title="🏆 Ranking Global",
            description=f"{texto}\n📄 Página {self.page+1}/{total}",
            color=0xf1c40f
        )
        embed.set_thumbnail(url=BOT_AVATAR)
        embed.set_image(url=BANNER)
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary, custom_id="rank_prev")
    async def prev(self, i: discord.Interaction, b: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await i.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, custom_id="rank_next")
    async def next(self, i: discord.Interaction, b: discord.ui.Button):
        if self.page < (len(ranking)-1)//10:
            self.page += 1
        await i.response.edit_message(embed=self.embed(), view=self)

# ================= MEDIADOR =================
class MedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar", style=discord.ButtonStyle.success, custom_id="med_entrar")
    async def entrar(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id not in fila_mediadores:
            fila_mediadores.append(i.user.id)
            salvar()
        await i.response.edit_message(embed=embed_mediadores(), view=self)

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, custom_id="med_sair")
    async def sair(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id in fila_mediadores:
            fila_mediadores.remove(i.user.id)
            salvar()
        await i.response.edit_message(embed=embed_mediadores(), view=self)

# ================= READY =================
@bot.event
async def on_ready():
    carregar()

    bot.add_view(PixView())
    bot.add_view(RankView())
    bot.add_view(MedView())

    for v in VALORES:
        bot.add_view(FilaView(v))

    print(f"✅ ONLINE COMO {bot.user}")

    # recriar painéis
    for canal_id in PAINEIS:
        canal = bot.get_channel(canal_id)
        if canal:
            await canal.purge(limit=50)
            for v in VALORES:
                await canal.send(embed=embed_fila(v), view=FilaView(v))

    # ranking
    canal = bot.get_channel(CANAL_RANK)
    if canal:
        await canal.purge(limit=10)
        await canal.send(embed=RankView().embed(), view=RankView())

    # pix
    canal = bot.get_channel(CANAL_PIX)
    if canal:
        await canal.purge(limit=10)
        await canal.send("💸 Configure seu PIX", view=PixView())

    # mediadores
    canal = bot.get_channel(CANAL_MED)
    if canal:
        await canal.purge(limit=10)
        await canal.send(embed=embed_mediadores(), view=MedView())

bot.run("MTQ5OTEzNjAzNDkwOTMyMzM3NA.GjJ89S.41l8BTSqdPxKSdwuySnZiF3fZpPvu6yjswiwRI")