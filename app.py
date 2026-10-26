import os
import asyncio
import threading
import gradio as gr

# Disable internal aiohttp web server since Gradio handles port 7860
os.environ["ENABLE_INTERNAL_WEB"] = "false"

import bot

def run_discord_bot():
    """Runs the Discord bot in background thread."""
    asyncio.run(bot.main())

# Start Discord bot in a background daemon thread
bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
bot_thread.start()

# Clean Gradio UI for Hugging Face Spaces
with gr.Blocks(title="EXILES AI Bot Console", theme=gr.themes.Monochrome()) as demo:
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
    demo.launch(server_name="0.0.0.0", server_port=port, ssr_mode=False)
