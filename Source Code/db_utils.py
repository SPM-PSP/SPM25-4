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

def insert_detection_result(processed_filename, objects):
    """插入主记录和检测对象（原子事务操作）

    Args:
        processed_filename: 处理后的文件名
        objects: 检测对象列表

    Returns:
        detection_result_id: 插入的主记录ID

    Raises:
        Exception: 数据库操作异常
    """
    conn = None
    try:
        conn = create_connection()
        with conn.cursor() as cursor:
            # 插入主记录
            main_sql = """INSERT INTO detection_results (processed_filename)
                          VALUES (%s)"""
            cursor.execute(main_sql, (processed_filename,))
            detection_result_id = cursor.lastrowid

            # 插入检测对象
            if objects:
                obj_sql = """INSERT INTO detected_objects
                             (detection_result_id, class_name, confidence, center_x, center_y)
                             VALUES (%s, %s, %s, %s, %s)"""
                obj_data = [
                    (detection_result_id,
                     obj["class_name"],
                     obj["confidence"],
                     obj["center_x"],
                     obj["center_y"])
                    for obj in objects
                ]
                cursor.executemany(obj_sql, obj_data)

            conn.commit()
            return detection_result_id
    except Exception as e:
        if conn:
            conn.rollback()
        raise e  # 将异常抛给上层处理
    finally:
        if conn:
            conn.close()

def insert_image_record(original_filename, processed_filename, report_text, created_at):
    """原子化插入图片记录

    Args:
        original_filename: 原始文件名
        processed_filename: 处理后的文件名
        report_text: 报告文本
        created_at: 创建时间

    Raises:
        Exception: 包含所有数据库异常
    """
    conn = None
    try:
        conn = create_connection()
        with conn.cursor() as cursor:
            sql = """INSERT INTO images 
                    (original_filename, processed_filename, report_text, created_at) 
                    VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (
                original_filename,
                processed_filename,
                report_text,
                created_at
            ))
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def get_detection_result_id(processed_filename):
    """根据 processed_filename 获取检测结果 ID"""
    conn = None
    try:
        conn = create_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM detection_results WHERE processed_filename = %s",
                (processed_filename,)
            )
            result = cursor.fetchone()
            return result['id'] if result else None
    except Exception as e:
        raise RuntimeError(f"Detection result query failed: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_detected_objects(detection_result_id):
    """根据检测结果 ID 获取目标检测信息"""
    conn = None
    try:
        conn = create_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT class_name, confidence, center_x, center_y 
                FROM detected_objects 
                WHERE detection_result_id = %s""",
                (detection_result_id,)
            )
            return [
                {
                    'class_name': row['class_name'],
                    'confidence': float(row['confidence']),
                    'center_x': float(row['center_x']),
                    'center_y': float(row['center_y']
                )} for row in cursor.fetchall()
            ]
    except Exception as e:
        raise RuntimeError(f"Detected objects query failed: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_image_report(processed_filename):
    """获取图片报告基础信息"""
    conn = None
    try:
        conn = create_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT report_text, created_at FROM images WHERE processed_filename = %s",
                (processed_filename,)
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError("Image report not found")
            return {
                "report_text": str(result["report_text"]),
                "created_at": str(result["created_at"])
            }
    except Exception as e:
        raise RuntimeError(f"Image report query failed: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_full_detection_data(processed_filename):
    """获取完整检测数据"""
    conn = None
    try:
        conn = create_connection()
        with conn.cursor() as cursor:
            # 获取检测结果ID
            cursor.execute(
                "SELECT id FROM detection_results WHERE processed_filename = %s",
                (processed_filename,)
            )
            result_id = cursor.fetchone()
            if not result_id:
                raise ValueError("Detection result not found")

            # 获取检测对象信息
            cursor.execute(
                """SELECT class_name, confidence, center_x, center_y 
                FROM detected_objects 
                WHERE detection_result_id = %s""",
                (result_id["id"],)
            )
            objects = [
                {
                    "class_name": row["class_name"],
                    "confidence": float(row["confidence"]),
                    "center_x": float(row["center_x"]),
                    "center_y": float(row["center_y"])
                } for row in cursor.fetchall()
            ]

            return objects
    except Exception as e:
        raise RuntimeError(f"Detection data query failed: {str(e)}")
    finally:
        if conn:
            conn.close()

def insert_video_record(original_filename, frame_folder_name):
    conn = create_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO videos (original_filename, frame_folder_name, create_time) VALUES (%s, %s, NOW())"
            cursor.execute(sql, (original_filename, frame_folder_name))
        conn.commit()
    finally:
        conn.close()