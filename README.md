# 🤖 Instagram Bot

> Autonomous Instagram content scouting and posting bot.  
> Find viral reels, edit captions, and post — all from your terminal.

---

## ⚡ Quick Start

```bash
# 1. One-click setup
setup.bat

# 2. Run the bot
run.bat
# — or —
venv\Scripts\python bot.py
```

---

## 🔑 Login Methods

| Method | How |
|--------|-----|
| **Username + Password** | Standard login, supports 2FA |
| **Session File** | Load a saved `session.json` |
| **Session Cookie** | Paste `sessionid` from browser DevTools |

Sessions are saved in `sessions/<username>.json` and auto-resumed on next launch.

---

## 🚀 Bot Flow

```
1. Login (or resume saved session)
2. Enter hashtags: urdupoetry, shayari, mushaira
3. Choose content type: Reels / Stories / Photos / Photos+Music
4. Choose count: 5 / 10 / 20
5. Bot scouts and ranks content by engagement score
6. Review numbered list with views, likes, duration, caption preview
7. Select: "1,3,5" or "1-4" or "all"
8. Bot downloads, edits captions, and posts automatically
9. Summary table with all posted links
10. Repeat or exit
```

---

## 🧠 Smart Caption System

The bot automatically:

- **Replaces** `Follow @handle` with your own `@username`
- **Removes** spam lines (`@same @same @same @same`)
- **Keeps** poetry text, hashtags, credit lines, and video courtesy notes
- **Appends** `Follow @youraccount for more 🖤` if not present

---

## 📁 Project Structure

```
Instagram Bot/
├── bot.py              ← Main entry point
├── modules/
│   ├── auth.py         ← Login & session management
│   ├── scout.py        ← Hashtag search & content ranking
│   ├── caption.py      ← Smart caption editing
│   ├── downloader.py   ← Video/image downloader
│   └── uploader.py     ← Reel / Story / Photo uploader
├── sessions/           ← Saved login sessions
├── downloads/          ← Temp files (auto-cleaned)
├── requirements.txt
├── setup.bat           ← One-click install
└── run.bat             ← One-click launch
```

---

## 🔮 Planned Features (AI Integration)

- AI-generated captions based on video content
- AI-based virality score prediction
- Auto-schedule posting based on optimal times
- Hashtag AI suggestions based on content analysis
- Multi-account management

---

## ⚠️ Disclaimer

This bot uses Instagram's unofficial private API via `instagrapi`.  
Use responsibly. Excessive posting may trigger account limits.

---

*Built on top of [instagram-mcp-server](https://github.com/official-Arvind/instagram-mcp)*
