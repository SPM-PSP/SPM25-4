import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from config import Config
import time

def detect_tampering(original_path, processed_path, model_type):
    if model_type == 'ps':
        model = YOLO(Config.PS_MODEL_PATH)
    elif model_type == 'faceapp':
        model = YOLO(Config.FACEAPP_MODEL_PATH)
    else:
        model = YOLO(Config.PS_MODEL_PATH)

    # 推理
    results = model(original_path)

    report_data = {
        "objects": []
    }

    # 遍历推理结果
    for result in results:
        # 获取预测的边界框、类别和置信度
        boxes = result.boxes.cpu().numpy()
        confidences = boxes.conf  # 置信度信息
        class_ids = boxes.cls.astype(int)  # 类别 ID
        class_names = result.names  # 类别名称字典

        # 获取预测的掩膜
        masks = result.masks
        if masks is not None:
            masks = masks.data.cpu().numpy()

        # 读取原始图像
        image = cv2.imread(original_path)
        height, width = image.shape[:2]

        # 根据图片宽度动态计算字号
        font_size = int(width * 0.05)  # 可根据实际情况调整比例
        if font_size < 10:
            font_size = 10  # 确保字号不小于 10

        # 将 OpenCV 图像转换为 PIL 图像
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)

        # 加载中文字体
        font = ImageFont.truetype("simhei.ttf", font_size)  # 使用动态计算的字号

        # 检测到的目标数量
        num_objects = len(boxes)
        report_data["num_objects"] = num_objects

        # 可视化边界框和文本
        for i in range(len(boxes)):
            # 获取边界框坐标
            x1, y1, x2, y2 = boxes[i].xyxy[0].astype(int)
            # 计算中心点坐标
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # 绘制边界框
            draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 0), width=2)

            # 获取类别名称
            class_id = class_ids[i]
            class_name = class_names[class_id]

            # 修改显示的文字信息
            confidence = confidences[i]
            text = f'篡改概率: {confidence:.2f}'
            # 使用 PIL 绘制中文文本
            draw.text((x1, y1 - font_size), text, font=font, fill=(0, 255, 0))

            object_info = {
                "class_name": class_name,
                "confidence": float(confidence),
                "center_x": center_x,
                "center_y": center_y
            }
            report_data["objects"].append(object_info)

        # 绘制掩膜
        if masks is not None:
            # 创建一个与原始图像相同大小的空白图像用于绘制掩膜
            mask_image = Image.new('RGB', (width, height), color=(0, 0, 0))
            for i in range(len(masks)):
                mask = masks[i]
                mask = cv2.resize(mask.astype(np.uint8), (width, height))
                mask = np.stack([mask * 255] * 3, axis=-1)
                mask_img = Image.fromarray(mask)
                # 将掩膜绘制到空白图像上
                mask_image = Image.blend(mask_image, mask_img, alpha=0.4)
            # 将绘制好掩膜的图像与原始图像融合
            pil_image = Image.blend(pil_image, mask_image, alpha=0.4)

        # 保存最终结果
        cv2.imwrite(processed_path, cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR))

    return report_data