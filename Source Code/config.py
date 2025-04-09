import os

class Config:
    # 文件存储配置
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB限制

    # MySQL数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DB = 'image_db'

    # 路径配置
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROCESSED_DIR = os.path.join(BASE_DIR, 'uploads/processed')
    ORIGINAL_DIR = os.path.join(BASE_DIR, 'uploads/original')

    # 大语言模型API配置
    API_KEY = 'Bearer sk-N5SRoE71R7b6hQstssjz7GNA9kgEmGw8796lFwxLhZmwv6WG'
    API_ENDPOINT = "xiaoai.plus"
    API_URL= "/v1/chat/completions"
    API_MODEL = "gpt-4o"
    API_PROMPT = ("这是一张被篡改过的图片，已经进行了标记，图片中绿色矩形框内是识别的篡改位置，篡改部分已经高亮显示，请根据图片给出篡改部分报告。"
                  "注意，如果没有标记，则说明图片未被篡改。请不要给出“根据标记”等词，直接针对篡改位置和图像进行分析")

    # 图像篡改识别模型配置
    PS_MODEL_PATH = "weights/ps.pt"
    FACEAPP_MODEL_PATH = "weights/faceapp.pt"