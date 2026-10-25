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
from tools import DISCORD_TOOLS_SCHEMA, execute_tool

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
ENABLE_MESSAGE_CONTENT = os.getenv("ENABLE_MESSAGE_CONTENT", "true").lower() == "true"

# Channel IDs
ANNOUNCEMENTS_CHANNEL_ID = 1562488082295562291
SCRIM_DESK_CHANNEL_ID = 1562490539121709127

# Conversation history cache (channel_id -> list of turns)
conversation_history = {}
MAX_HISTORY = 12

PRIMARY_MODEL = "gemini-3.5-flash"


async def query_gemini_with_tools(bot_client: discord.Client, guild: discord.Guild, messages_history: list) -> str:
    """Calls Gemini with Discord Function Calling tools enabled."""
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API Key is missing! Please configure GEMINI_API_KEY."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{PRIMARY_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": messages_history,
        "tools": DISCORD_TOOLS_SCHEMA,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    logger.error(f"Gemini API Error {resp.status}: {err_text[:200]}")
                    return "⚠️ Gemini API connect karne me error aaya. Kuch der baad retry karein."

                data = await resp.json()
                candidate = data.get("candidates", [{}])[0]
                model_part = candidate.get("content", {}).get("parts", [{}])[0]

                # Check if Gemini invoked a function call
                if "functionCall" in model_part:
                    func_call = model_part["functionCall"]
                    func_name = func_call.get("name")
                    func_args = func_call.get("args", {})
                    call_id = func_call.get("id", "call_1")

                    logger.info(f"Gemini decided to call tool: {func_name} with args {func_args}")

                    # Execute the Discord tool
                    tool_result = await execute_tool(bot_client, guild, func_name, func_args)

                    # Feed the result back to Gemini
                    followup_contents = list(messages_history)
                    followup_contents.append({
                        "role": "model",
                        "parts": [model_part]
                    })
                    followup_contents.append({
                        "role": "user",
                        "parts": [{
                            "functionResponse": {
                                "name": func_name,
                                "response": tool_result,
                                "id": call_id
                            }
                        }]
                    })

                    followup_payload = {
                        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                        "contents": followup_contents,
                        "tools": DISCORD_TOOLS_SCHEMA,
                        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
                    }

                    async with session.post(url, json=followup_payload, timeout=aiohttp.ClientTimeout(total=25)) as resp2:
                        if resp2.status == 200:
                            data2 = await resp2.json()
                            candidate2 = data2.get("candidates", [{}])[0]
                            parts2 = candidate2.get("content", {}).get("parts", [])
                            reply2 = "".join([p.get("text", "") for p in parts2 if "text" in p]).strip()
                            if reply2:
                                return reply2

                    return f"✅ Action '{func_name}' execute ho gaya: {tool_result.get('result', tool_result.get('message', 'Done'))}"

                # Normal text response
                parts = candidate.get("content", {}).get("parts", [])
                reply = "".join([p.get("text", "") for p in parts if "text" in p]).strip()
                return reply if reply else "Main samajh nahi paya, dobara bolna?"

        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return "⚠️ Gemini service temporary down hai ya timeout ho gaya. Ek baar dobara try karo."


intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
if ENABLE_MESSAGE_CONTENT:
    intents.message_content = True
    logger.info("Message Content Intent: ENABLED")
else:
    intents.message_content = False
    logger.info("Message Content Intent: DISABLED")

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    logger.info(f"✅ Logged in successfully as {bot.user} (ID: {bot.user.id})")
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
    if message.author.bot:
        return

    is_founder_channel = message.channel.id == FOUNDER_AI_CHANNEL_ID
    is_mentioned = bot.user.mentioned_in(message) and not message.mention_everyone
    is_dm = isinstance(message.channel, discord.DMChannel)

    if not (is_founder_channel or is_mentioned or is_dm):
        await bot.process_commands(message)
        return

    user_text = message.clean_content.replace(f"@{bot.user.name}", "").strip()
    if not user_text:
        return

    cid = message.channel.id
    if cid not in conversation_history:
        conversation_history[cid] = []

    conversation_history[cid].append({
        "role": "user",
        "parts": [{"text": user_text}]
    })

    if len(conversation_history[cid]) > MAX_HISTORY:
        conversation_history[cid] = conversation_history[cid][-MAX_HISTORY:]

    guild = message.guild or bot.get_guild(GUILD_ID)

    async with message.channel.typing():
        response_text = await query_gemini_with_tools(bot, guild, conversation_history[cid])

    conversation_history[cid].append({
        "role": "model",
        "parts": [{"text": response_text}]
    })

    if len(response_text) <= 2000:
        await message.reply(response_text, mention_author=False)
    else:
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


# Slash Commands
@bot.tree.command(name="status", description="Check EXILES Bot latency and system status")
async def cmd_status(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="⚡ EXILES Bot // System Status",
        color=0xDC143C,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Ping / Latency", value=f"`{latency}ms`", inline=True)
    embed.add_field(name="AI Model", value="`Gemini 3.5 Flash (Function Calling Enabled)`", inline=True)
    embed.add_field(name="Cloud Hosting", value="`Online 24/7`", inline=True)
    embed.set_footer(text="EXILES Competitive Clan")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="announce", description="Post an official clan announcement with @everyone ping")
async def cmd_announce(interaction: discord.Interaction, title: str, message: str):
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

    await channel.send(content="<@&1562961690549551204>", embed=embed)
    await interaction.response.send_message(f"✅ Credentials posted in {channel.mention}!", ephemeral=True)


# Keep-Alive Web Server for 24/7 Hosting
async def start_web_server():
    from aiohttp import web

    async def handle_ping(request):
        return web.json_response({
            "status": "online",
            "bot": "EXILES AI",
            "guild_id": GUILD_ID,
            "tools_enabled": True,
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
        logger.error("DISCORD_TOKEN is missing!")
        sys.exit(1)

    await start_web_server()

    # Smart start with fallback if Message Content Intent is not enabled in portal
    try:
        await bot.start(DISCORD_TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning("Privileged intent missing. Falling back to compatibility mode...")
        bot.intents.message_content = False
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
