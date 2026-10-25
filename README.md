# 🛡️ EXILES AI — 24/7 Discord Operations Agent

An intelligent, cloud-native Discord AI agent built for **EXILES** (Competitive Free Fire Clan & Gaming Guild). Powered by **Google Gemini 3.5 Flash** and **Discord.py**, designed to run 24/7 on free cloud platforms (Hugging Face Spaces, Koyeb, Docker) even when your PC is offline.

---

## ⚡ Highlights & Capabilities

- 🤖 **Natural Language Operations**: Direct 1-on-1 AI console in `#founder-ai`. Understands fluent Hinglish and English commands naturally.
- 🚫 **Zero Grey Boxes ("Dabbe-Free")**: Strictly formatted with clean Discord markdown, subheadings (`###`), bullet points, and Crimson Red (`#DC143C`) embeds. No ugly codeblock boxes.
- ⚔️ **Guild Scrim & Desk Automation**:
  - `/announce`: Dispatches official crimson announcements to `#announcements` with `@everyone` ping.
  - `/scrimdesk`: Instantly updates room credentials, slot timings, and passwords in `#scrim-desk`.
  - `/status`: Checks bot latency, AI status, and cloud uptime.
- 🌐 **Built-in 24/7 Keep-Alive Web Server**: Exposes an HTTP healthcheck on port `7860` for seamless Hugging Face Spaces / cloud container uptime.
- 🧠 **Context Memory**: Retains multi-turn conversation context so you can have ongoing discussions and planning sessions.

---

## 🚀 1-Click 24/7 Free Hosting on Hugging Face Spaces

You can host this bot **100% free with 16GB RAM / 2 vCPU** on Hugging Face Spaces without entering any credit card.

### Step 1: Create a New Space
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Set **Space name**: `exiles-discord-ai`
3. Set **License**: `mit`
4. Set **Space SDK**: Select **Docker** (Blank).
5. Set **Space hardware**: `Free CPU (2 vCPU, 16 GB)`
6. Click **Create Space**.

### Step 2: Add Secrets (Environment Variables)
In your newly created Space:
1. Go to **Settings** ➔ **Variables and secrets**.
2. Click **New secret** and add:
   - `DISCORD_TOKEN`: Your Discord Bot Token (from Discord Developer Portal).
   - `GEMINI_API_KEY`: Your Gemini API Key (from [aistudio.google.com](https://aistudio.google.com)).
   - `GUILD_ID`: `1562425772231360586`
   - `FOUNDER_AI_CHANNEL_ID`: `1564050092070142197`
   - `PORT`: `7860`

### Step 3: Push / Upload Code
Push this repository or upload the files (`bot.py`, `system_prompt.py`, `requirements.txt`, `Dockerfile`) to your Hugging Face Space repository:
```bash
git remote add space https://huggingface.co/spaces/<your-username>/exiles-discord-ai
git push space master
```
Once built, the bot will show **Running** and stay online 24/7!

---

## 💻 Local Development Setup

If you want to run the bot locally on your machine:

1. **Clone the repository:**
```bash
git clone https://github.com/himanshu-xyz-1/exiles-discord-ai-bot.git
cd exiles-discord-ai-bot
```

2. **Create a virtual environment & install dependencies:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure `.env` file:**
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your credentials inside `.env`:
```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
GUILD_ID=1562425772231360586
FOUNDER_AI_CHANNEL_ID=1564050092070142197
PORT=7860
```

4. **Run the bot:**
```bash
python bot.py
```

---

## 📁 Repository Structure

```
├── bot.py             # Main Discord bot & keep-alive web server
├── system_prompt.py   # System persona & strict formatting instructions
├── Dockerfile         # Production Docker container for Hugging Face Spaces
├── requirements.txt   # Python dependencies
├── .env.example       # Example environment variables (safe template)
├── .gitignore         # Ignores .env and local caches
└── README.md          # Documentation and cloud setup guide
```

---

## 🔒 Security & Privacy

- `.env` is permanently excluded via `.gitignore` to prevent secret leaks.
- Channel `#founder-ai` is restricted strictly to the Founder and the bot.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
