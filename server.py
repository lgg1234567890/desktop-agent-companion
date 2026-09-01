# -*- coding: utf-8 -*-
"""
桌面AI陪伴Agent - 服务端API
将Agent核心能力包装成FastAPI服务，支持多端接入
桌面端可以选择直接调用本地API，而不是直接import

启动方式：
    uvicorn server:app --host 0.0.0.0 --port 8000

API文档：http://localhost:8000/docs
"""
import os
import sys
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent_core import get_agent_core

# 创建FastAPI应用
app = FastAPI(
    title="Desktop AI Companion Agent API",
    description="桌面AI陪伴Agent的服务端API，支持对话、记忆管理、角色管理等功能",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置（允许前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局Agent实例
_agent = None


def get_agent():
    """获取Agent单例"""
    global _agent
    if _agent is None:
        _agent = get_agent_core()
    return _agent


# ========== 请求/响应模型 ==========

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    user_id: str = Field("default", description="用户ID（用于多用户隔离）")
    use_rag: bool = Field(True, description="是否使用RAG检索")
    use_tools: bool = Field(True, description="是否启用工具调用")
    extract_memory: bool = Field(True, description="是否自动提取用户记忆")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Agent回复")
    success: bool = Field(..., description="是否成功")
    tools_used: List[Dict] = Field(default_factory=list, description="调用的工具列表")
    memory_context: str = Field("", description="RAG检索到的上下文")


class MemoryRequest(BaseModel):
    category: str = Field(..., description="记忆类别：event/ongoing/personality/info/preference")
    content: str = Field(..., description="记忆内容")


class CharacterRequest(BaseModel):
    name: str = Field(..., description="角色名称")
    source: str = Field("", description="角色出处（如：盗墓笔记）")


class CharacterResponse(BaseModel):
    name: str = Field(..., description="角色名称")
    system_prompt: str = Field("", description="生成的System Prompt")
    profile: Dict = Field(default_factory=dict, description="8维角色画像")


# ========== API路由 ==========

@app.get("/")
async def root():
    """服务状态检查"""
    return {
        "service": "Desktop AI Companion Agent API",
        "version": "2.0.0",
        "architecture": "Multi-Agent (Planner + Memory + Tool)",
        "status": "running"
    }


@app.get("/api/status")
async def get_status():
    """获取Agent系统状态"""
    agent = get_agent()
    return {
        "status": "running",
        "multi_agent": True,
        "agent_status": agent.get_multi_agent_status(),
        "stats": agent.get_agent_stats(),
        "user_memory": agent.get_user_memory_stats()
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    发送消息给Agent，获取回复
    支持RAG检索、Function Calling工具调用、用户记忆自动提取
    """
    agent = get_agent()
    try:
        reply, success, tools_used, memory_context = agent.chat(
            user_message=request.message,
            use_rag=request.use_rag,
            use_tools=request.use_tools,
            extract_memory=request.extract_memory
        )
        return ChatResponse(
            reply=reply,
            success=success,
            tools_used=tools_used,
            memory_context=memory_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@app.get("/api/memory")
async def get_memory():
    """获取用户记忆"""
    agent = get_agent()
    return {
        "context": agent.get_user_memory_context(),
        "stats": agent.get_user_memory_stats()
    }


@app.post("/api/memory")
async def save_memory(request: MemoryRequest):
    """手动保存用户记忆"""
    agent = get_agent()
    valid_categories = ["event", "ongoing", "personality", "info", "preference"]
    if request.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"无效的记忆类别，支持: {valid_categories}"
        )
    agent.add_user_memory_manual(request.category, request.content)
    return {"status": "success", "message": f"记忆已保存: {request.category}"}


@app.get("/api/characters")
async def list_characters():
    """列出所有已保存的角色"""
    agent = get_agent()
    return {"characters": agent.list_saved_characters()}


@app.post("/api/characters/generate", response_model=CharacterResponse)
async def generate_character(request: CharacterRequest):
    """
    生成新角色
    输入角色名称和出处，LLM自动生成8维角色画像和System Prompt
    """
    agent = get_agent()
    try:
        result = agent.generate_character(request.name, request.source)
        return CharacterResponse(
            name=request.name,
            system_prompt=result.get("system_prompt", ""),
            profile=result.get("profile", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"角色生成失败: {str(e)}")


@app.post("/api/characters/load")
async def load_character(request: CharacterRequest):
    """加载已保存的角色"""
    agent = get_agent()
    profile = agent.load_character(request.name)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"角色 {request.name} 不存在")
    return {"name": request.name, "profile": profile}


@app.post("/api/history/clear")
async def clear_history():
    """清空对话历史（不清空长期记忆）"""
    agent = get_agent()
    agent.clear_history()
    return {"status": "success", "message": "对话历史已清空"}


@app.get("/api/tools")
async def list_tools():
    """列出所有可用工具"""
    agent = get_agent()
    tools = agent.tool_registry.list_tools()
    schemas = agent.tool_registry.get_function_schemas()
    return {"tools": tools, "schemas": schemas}


@app.get("/api/agents/status")
async def get_agents_status():
    """获取多Agent协作系统的详细状态"""
    agent = get_agent()
    return agent.get_multi_agent_status()


# ========== 启动入口 ==========

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("桌面AI陪伴Agent - 服务端API")
    print("多Agent架构：Planner + Memory + Tool")
    print("=" * 60)
    print("API文档: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
