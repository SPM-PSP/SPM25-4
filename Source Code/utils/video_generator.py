import imageio
import os
import re
import sys
from tqdm import tqdm  # 用于进度条提示


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
    first_frame = imageio.v3.imread(os.path.join(input_folder, images[0]))
    height, width, _ = first_frame.shape

    # 创建视频写入器（自动处理编码器）
    writer = imageio.get_writer(
        output_video_path,
        fps=fps,
        codec="libx264",  # 使用广泛支持的H.264编码
        quality=8,  # 质量参数（0-10）
        pixelformat="yuv420p",
        macro_block_size=16  # 确保能被16整除
    )

    # 逐帧写入并显示进度
    try:
        for img_file in tqdm(images, desc="生成视频"):
            img_path = os.path.join(input_folder, img_file)
            frame = imageio.v3.imread(img_path)

            # 检查帧尺寸一致性
            if frame.shape != first_frame.shape:
                raise ValueError(f"帧 {img_file} 的尺寸不一致")

            writer.append_data(frame)
    finally:
        writer.close()  # 确保总是会关闭写入器

    print(f"\n视频已成功保存至：{output_video_path}")


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