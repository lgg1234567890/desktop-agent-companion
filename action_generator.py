# -*- coding: utf-8 -*-
"""动作图片生成器：基于建模图片，AI生成13种动作，自动抠图保存"""
import os
import json
import time
import requests
from PIL import Image
import numpy as np

import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CONFIG_FILE = os.path.join(BASE_DIR, "api_config.json")

# 13种动作的中文描述
ACTION_DESCRIPTIONS = {
    "idle": "待机站立，自然站立姿势，双手自然下垂",
    "walk": "行走，步行姿势，一腿向前迈出",
    "monkey_crawl": "猴子爬行，四肢着地爬行，像猴子一样灵活",
    "slash": "挥刀斩击，手持黑金古刀用力挥砍，动作凌厉",
    "qilin_blood": "麒麟放血，手臂流血，鲜血滴落，表情冷峻",
    "two_fingers": "二指探洞，伸出两指探查洞穴机关，专注神情",
    "jump": "跳跃飞身，腾空跃起，身体舒展，动作矫健",
    "crouch": "蹲下探查，蹲下身姿，低头查看地面，警惕神情",
    "nod": "点头致意，微微点头，表情平静，礼貌回应",
    "injured": "受伤踉跄，身体摇晃，手扶伤口，表情痛苦但坚韧",
    "squeeze": "缩骨钻缝，身体收缩扭曲，钻入狭窄缝隙",
    "eat_noodle": "吃泡面，手持泡面桶，用筷子吃面条，日常神态",
    "kneel": "单膝跪地，低头姿态，恭敬或认错神情",
    "kneel_apologize": "双膝跪地，低头认错，懊悔神情",
    "climb": "攀岩攀爬，双手抓握岩壁，身体向上攀登",
    "sit": "坐在边缘，双腿垂下，放松坐姿",
    "fall": "坠落下落，身体失去平衡，空中坠落姿态",
}


def load_config():
    """加载配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def remove_background(image_path, output_path=None):
    """去除图片背景，返回透明背景图片路径"""
    try:
        img = Image.open(image_path).convert("RGBA")
        data = np.array(img)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        # 白色/浅色背景设为透明
        mask = (r > 200) & (g > 200) & (b > 200)
        data[mask, 3] = 0
        # 灰白棋盘格背景设为透明
        gray_mask = (np.abs(r.astype(int) - g.astype(int)) < 15) & \
                    (np.abs(g.astype(int) - b.astype(int)) < 15) & \
                    (r > 180)
        data[gray_mask, 3] = 0
        result = Image.fromarray(data)
        if output_path:
            result.save(output_path, "PNG")
            return output_path
        # 保存到临时文件
        temp_path = image_path.rsplit(".", 1)[0] + "_transparent.png"
        result.save(temp_path, "PNG")
        return temp_path
    except Exception as e:
        print(f"抠图失败: {e}")
        return image_path


def generate_action_image(prompt, api_key, model="wanx2.1-t2i-turbo", size="1024*1024"):
    """调用阿里云百炼通义万相生成图片（文生图）"""
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    payload = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": 1}
    }

    # 提交任务
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    task_data = resp.json()
    task_id = task_data.get("output", {}).get("task_id")
    if not task_id:
        raise Exception(f"提交生成任务失败: {task_data}")

    # 轮询结果
    result_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    for _ in range(60):  # 最多等5分钟
        time.sleep(5)
        resp = requests.get(result_url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("output", {}).get("task_status")
        if status == "SUCCEEDED":
            results = data.get("output", {}).get("results", [])
            if results:
                return results[0].get("url")
            raise Exception("生成成功但无图片URL")
        elif status == "FAILED":
            raise Exception(f"生成失败: {data}")
    raise Exception("生成超时")


def download_image(url, save_path):
    """下载图片到本地"""
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(resp.content)
    return save_path


def generate_all_actions(model_image_path=None, character_desc=None, progress_callback=None):
    """
    生成所有动作图片
    :param model_image_path: 建模图片路径（用于参考角色形象，当前版本用于提取角色描述）
    :param character_desc: 角色描述（如"张起灵，黑色连帽衫，黑金古刀，冷峻青年"）
    :param progress_callback: 进度回调函数 callback(action_name, index, total)
    :return: 成功生成的动作数量
    """
    cfg = load_config()
    api_key = cfg.get("api_key", "").strip()
    if not api_key:
        raise Exception("未配置API Key，请在角色设置中配置")

    # 角色描述：优先用传入的，其次用配置中的角色来源
    if not character_desc:
        character_desc = cfg.get("character_source", "").strip()
    if not character_desc:
        character_desc = "神秘冷峻的青年，黑色连帽衫，手持黑金古刀，盗墓笔记风格"

    os.makedirs(ASSETS_DIR, exist_ok=True)
    total = len(ACTION_DESCRIPTIONS)
    success_count = 0

    for idx, (action_name, action_desc) in enumerate(ACTION_DESCRIPTIONS.items()):
        if progress_callback:
            progress_callback(action_name, idx, total)

        try:
            # 构造prompt：角色描述 + 动作描述 + 风格要求
            prompt = (
                f"{character_desc}，{action_desc}。"
                f"全身像，纯白色背景，动漫插画风格，高清细节，"
                f"人物居中，完整身体，无多余物体。"
            )

            # 生成图片
            img_url = generate_action_image(prompt, api_key)

            # 下载图片
            temp_path = os.path.join(ASSETS_DIR, f"{action_name}_raw.png")
            download_image(img_url, temp_path)

            # 抠图（去除白色背景）
            output_path = os.path.join(ASSETS_DIR, f"{action_name}.png")
            remove_background(temp_path, output_path)

            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

            success_count += 1
            print(f"[{idx+1}/{total}] {action_name} 生成成功")

        except Exception as e:
            print(f"[{idx+1}/{total}] {action_name} 生成失败: {e}")
            continue

    if progress_callback:
        progress_callback("完成", total, total)

    return success_count


if __name__ == "__main__":
    # 测试：生成所有动作
    count = generate_all_actions()
    print(f"成功生成 {count} 个动作图片")
