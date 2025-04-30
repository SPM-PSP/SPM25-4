import cv2
import os
import re
import sys

def natural_sort_key(s):
    """按文件名中的数字自然排序"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def combine_frames(input_folder, output_video_path, fps=15):
    # 获取所有图片并排序
    images = [img for img in os.listdir(input_folder)
              if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    images.sort(key=natural_sort_key)

    if not images:
        print("未找到有效的图片帧。")
        return

    # 读取第一张图片确定视频尺寸
    frame_path = os.path.join(input_folder, images[0])
    frame = cv2.imread(frame_path)
    height, width, _ = frame.shape

    # 创建视频写入器（可能需要调整编码器）
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # 逐帧写入
    for image in images:
        img_path = os.path.join(input_folder, image)
        frame = cv2.imread(img_path)
        video.write(frame)

    # 释放资源
    video.release()
    print("视频生成成功！")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python video_generator.py <输入文件夹路径> <输出视频文件路径>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_video_path = sys.argv[2]

    if not os.path.exists(input_folder):
        print(f"输入文件夹 {input_folder} 不存在。")
        sys.exit(1)

    combine_frames(input_folder, output_video_path)