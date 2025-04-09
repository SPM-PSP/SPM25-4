import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ultralytics.utils.plotting
from ultralytics import YOLO
from config import Config



def detect_tampering(original_path,processed_path,model_type):
    if model_type == 'ps':
        model = YOLO(Config.PS_MODEL_PATH)
    elif model_type == 'faceapp':
        model = YOLO(Config.FACEAPP_MODEL_PATH)
    else:
        model = YOLO(Config.PS_MODEL_PATH)
    # 推理
    results = model(original_path)
    # 遍历推理结果
    for result in results:
        # 获取预测的边界框、类别和置信度
        boxes = result.boxes.cpu().numpy()
        classes = boxes.cls  # 类别信息
        confidences = boxes.conf  # 置信度信息

        # 获取预测的掩膜
        masks = result.masks
        if masks is not None:
            masks = masks.data.cpu().numpy()

        # 读取原始图像
        image = cv2.imread(original_path)
        height, width = image.shape[:2]

        # 将 OpenCV 图像转换为 PIL 图像
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)

        # 加载中文字体
        font = ImageFont.truetype("simhei.ttf", 15)  # 这里使用黑体字体，你可以根据实际情况修改字体文件路径

        # 可视化边界框和掩膜
        for i in range(len(boxes)):
            # 获取边界框坐标
            x1, y1, x2, y2 = boxes[i].xyxy[0].astype(int)

            # 计算边界框的宽、高和面积
            box_width = x2 - x1
            box_height = y2 - y1
            box_area = box_width * box_height

            # 绘制边界框
            draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 0), width=2)

            # 修改显示的文字信息
            confidence = confidences[i]
            class_id = int(classes[i])
            class_name = model.names[class_id]
            text = f'篡改部分 置信度: {confidence:.2f} 宽: {box_width} 高: {box_height} 面积: {box_area}'

            # 使用 PIL 绘制中文文本
            draw.text((x1, y1 - 15), text, font=font, fill=(0, 255, 0))

            # 绘制掩膜
            if masks is not None:
                mask = masks[i]
                mask = cv2.resize(mask.astype(np.uint8), (width, height))
                mask = np.stack([mask * 255] * 3, axis=-1)
                mask_image = Image.fromarray(mask)
                pil_image = Image.blend(pil_image, mask_image, alpha=0.3)

        # 将 PIL 图像转换回 OpenCV 图像
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        cv2.imwrite(processed_path, image)