# 🐱 XiaogePet — Desktop AI Companion Agent

**A desktop AI pet that actually *lives* with you — proactive, memory-aware, and powered by a full Agent stack.**

> Built with Python + PyQt5 + LLM (Function Calling) + RAG + TTS. Not just a widget — a real Agent system with long-term memory, tool use, and proactive behavior.

---

## ✨ Features

### 🧠 Full Agent Architecture
- **RAG Long-Term Memory** — Vector knowledge base (ChromaDB) stores character background lore; auto-retrieves relevant context during conversation
- **Function Calling** — Agent autonomously calls tools: get time, set reminders, check idle time, take screenshots, open apps
- **User Memory** — Automatically extracts and persists user info (name, preferences, events, emotions) from conversations; references them naturally
- **Character Builder** — Input any character name + source → LLM generates 8-dimension structured profile → auto-renders System Prompt
- **Proactive Behavior** — Not just reactive. Agent initiates conversations: time reports, health reminders (water/idle/rest/eyes), mood check-ins, follow-up questions based on memory

### 🎭 Character System
- **13 animated actions** with character-specific voice lines
- **Window climbing** — Drag pet to any window edge → sits on top / hangs on side. Window closes → pet falls
- **Irregular mask** — Window shape follows character silhouette (transparent background, always-on-top)
- **Custom persona** — Right-click → Character Settings to edit System Prompt, API config, or generate new characters from scratch

### 💬 Immersive Chat
- Double-click pet → chat input appears
- LLM responds in-character with cold, reticent personality (default: Zhang Qiling from *The Lost Tomb*)
- Context memory (last 10 turns) + RAG background knowledge + user memory injection
- Pink rounded speech bubbles, auto-positioned to not cover pet's face

### 🔊 TTS Voice
- Priority: Alibaba Cloud CosyVoice (deep male voice, character-matched)
- Fallback: edge-tts (YunjianNeural, low-pitched)
- Async generation, non-blocking playback

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    pet_agent.py (Main)                    │
│          PyQt5 Window · 13 Actions · Window Climbing      │
├──────────────┬───────────────┬───────────┬───────────────┤
│  Bubble.py   │  ChatWindow   │  tts.py   │ proactive.py  │
│  (Speech)    │  (Input UI)   │  (Voice)  │ (Auto-talk)   │
├──────────────┴───────────────┴───────────┴───────────────┤
│                   agent_core.py (Brain)                    │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │   RAG   │  │   Tool   │  │  Character │  │   User   │ │
│  │   KB    │  │  Registry│  │  Builder   │  │  Memory  │ │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘ │
│       │            │              │              │       │
│  ┌────▼────┐  ┌────▼─────┐  ┌─────▼─────┐  ┌────▼─────┐ │
│  │knowledge│  │  tools/  │  │    llm/   │  │  memory/  │ │
│  │ _base.py│  │  time_   │  │ character_│  │user_memory│ │
│  │         │  │  tools.py│  │  builder  │  │  _extract │ │
│  └─────────┘  │  system_ │  │           │  └──────────┘ │
│               │  tools.py │  └───────────┘               │
│               └──────────┘                               │
├──────────────────────────────────────────────────────────┤
│              llm_client.py (LLM API Client)               │
│         Function Calling + Context Memory + RAG           │
└──────────────────────────────────────────────────────────┘
```

### Agent Core Pipeline

```
User Message
    │
    ▼
┌─ RAG Retrieval ──── Vector search (Top-K) in character knowledge base
│                      → Inject relevant lore as context
│
├─ System Context ──── Tool usage hints + User memory + RAG context
│                      + Character System Prompt
│
├─ Function Calling ── LLM decides: direct reply OR call a tool
│                      Tools: time, reminder, idle check, screenshot, app launch
│
├─ Memory Extract ──── Async: LLM extracts user info from conversation
│                      → Persists to user_memory.json
│
└─ Proactive ───────── Timer-based: health reminders, follow-up questions,
                       mood check-ins (skipped at night 23:00-08:00)
