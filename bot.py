import os
import json
import asyncio
from aiohttp import web
import discord
from discord.ui import View, Button
from supabase import create_client, Client

# Загружаем конфиг из файла (на хостинге Render мы заменим это на переменные окружения)
if os.path.exists("config.json"):
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        SUPABASE_URL = config["supabase_url"]
        SUPABASE_KEY = config["supabase_key"]
        DISCORD_TOKEN = config["discord_token"]
        ADMIN_CHANNEL_ID = config["admin_channel_id"]
else:
    # Если запуск идет на облачном сервере через Environment Variables
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
    ADMIN_CHANNEL_ID = int(os.environ.get("ADMIN_CHANNEL_ID", 0))

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

class ContractReviewView(View):
    def __init__(self, report_id: str):
        super().__init__(timeout=None)
        self.report_id = report_id

    @discord.ui.button(label="Одобрить", style=discord.ButtonStyle.green, custom_id="approve_contract")
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        supabase.table("contract_reports").update({"status": "Approved"}).eq("id", self.report_id).execute()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"✅ **Одобрено** администратором {interaction.user.mention}", view=self)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="reject_contract")
    async def reject_button(self, interaction: discord.Interaction, button: Button):
        supabase.table("contract_reports").update({"status": "Rejected"}).eq("id", self.report_id).execute()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"❌ **Отклонено** администратором {interaction.user.mention}", view=self)

@client.event
async def on_ready():
    print(f"Бот {client.user} успешно запущен и работает 24/7!")

# Функция веб-сервера для предотвращения засыпания бота на бесплатном хостинге
async def handle_ping(request):
    return web.Response(text="Bot is active and running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Keep-Alive сервер запущен на порту {port}")

async def main():
    # Запускаем и веб-сервер, и Discord бота одновременно
    await start_web_server()
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())