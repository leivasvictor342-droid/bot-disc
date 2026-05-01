# ================= IMPORTS =================
import discord
from discord.ext import commands
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= KEEP ALIVE =================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot online')

def run_web():
    server = HTTPServer(('0.0.0.0', 3000), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()

# ================= BOT CONFIG =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# ================= CONFIG =================
BOT_AVATAR = "https://media.discordapp.net/attachments/1499137895900909740/1499171139958738995/ChatGPT_Image_29_de_abr._de_2026_16_59_39.png"
BANNER = "https://media.discordapp.net/attachments/1499137895900909740/1499171141233807360/29_de_abr._de_2026_13_19_52.png"

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

# ================= MATCHMAKING =================
fila_paineis = {}
mediador_index = 0

def get_next_mediador():
    global mediador_index

    if not fila_mediadores:
        return None

    mediador_id = fila_mediadores[mediador_index]
    mediador_index = (mediador_index + 1) % len(fila_mediadores)
    return mediador_id

class ConfirmView(discord.ui.View):
    def __init__(self, players, canal):
        super().__init__(timeout=None)
        self.players = players
        self.canal = canal
        self.confirmados = []

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.green)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user not in self.players:
            return await interaction.response.send_message("Não é sua partida.", ephemeral=True)

        if interaction.user in self.confirmados:
            return await interaction.response.send_message("Você já confirmou.", ephemeral=True)

        self.confirmados.append(interaction.user)
        await interaction.response.send_message("Confirmado!", ephemeral=True)

        if len(self.confirmados) == len(self.players):

            guild = interaction.guild
            categoria_partidas = discord.utils.get(guild.categories, name="partidas")

            mediador_id = get_next_mediador()
            mediador = guild.get_member(mediador_id) if mediador_id else None

            if mediador:
                await self.canal.set_permissions(mediador, read_messages=True, send_messages=True)

            await self.canal.edit(
                name=f"partida-{self.players[0].name}-vs-{self.players[1].name}",
                category=categoria_partidas
            )

            msg = "✅ Partida confirmada!\n💰 Realizem o pagamento."

            if mediador:
                msg += f"\n👨‍💼 Mediador: {mediador.mention}"
            else:
                msg += "\n⚠️ Nenhum mediador disponível!"

            await self.canal.send(msg)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.canal.delete()


async def iniciar_partida_por_valor(ctx, valor):
    fila = filas[valor]

    if len(fila) >= 2:

        if not fila_mediadores:
            await ctx.channel.send("❌ Não há mediador disponível no momento.")
            return

        p1_id = fila.pop(0)
        p2_id = fila.pop(0)

        guild = ctx.guild
        p1 = guild.get_member(p1_id)
        p2 = guild.get_member(p2_id)

        categoria = discord.utils.get(guild.categories, name="aguardando")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            p1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            p2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        canal = await guild.create_text_channel(
            name=f"aguardando-{p1.name}-vs-{p2.name}",
            category=categoria,
            overwrites=overwrites
        )

        view = ConfirmView([p1, p2], canal)

        await canal.send(
            f"{p1.mention} vs {p2.mention}\nClique em **Confirmar**:",
            view=view
        )

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

    embed.set_thumbnail(url=BOT_AVATAR)
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

    @discord.ui.button(label="🎮 Entrar", style=discord.ButtonStyle.success, custom_id="fila_entrar")
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

        await iniciar_partida_por_valor(interaction, self.valor)

    @discord.ui.button(label="🚪 Sair", style=discord.ButtonStyle.danger, custom_id="fila_sair")
    async def sair_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id not in filas[self.valor]:
            return await interaction.response.send_message("Você não está na fila", ephemeral=True)

        filas[self.valor].remove(interaction.user.id)

        await interaction.response.edit_message(
            embed=embed_fila(self.valor),
            view=self
        )
# ================= MEDIADOR =================
class MedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar", style=discord.ButtonStyle.success, custom_id="med_entrar")
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in fila_mediadores:
            fila_mediadores.append(interaction.user.id)
            salvar()

        await interaction.response.edit_message(
            embed=embed_mediadores(),
            view=self
        )

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, custom_id="med_sair")
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in fila_mediadores:
            fila_mediadores.remove(interaction.user.id)
            salvar()

        await interaction.response.edit_message(
            embed=embed_mediadores(),
            view=self
        )

class ResultadoView(discord.ui.View):
    def __init__(self, p1, p2):
        super().__init__(timeout=None)
        self.p1 = p1
        self.p2 = p2

        # nomes nos botões
        self.add_item(discord.ui.Button(
            label=f"🏆 {p1.name}",
            style=discord.ButtonStyle.success,
            custom_id="win_p1"
        ))

        self.add_item(discord.ui.Button(
            label=f"🏆 {p2.name}",
            style=discord.ButtonStyle.success,
            custom_id="win_p2"
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in fila_mediadores:
            await interaction.response.send_message("❌ Apenas mediador pode finalizar.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="hidden1", style=discord.ButtonStyle.secondary)
    async def dummy1(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    async def on_item_interaction(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")

        if custom_id == "win_p1":
            vencedor = self.p1
        elif custom_id == "win_p2":
            vencedor = self.p2
        else:
            return

        ranking[str(vencedor.id)] = ranking.get(str(vencedor.id), 0) + 1
        salvar()

        await interaction.message.edit(view=None)
        await interaction.response.send_message(f"🏆 {vencedor.mention} venceu!")
        
# ================= READY =================
@bot.event
async def on_ready():
    carregar()

    bot.add_view(MedView())

    for v in VALORES:
        bot.add_view(FilaView(v))

    print(f"✅ ONLINE COMO {bot.user}")

import os
bot.run(os.getenv("TOKEN"))