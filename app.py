import os
import asyncio
import threading
import gradio as gr
import bot

def run_discord_bot():
    """Runs the Discord bot event loop in a background thread."""
    asyncio.run(bot.main())

# Start Discord bot in a dedicated thread
bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
bot_thread.start()

# Minimal clean Gradio dashboard to satisfy Hugging Face Space runtime
with gr.Blocks(title="EXILES AI Bot Console", theme=gr.themes.Monochrome()) as demo:
    gr.Markdown(
        """
        # ⚡ EXILES AI — Discord Operations Bot
        ### Status: 🟢 Online (24/7 Cloud Running)
        * **Guild:** EXILES (Free Fire Clan)
        * **Founder:** Trigo
        * **Model:** Google Gemini 3.5 Flash with Discord Tools
        
        The bot is active and listening to Discord channels.
        """
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
