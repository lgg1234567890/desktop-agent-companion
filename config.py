# -*- coding: utf-8 -*-
"""配置文件"""

# === 大模型 API 配置（阿里云百炼兼容模式）===
LLM_API_KEY = "sk-ws-H.EXHIPRH.Cxyl.MEUCIQChYoGgVlmuyEkDS07OLx--5Ynlcnyu71kw3_uQm2A1UgIgCcLnFHaYsyvIhT9njvmg0fP_gUQTH23SvMf8oL0fc_4"
LLM_MODEL = "glm-5"
LLM_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
LLM_TIMEOUT = 30

# === 桌宠尺寸 ===
DEFAULT_PET_WIDTH = 180
DEFAULT_PET_HEIGHT = 260
MIN_PET_WIDTH = 80
MAX_PET_WIDTH = 400

# === 动画速度 ===
WALK_SPEED = 3
CRAWL_SPEED = 2
TICK_INTERVAL = 40

# === 互动动作持续时间（10秒，避免频闪）===
INTERACTION_DURATION = 10000
BUBBLE_DURATION = 3000

# === 自主活动 ===
IDLE_TO_WALK_MIN = 3000
IDLE_TO_WALK_MAX = 6000
WALK_TO_IDLE_MIN = 8000
WALK_TO_IDLE_MAX = 15000

MAX_HISTORY = 20
