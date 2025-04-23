from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import os
import uuid
from config import Config
from database.db_utils import init_db, create_connection
from yolo_detection import detect_tampering
from llm_report import generate_report, generate_followup_response
import subprocess
import threading
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from PIL import Image

# 注册支持中文的字体，这里以 SimHei 为例，确保系统中有该字体文件
pdfmetrics.registerFont(TTFont('SimHei', 'SimHei.ttf'))

app = Flask(__name__)
app.config.from_object(Config)
# 设置最大请求体大小为 1GB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024
init_db()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/image_detect')
def image_detect():
    return render_template('image_detect.html')


@app.route('/video_detect')
def CGdetect():
    return render_template('video_detect.html')


@app.route('/yolo_detect', methods=['POST'])
def yolo_detect():
    # 获取模型类型参数
    model_type = request.form.get('model_type', 'ps')
    if model_type not in ['ps', 'faceapp']:
        return jsonify({'error': 'Invalid model type'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        original_filename = f"{file_id}_original.{original_ext}"
        processed_filename = f"{file_id}_processed.png"

        # 保存原始文件
        original_path = os.path.join(Config.ORIGINAL_DIR, original_filename)
        file.save(original_path)

        # 保存处理结果
        processed_path = os.path.join(Config.PROCESSED_DIR, processed_filename)

        try:
            # 调用检测模型
            report_data = detect_tampering(original_path, processed_path, model_type=model_type)
        except Exception as e:
            return jsonify({'error': f'Model error: {str(e)}'}), 500

        # 存储数据库记录
        conn = create_connection()
        try:
            with conn.cursor() as cursor:
                # 插入主报告信息
                sql = """INSERT INTO detection_results (processed_filename) VALUES (%s)"""
                cursor.execute(sql, (processed_filename,))

                # 获取插入的主记录的 ID
                detection_result_id = cursor.lastrowid

                # 插入每个检测对象的信息
                for obj in report_data["objects"]:
                    sql = """INSERT INTO detected_objects 
                             (detection_result_id, class_name, confidence, center_x, center_y) 
                             VALUES (%s, %s, %s, %s, %s)"""
                    cursor.execute(sql, (
                        detection_result_id,
                        obj["class_name"],
                        obj["confidence"],
                        obj["center_x"],
                        obj["center_y"]
                    ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()

        return jsonify({
            'processed_url': f'/processed/{processed_filename}',
            'processed_path': processed_path,
            'model_type': model_type
        })

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/generate_report', methods=['POST'])
def generate_report_route():
    data = request.get_json()
    processed_path = data.get('processed_path')
    model_type = data.get('model_type')
    try:
        # 生成文字报告
        report = generate_report(processed_path)
        # 存储数据库记录
        conn = create_connection()
        created_at = datetime.now()
        try:
            with conn.cursor() as cursor:
                sql = """INSERT INTO images 
                    (original_filename, processed_filename, report_text, created_at) 
                    VALUES (%s, %s, %s, %s)"""
                cursor.execute(sql, (
                    os.path.basename(processed_path).replace('_processed.png', '_original.png'),
                    os.path.basename(processed_path),
                    report,
                    created_at
                ))
            conn.commit()
        finally:
            conn.close()
        return jsonify({
            'report': report,
            'model_type': model_type
        })
    except Exception as e:
        return jsonify({'error': f'Report generation error: {str(e)}'}), 500


@app.route('/generate_followup', methods=['POST'])
def generate_followup():
    data = request.get_json()
    processed_path = data.get('processed_path')
    question = data.get('question')
    previous_messages = data.get('previous_messages', [])

    try:
        response = generate_followup_response(processed_path, question, previous_messages)
        return jsonify({
            'response': response
        })
    except Exception as e:
        return jsonify({'error': f'Follow - up response error: {str(e)}'}), 500


@app.route('/processed/<filename>')
def send_processed_image(filename):
    return send_from_directory(Config.PROCESSED_DIR, filename)


@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video part', 'success': False}), 400

    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No selected video', 'success': False}), 400

    if video and allowed_file(video.filename):
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        original_ext = video.filename.rsplit('.', 1)[1].lower()
        original_filename = f"{file_id}_original.{original_ext}"
        original_path = os.path.join(Config.VIDEOS_UPLOADS_DIR, 'original', original_filename)
        video.save(original_path)

        # 启动视频处理线程
        def process_video():
            try:
                subprocess.run(['python', 'video_preprocess.py', original_path, file_id], check=True)
            except subprocess.CalledProcessError as e:
                print(f"视频处理出错: {e}")

        threading.Thread(target=process_video).start()

        # 获取视频总帧数
        import cv2
        cap = cv2.VideoCapture(original_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        return jsonify({'success': True, 'total_frames': total_frames})

    return jsonify({'error': 'Invalid video', 'success': False}), 400


@app.route('/check_processing_progress')
def check_processing_progress():
    # 这里简单模拟处理进度，实际可根据视频处理情况更新
    try:
        with open('processing_progress.txt', 'r') as f:
            processed_frames = int(f.read())
    except FileNotFoundError:
        processed_frames = 0
    return jsonify({'processed_frames': processed_frames})


@app.route('/get_detection_info', methods=['POST'])
def get_detection_info():
    data = request.get_json()
    processed_filename = data.get('processed_filename')

    if processed_filename is None:
        return jsonify({'error': 'Missing processed_filename in request data'}), 400

    conn = create_connection()
    try:
        with conn.cursor() as cursor:
            # 获取检测结果ID
            cursor.execute("SELECT id FROM detection_results WHERE processed_filename = %s", (processed_filename,))
            detection_result_id = cursor.fetchone()
            if detection_result_id is None:
                return jsonify({'error': 'Detection results not found for the given processed_filename'}), 404

            detection_result_idn = detection_result_id[0]
            # 获取目标检测信息
            cursor.execute(
                "SELECT class_name, confidence, center_x, center_y FROM detected_objects WHERE detection_result_id = %s",
                (detection_result_idn,))
            detection_info = cursor.fetchall()

            result = [
                {
                    'class_name': row[0],
                    'confidence': row[1],
                    'center_x': row[2],
                    'center_y': row[3]
                }
                for row in detection_info
            ]

            return jsonify({'detection_info': result})
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/export_report', methods=['POST'])
def export_report():
    data = request.get_json()
    processed_filename = data.get('processed_filename')
    processed_filename=processed_filename.split('\\')[-1]

    if processed_filename is None:
        return jsonify({'error': 'Missing processed_filename in request data'}), 400

    conn = create_connection()
    try:
        with conn.cursor() as cursor:
            # 获取LLM报告结果和检测完成时间
            cursor.execute("SELECT report_text, created_at FROM images WHERE processed_filename = %s",
                           (processed_filename,))
            image_info = cursor.fetchone()
            if image_info is None:
                return jsonify({'error': 'Report text not found for the given processed_filename'}), 404

            report_text= str(image_info.get('report_text'))
            created_at = str(image_info.get('created_at'))

            # 获取检测结果ID
            cursor.execute("SELECT id FROM detection_results WHERE processed_filename = %s", (processed_filename,))
            detection_result_id = cursor.fetchone()
            if detection_result_id is None:
                return jsonify({'error': 'Detection results not found for the given processed_filename'}), 404

            detection_result_idn = detection_result_id.get('id')

            # 获取目标检测信息
            cursor.execute(
                "SELECT class_name, confidence, center_x, center_y FROM detected_objects WHERE detection_result_id = %s",
                (detection_result_idn,))
            detection_info = cursor.fetchall()
            detection_info_text = '\n'.join(
                [f'类别: {row["class_name"]}, 置信度: {row["confidence"]}, 中心坐标: ({row["center_x"]}, {row["center_y"]})'
                 for row in detection_info])
            # 将换行符替换为<br/>标签
            detection_info_text_html = detection_info_text.replace('\n', '<br/>')

            # 生成PDF报告
            pdf_path = os.path.join(Config.REPORT_DIR, f'{processed_filename.replace(".png", ".pdf")}')
            c = canvas.Canvas(pdf_path, pagesize=letter)

            # 添加标题
            c.setFont('SimHei', 20)
            c.drawString(50, 750, '图像篡改检测报告')

            # 添加检测完成时间
            c.setFont('SimHei', 12)
            timestr='检测完成时间:'+created_at
            c.drawString(50, 720, timestr)

            # 添加原始图片
            original_image_path = os.path.join(Config.ORIGINAL_DIR,
                                               processed_filename.replace('_processed.png', '_original.jpg'))
            if os.path.exists(original_image_path):
                try:
                    img = Image.open(original_image_path)
                    img_width, img_height = img.size
                    aspect = img_height / float(img_width)
                    c.drawImage(original_image_path, 50, 500, width=200, height=(200 * aspect))
                except Exception as img_error:
                    print(f"添加原始图片时出错: {img_error}")

            # 添加处理后图片
            processed_image_path = os.path.join(Config.PROCESSED_DIR, processed_filename)
            if os.path.exists(processed_image_path):
                try:
                    img = Image.open(processed_image_path)
                    img_width, img_height = img.size
                    aspect = img_height / float(img_width)
                    c.drawImage(processed_image_path, 50, 250, width=200, height=(200 * aspect))
                except Exception as img_error:
                    print(f"添加处理后图片时出错: {img_error}")

            # 添加LLM报告
            styleSheet = getSampleStyleSheet()
            style = styleSheet['Normal']
            style.fontName = 'SimHei'
            style.fontSize = 12
            para = Paragraph(report_text, style)
            para.wrapOn(c, 500, 700)
            para.drawOn(c, 50, 670)

            # 添加目标检测信息
            c.showPage()
            c.setFont('SimHei', 12)
            c.drawString(50, 760, '目标检测信息')
            para = Paragraph(detection_info_text_html, style)
            para.wrapOn(c, 500, 700)
            para.drawOn(c, 50, 720)

            c.save()
            return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'PDF generation error: {str(e)}'}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    os.makedirs(os.path.join(Config.VIDEOS_UPLOADS_DIR, 'original'), exist_ok=True)
    os.makedirs(os.path.join(Config.VIDEOS_UPLOADS_DIR, 'frame'), exist_ok=True)
    os.makedirs(Config.REPORT_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
