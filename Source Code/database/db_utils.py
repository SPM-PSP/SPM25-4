import pymysql
from config import Config


def create_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def init_db():
    conn = create_connection()
    try:
        with conn.cursor() as cursor:
            # 创建 images 表
            cursor.execute('''CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                original_filename VARCHAR(255) NOT NULL,
                processed_filename VARCHAR(255) NOT NULL,
                report_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            # 创建 videos 表
            cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
                video_id INT AUTO_INCREMENT PRIMARY KEY,
                original_filename VARCHAR(255) NOT NULL,
                frame_folder_name VARCHAR(255) NOT NULL,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        conn.commit()
    finally:
        conn.close()


def insert_video_record(original_filename, frame_folder_name):
    conn = create_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO videos (original_filename, frame_folder_name) VALUES (%s, %s)"
            cursor.execute(sql, (original_filename, frame_folder_name))
        conn.commit()
    finally:
        conn.close()
