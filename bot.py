import os
import sys
import json
import asyncio
import logging
from datetime import datetime
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from system_prompt import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ExilesBot")

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID", "1562425772231360586"))
FOUNDER_AI_CHANNEL_ID = int(os.getenv("FOUNDER_AI_CHANNEL_ID", "1564050092070142197"))
PORT = int(os.getenv("PORT", "7860"))

# Important Channel IDs
ANNOUNCEMENTS_CHANNEL_ID = 1562488082295562291
SCRIM_DESK_CHANNEL_ID = 1562490539121709127

# Initialize Discord Bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Conversation history cache (channel_id -> list of turns)
conversation_history = {}
MAX_HISTORY = 12

PRIMARY_MODEL = "gemini-3.5-flash"
FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"]


async def query_gemini(messages_history: list) -> str:
    """Calls Google Gemini API with system instructions and chat history."""
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API Key configure nahi hai! Please set GEMINI_API_KEY in .env or Secrets."

    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": messages_history,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }

    async with aiohttp.ClientSession() as session:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text_parts = [p.get("text", "") for p in parts if "text" in p]
                            reply = "".join(text_parts).strip()
                            if reply:
                                return reply
                    else:
                        err_text = await resp.text()
                        logger.warning(f"Model {model} returned status {resp.status}: {err_text[:200]}")
            except Exception as e:
                logger.error(f"Error querying Gemini model {model}: {e}")

    return "⚠️ Bhai, Gemini API se connect karne me dikkat aa rahi hai. Kuch second baad dobara try karo."


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="over EXILES Clan 🛡️"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    # Ignore bot's own messages
    if message.author.bot:
        return

    # Check if message is in founder-ai channel OR mentions the bot OR is DM
    is_founder_channel = message.channel.id == FOUNDER_AI_CHANNEL_ID
    is_mentioned = bot.user.mentioned_in(message) and not message.mention_everyone
    is_dm = isinstance(message.channel, discord.DMChannel)

    if not (is_founder_channel or is_mentioned or is_dm):
        await bot.process_commands(message)
        return

    # Clean user content
    user_text = message.clean_content.replace(f"@{bot.user.name}", "").strip()
    if not user_text:
        return

    # Maintain channel history
    cid = message.channel.id
    if cid not in conversation_history:
        conversation_history[cid] = []

    # Append user turn
    conversation_history[cid].append({
        "role": "user",
        "parts": [{"text": user_text}]
    })

    # Trim history
    if len(conversation_history[cid]) > MAX_HISTORY:
        conversation_history[cid] = conversation_history[cid][-MAX_HISTORY:]

    # Trigger Discord typing indicator
    async with message.channel.typing():
        response_text = await query_gemini(conversation_history[cid])

    # Append model reply to history
    conversation_history[cid].append({
        "role": "model",
        "parts": [{"text": response_text}]
    })

    # Send response (handle Discord 2000-char limit)
    if len(response_text) <= 2000:
        await message.reply(response_text, mention_author=False)
    else:
        # Split message into chunks
        chunks = []
        current = ""
        for line in response_text.split("\n"):
            if len(current) + len(line) + 1 <= 1900:
                current += line + "\n"
            else:
                chunks.append(current)
                current = line + "\n"
        if current:
            chunks.append(current)

        for chunk in chunks:
            await message.channel.send(chunk)

    await bot.process_commands(message)


# Slash Command: Status
@bot.tree.command(name="status", description="Check EXILES Bot latency and system status")
async def cmd_status(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="⚡ EXILES Bot // System Status",
        color=0xDC143C,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Ping / Latency", value=f"`{latency}ms`", inline=True)
    embed.add_field(name="AI Model", value="`Gemini 3.5 Flash`", inline=True)
    embed.add_field(name="Cloud Hosting", value="`Online 24/7`", inline=True)
    embed.set_footer(text="EXILES Competitive Clan")
    await interaction.response.send_message(embed=embed)


# Slash Command: Quick Announcement
@bot.tree.command(name="announce", description="Post an official clan announcement with @everyone ping")
async def cmd_announce(interaction: discord.Interaction, title: str, message: str):
    # Only Founder / Admins can announce
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only Trigo or Clan Admins can post announcements.", ephemeral=True)
        return

    channel = bot.get_channel(ANNOUNCEMENTS_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Announcements channel not found.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"📢 {title.upper()}",
        description=f"{message}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n*Posted by {interaction.user.mention}*",
        color=0xDC143C,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="EXILES Clan • Official Announcement")

    await channel.send(content="@everyone", embed=embed)
    await interaction.response.send_message(f"✅ Announcement posted in {channel.mention}!", ephemeral=True)


# Slash Command: Scrim Desk
@bot.tree.command(name="scrimdesk", description="Post room credentials in #scrim-desk")
async def cmd_scrimdesk(interaction: discord.Interaction, match_time: str, room_id: str, password: str, notes: str = "Be on time."):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    channel = bot.get_channel(SCRIM_DESK_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Scrim desk channel not found.", ephemeral=True)
        return

    embed = discord.Embed(
        title="⚔️ EXILES // SCRIM CREDENTIALS",
        description=f"Match credentials updated by {interaction.user.mention}.\n━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=0xDC143C,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="⏰ Time", value=f"**{match_time}**", inline=True)
    embed.add_field(name="🔑 Room ID", value=f"**{room_id}**", inline=True)
    embed.add_field(name="🔒 Password", value=f"**{password}**", inline=True)
    embed.add_field(name="📋 Instructions", value=notes, inline=False)
    embed.set_footer(text="EXILES Scrim Desk • All Lineups Ready")

    await channel.send(content="<@&1562961690549551204>", embed=embed)  # Ping @Scrims Ping
    await interaction.response.send_message(f"✅ Credentials posted in {channel.mention}!", ephemeral=True)


# Web Keep-Alive Server for Hugging Face Spaces / 24/7 Hosting
async def start_web_server():
    from aiohttp import web

    async def handle_ping(request):
        return web.json_response({
            "status": "online",
            "bot": "EXILES AI",
            "guild_id": GUILD_ID,
            "latency_ms": round(bot.latency * 1000) if bot.is_ready() else 0,
            "timestamp": datetime.utcnow().isoformat()
        })

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Keep-alive web server listening on 0.0.0.0:{PORT}")


async def main():
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is missing! Please provide it in .env or environment.")
        sys.exit(1)

    # Start both web server and discord bot concurrently
    await asyncio.gather(
        start_web_server(),
        bot.start(DISCORD_TOKEN)
    )


if __name__ == "__main__":
    asyncio.run(main())
