import os
import uuid
import subprocess
import threading
import cv2
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from config import Config
from db_utils import init_db, insert_detection_result, insert_image_record, \
    get_detected_objects, get_detection_result_id, get_image_report, get_full_detection_data, insert_video_record
from pdf_generator import ReportGenerator
from image_detector import detect_tampering
from llm_reporter import generate_report, generate_followup_response

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# 注册支持中文的字体，这里以 SimHei 为例，确保系统中有该字体文件
pdfmetrics.registerFont(TTFont('SimHei', 'SimHei.ttf'))

app = Flask(__name__)
app.config.from_object(Config)
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

        # 存储数据库记录
        try:
            # 调用检测模型
            report_data = detect_tampering(original_path, processed_path, model_type=model_type)

            # 调用数据库操作
            insert_detection_result(
                processed_filename=processed_filename,
                objects=report_data["objects"]
            )

        except Exception as e:  # 统一捕获模型和数据库异常
            return jsonify({'error': f'Internal error: {str(e)}'}), 500

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

        # 计算文件名参数
        original_filename = os.path.basename(processed_path).replace('_processed.png', '_original.png')
        processed_filename = os.path.basename(processed_path)

        # 调用解耦后的数据库操作
        insert_image_record(
            original_filename=original_filename,
            processed_filename=processed_filename,
            report_text=report,
            created_at=datetime.now()
        )

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
        return jsonify({'error': 'No video part','success': False}), 400

    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No selected video','success': False}), 400

    if video and allowed_file(video.filename):
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        original_ext = video.filename.rsplit('.', 1)[1].lower()
        original_filename = f"{file_id}_original.{original_ext}"
        original_path = os.path.join(Config.VIDEOS_UPLOADS_DIR, 'original', original_filename)
        video.save(original_path)

        # 启动视频预处理线程
        def preprocess_video():
            try:
                subprocess.run(['python', 'video_preprocess.py', original_path, file_id], check=True)
            except subprocess.CalledProcessError as e:
                print(f"视频预处理出错: {e}")

        threading.Thread(target=preprocess_video).start()

        # 获取视频总帧数
        cap = cv2.VideoCapture(original_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        return jsonify({'success': True, 'total_frames': total_frames, 'file_id': file_id})

    return jsonify({'error': 'Invalid video','success': False}), 400

@app.route('/start_detection', methods=['POST'])
def start_detection():
    # 从请求中获取 file_id
    data = request.get_json()
    file_id = data.get('file_id')
    if not file_id:
        return jsonify({'error': 'No file_id provided','success': False}), 400

    original_ext = data.get('original_ext')
    original_filename = f"{file_id}_original.{original_ext}"

    try:
        # 使用AI模型处理帧
        frame_folder = os.path.join(Config.VIDEOS_UPLOADS_DIR, 'frame', file_id)
        processed_frame_folder = os.path.join(Config.VIDEOS_UPLOADS_DIR, 'processed_frame', file_id)
        os.makedirs(processed_frame_folder, exist_ok=True)
        subprocess.run(['python', 'frame_detector.py', frame_folder, processed_frame_folder], check=True)

        # 合成处理后的视频
        processed_video_filename = f"processed_{original_filename}"
        processed_video_path = os.path.join(Config.VIDEOS_UPLOADS_DIR, 'processed_video', processed_video_filename)
        subprocess.run(['python', 'video_generator.py', processed_frame_folder, processed_video_path], check=True)

        # 插入数据库记录
        frame_folder_name = file_id
        insert_video_record(original_filename, frame_folder_name)

        # 返回处理后视频的URL
        processed_video_url = f"/processed_video/{processed_video_filename}"
        return jsonify({'success': True,'message': 'Detection and video generation completed', 'processed_video_url': processed_video_url}), 200
    except subprocess.CalledProcessError as e:
        print(f"检测和视频生成出错: {e}")
        return jsonify({'error': 'Error during detection and video generation','success': False}), 500

@app.route('/check_processing_progress')
def check_processing_progress():
    # 简单模拟处理视频处理进度
    try:
        with open(Config.PROGRESS_TXT_PATH, 'r') as f:
            processed_frames = int(f.read())
    except FileNotFoundError:
        processed_frames = 0
    return jsonify({'processed_frames': processed_frames})

@app.route('/processed_video/<filename>')
def serve_processed_video(filename):
    return send_from_directory(os.path.join(Config.VIDEOS_UPLOADS_DIR, 'processed_video'), filename)

@app.route('/get_detection_info', methods=['POST'])
def get_detection_info():
    data = request.get_json()
    processed_filename = data.get('processed_filename')

    if not processed_filename:
        return jsonify({'error': 'Missing processed_filename'}), 400

    try:
        # 获取检测结果ID
        result_id = get_detection_result_id(processed_filename)
        if not result_id:
            return jsonify({'error': 'Detection results not found'}), 404

        # 获取检测对象信息
        detection_info = get_detected_objects(result_id)
        return jsonify({'detection_info': detection_info})

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/export_report', methods=['POST'])
def export_report():
    # 请求参数处理
    data = request.get_json()
    raw_filename = data.get('processed_filename')
    if not raw_filename:
        return jsonify({'error': 'Missing filename'}), 400

    try:
        # 文件名标准化处理
        processed_filename = raw_filename.split('\\')[-1]

        # 获取报告数据
        base_info = get_image_report(processed_filename)
        detection_objects = get_full_detection_data(processed_filename)

        # 生成PDF报告
        report_data = {
            **base_info,
            "detection_objects": detection_objects
        }
        pdf_path = ReportGenerator(Config).generate_pdf(processed_filename, report_data)

        return send_file(pdf_path, as_attachment=True)

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'PDF生成失败: {str(e)}'}), 500


if __name__ == '__main__':
    os.makedirs(os.path.join(Config.VIDEOS_UPLOADS_DIR, 'original'), exist_ok=True)
    os.makedirs(os.path.join(Config.VIDEOS_UPLOADS_DIR, 'frame'), exist_ok=True)
    os.makedirs(Config.REPORT_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
