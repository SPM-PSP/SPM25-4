import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
import os

def process_frames(input_folder, output_folder):
    # 加载模型
    model = YOLO('weights/faceapp.pt')
    # 加载中文字体
    font = ImageFont.truetype("simhei.ttf", 15)  # 这里使用黑体字体，你可以根据实际情况修改字体文件路径

    # 遍历输入文件夹中的所有帧
    for filename in os.listdir(input_folder):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            frame_path = os.path.join(input_folder, filename)
            # 推理
            results = model(frame_path)
            # 遍历推理结果
            for result in results:
                # 获取预测的边界框、类别和置信度
                boxes = result.boxes.cpu().numpy()
                confidences = boxes.conf  # 置信度信息
                # 获取预测的掩膜
                masks = result.masks
                if masks is not None:
                    masks = masks.data.cpu().numpy()

                # 读取原始图像
                image = cv2.imread(frame_path)
                height, width = image.shape[:2]

                # 将 OpenCV 图像转换为 PIL 图像
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image)
                draw = ImageDraw.Draw(pil_image)

                # 可视化边界框和文本
                for i in range(len(boxes)):
                    # 获取边界框坐标
                    x1, y1, x2, y2 = boxes[i].xyxy[0].astype(int)
                    # 绘制边界框
                    draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 0), width=2)
                    # 修改显示的文字信息
                    confidence = confidences[i]
                    text = f'置信度: {confidence:.2f}'
                    # 使用 PIL 绘制中文文本
                    draw.text((x1, y1 - 15), text, font=font, fill=(0, 255, 0))

                # 绘制掩膜
                if masks is not None:
                    # 创建一个与原始图像相同大小的空白图像用于绘制掩膜
                    mask_image = Image.new('RGB', (width, height), color=(0, 0, 0))
                    mask_draw = ImageDraw.Draw(mask_image)
                    for i in range(len(masks)):
                        mask = masks[i]
                        mask = cv2.resize(mask.astype(np.uint8), (width, height))
                        mask = np.stack([mask * 255] * 3, axis=-1)
                        mask_img = Image.fromarray(mask)
                        # 将掩膜绘制到空白图像上
                        mask_image = Image.blend(mask_image, mask_img, alpha=0.4)
                    # 将绘制好掩膜的图像与原始图像融合
                    pil_image = Image.blend(pil_image, mask_image, alpha=0.5)

                # 将 PIL 图像转换回 OpenCV 图像
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                # 保存处理后的帧
                output_path = os.path.join(output_folder, filename)
                cv2.imwrite(output_path, image)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python frame_detection.py <input_folder> <output_folder>")
        sys.exit(1)
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    process_frames(input_folder, output_folder)