```

---

## 📦 Project Structure

```
pet/
├── pet_agent.py              # Main app: window, interactions, state machine
├── agent_core.py             # Agent brain: RAG + Tools + Memory + Character
├── llm_client.py             # LLM API client (Function Calling + context)
├── proactive.py              # Proactive behavior engine
├── bubble.py                 # Speech bubble UI
├── chat_window.py            # Chat input UI
├── chat_box.py               # Legacy chat component
├── character.py              # Default character config
├── character_settings.py     # Character settings UI (persona + API config)
├── config.py                 # Global config (size, speed, timers)
├── window_manager.py         # Win32 window enumeration + climb detection
├── tts.py                    # TTS engine (CosyVoice → edge-tts fallback)
├── llm/
│   └── character_builder.py  # LLM 8-dimension character profile generator
├── memory/
│   ├── knowledge_base.py     # RAG: document loading, chunking, retrieval
│   ├── vector_store.py       # ChromaDB vector store wrapper
│   ├── embedding_client.py   # Embedding API client
│   ├── user_memory.py        # User long-term memory (JSON persistence)
│   └── memory_extractor.py   # Auto-extract user info from conversations
├── tools/
│   ├── base.py               # BaseTool abstract class
│   ├── registry.py           # Tool registry + OpenAI schema export
│   ├── time_tools.py         # get_current_time, set_reminder
│   ├── system_tools.py       # check_idle_time, take_screenshot, open_application
│   └── lunar.py              # Lunar calendar utilities
├── data/
│   ├── knowledge/            # Character knowledge .txt files (RAG source)
│   └── vector_db/            # ChromaDB persistent storage
├── assets/                   # 17 transparent PNG action sprites
└── api_config.json           # (Optional) API configuration
```

---

## 🚀 Quick Start

### Option 1: Run from source (recommended for development)

```bash
# Clone
git clone https://github.com/yourusername/xiaoge-pet.git
cd xiaoge-pet

# Install dependencies
pip install PyQt5 pywin32 Pillow requests certifi chromadb edge-tts

# Configure your LLM API
# Edit config.py or create api_config.json:
# {
#   "api_key": "sk-your-key",
#   "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
#   "model": "glm-5"
# }

# Run
python pet_agent.py
```

### Option 2: Standalone EXE

Download the latest release, double-click `XiaogePet.exe`. Pet appears in bottom-right corner.

### Controls

| Action | Effect |
|--------|--------|
| **Click** pet | Cycle through 13 actions |
| **Double-click** pet | Open chat input |
| **Drag** pet | Move; drag to window edge → climb/sit |
| **Scroll** | Resize pet |
| **Right-click** pet | Menu: select action / walk here / settings / quit |

---

## 🔧 Adding Your Own Character

1. Right-click pet → **Character Settings**
2. Enter character name + source (e.g., "Sherlock Holmes, BBC Sherlock")
3. Click **Generate** — LLM creates 8-dimension profile automatically
4. Edit System Prompt if needed, then **Save**
5. Add character knowledge as `.txt` files in `data/knowledge/` for RAG
6. Restart — pet now speaks as your character with lore-accurate knowledge

### Adding Custom Tools

```python
from tools.base import BaseTool

class MyCustomTool(BaseTool):
    @property
    def name(self):
        return "my_custom_tool"
    
    @property
    def description(self):
        return "Use this when the user asks about X"
    
    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look up"}
            },
            "required": ["query"]
        }
    
    def execute(self, **kwargs):
        result = do_something(kwargs["query"])
        return result
```

Register in `tools/registry.py`:
```python
self.register(MyCustomTool())
```

The Agent will automatically include it in Function Calling schemas and call it when appropriate.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI Framework | PyQt5 |
| Window Management | pywin32 (Win32 API) |
| LLM Backend | OpenAI-compatible API (tested with Alibaba Cloud GLM-5) |
| Function Calling | OpenAI Function Calling schema |
| RAG / Vector DB | ChromaDB + custom embedding client |
| TTS | Alibaba Cloud CosyVoice → edge-tts fallback |
| Image Processing | Pillow |
| Packaging | PyInstaller |

---

## 📋 Agent Capabilities Summary

| Capability | Status | Description |
|-----------|--------|-------------|
| RAG Knowledge Base | ✅ | Character lore retrieval with Top-K + score threshold |
| Function Calling | ✅ | 5 built-in tools, extensible via BaseTool |
| User Long-Term Memory | ✅ | Auto-extract + persist user info from conversations |
| Character Generation | ✅ | LLM 8-dimension structured profile → System Prompt |
| Proactive Behavior | ✅ | Time/health/mood/follow-up triggers with night-silence |
| TTS Voice | ✅ | CosyVoice (primary) → edge-tts (fallback) |
| Window Climbing | ✅ | Win32-based edge detection, sit/climb/fall animations |
| Context Memory | ✅ | Last 10 turns conversation history |
| Memory Extraction | ✅ | Async LLM-based user info extraction every 3 turns |

---

## 📝 License

MIT License — see [LICENSE](LICENSE)

Character images and persona are based on *The Lost Tomb* (盗墓笔记) and are used for educational/demo purposes only. Character rights belong to their respective owners.

---

## 🙏 Acknowledgments

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — GUI framework
- [ChromaDB](https://www.trychroma.com/) — Vector database
- [edge-tts](https://github.com/rany2/edge-tts) — Microsoft Edge TTS
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) — Alibaba TTS
- The Lost Tomb (盗墓笔记) — Character inspiration

---

⭐ If you like this project, please star it!
