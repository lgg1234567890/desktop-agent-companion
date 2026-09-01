# AGENTS.md — AI Collaboration Guide

This file provides guidance for AI agents (Claude, Cursor, Copilot, etc.) working on this codebase.

## Project Overview

XiaogePet is a desktop AI companion agent with full Agent architecture:
- **RAG** long-term memory (ChromaDB vector store)
- **Function Calling** tool use (time, reminders, system tools)
- **User memory** auto-extraction and persistence
- **Proactive behavior** engine (health reminders, mood check-ins, follow-ups)
- **TTS** voice synthesis (CosyVoice → edge-tts fallback)
- **PyQt5** desktop UI with window climbing, transparent background, 13 animated actions

## Architecture

```
pet_agent.py          # Main window, interactions, state machine
├── agent_core.py     # Agent brain: orchestrates RAG + Tools + Memory + Character
├── llm_client.py     # LLM API client with Function Calling support
├── proactive.py      # Proactive behavior engine (timer-based)
├── tts.py            # TTS engine with fallback chain
├── bubble.py         # Speech bubble UI
├── chat_window.py    # Chat input UI
├── character.py      # Default character config
├── character_settings.py  # Character settings UI
├── config.py         # Global configuration
├── window_manager.py # Win32 window enumeration + climb detection
├── llm/
│   └── character_builder.py  # 8-dimension character profile generator
├── memory/
│   ├── knowledge_base.py     # RAG: document loading, chunking, retrieval
│   ├── vector_store.py       # ChromaDB wrapper
│   ├── embedding_client.py   # Embedding API client
│   ├── user_memory.py        # User long-term memory (JSON)
│   └── memory_extractor.py   # Auto-extract user info from conversations
└── tools/
    ├── base.py               # BaseTool abstract class
    ├── registry.py           # Tool registry + OpenAI schema export
    ├── time_tools.py         # get_current_time, set_reminder
    ├── system_tools.py       # check_idle_time, take_screenshot, open_application
    └── lunar.py              # Lunar calendar utilities
```

## Key Conventions

### Adding a New Tool
1. Inherit from `BaseTool` in `tools/base.py`
2. Implement `name`, `description`, `parameters`, `execute()`
3. Register in `tools/registry.py` `ToolRegistry.__init__`
4. The Agent automatically includes it in Function Calling schemas

### Adding a New Character
1. Add knowledge `.txt` file to `data/knowledge/`
2. Use Character Settings UI to generate profile via LLM
3. Profile saved to `data/character_profiles/`

### Memory System
- **Character knowledge**: RAG vector store, retrieved per-conversation
- **User memory**: JSON file, auto-extracted every 3 conversation turns
- **Context memory**: Last 10 turns in conversation history

## Testing

Run module tests:
```bash
python test_agent_core.py
python test_agent_modules.py
```

## Build EXE

```bash
pyinstaller XiaogePet.spec --clean
```

Output in `dist/XiaogePet/`.

## Do Not Commit

- `api_config.json` (contains API keys)
- `data/vector_db/` (generated at runtime)
- `data/user_memory.json` (personal data)
- `build/`, `dist/` directories
- `*.log` files
