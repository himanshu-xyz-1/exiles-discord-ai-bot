import os
import time
import asyncio
import threading
import gradio as gr

# Disable internal aiohttp server since Gradio binds to port 7860
os.environ["ENABLE_INTERNAL_WEB"] = "false"

import bot

def run_discord_bot():
    """Runs the Discord bot event loop in a dedicated daemon thread."""
    asyncio.run(bot.main())

# Start Discord bot in a background daemon thread
bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
bot_thread.start()

# Clean Gradio UI for Hugging Face Spaces
with gr.Blocks(title="EXILES AI Bot Console") as demo:
    gr.Markdown(
        """
        # ⚡ EXILES AI — 24/7 Discord Operations Agent
        ### Status: 🟢 Online (Running 24/7 on Cloud)
        * **Guild:** EXILES (Free Fire Clan)
        * **Founder:** Trigo
        * **AI Model:** Google Gemini 3.5 Flash
        * **Actions:** Function Calling Enabled (Channels, Roles, Embeds, Moderation)
        
        *Your Discord bot is connected and running in the background.*
        """
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    # Launch Gradio and explicitly block main thread to prevent container exit
    demo.launch(server_name="0.0.0.0", server_port=port)
    while True:
        time.sleep(3600)
