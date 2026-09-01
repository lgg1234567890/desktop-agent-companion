# -*- coding: utf-8 -*-
"""批量处理assets图片：将灰白棋盘格背景转为真正透明"""
import os
from PIL import Image
import numpy as np

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

def process_image(filepath):
    """将图片中的灰白棋盘格背景转为透明"""
    img = Image.open(filepath).convert("RGBA")
    data = np.array(img)
    
    # 提取RGB通道
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # 识别灰白棋盘格：RGB三个通道值都较高(>180)且差值小(<25)，即灰色/白色
    gray_mask = (r > 180) & (g > 180) & (b > 180) & \
                (np.abs(r.astype(int) - g.astype(int)) < 25) & \
                (np.abs(g.astype(int) - b.astype(int)) < 25) & \
                (np.abs(r.astype(int) - b.astype(int)) < 25)
    
    # 将这些像素的alpha设为0（透明）
    data[gray_mask, 3] = 0
    
    # 边缘羽化：对alpha在0-255之间的像素进行平滑
    # 先做一次膨胀，确保棋盘格完全清除
    from scipy import ndimage
    alpha = data[:,:,3]
    # 对透明区域做轻微膨胀，清除边缘残留
    transparent = (alpha == 0)
    dilated = ndimage.binary_dilation(transparent, iterations=1)
    data[dilated & ~transparent, 3] = 0
    
    result = Image.fromarray(data)
    result.save(filepath, "PNG")
    return True

def main():
    count = 0
    for filename in os.listdir(ASSETS_DIR):
        if filename.endswith(".png"):
            filepath = os.path.join(ASSETS_DIR, filename)
            try:
                process_image(filepath)
                print(f"处理完成: {filename}")
                count += 1
            except Exception as e:
                print(f"处理失败 {filename}: {e}")
    print(f"\n共处理 {count} 张图片")

if __name__ == "__main__":
    main()
