# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
from config import Config
from database.db_utils import init_db, create_connection
from yolo_detection import detect_tampering
from llm_report import generate_report

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

        try:
            # 调用检测模型
            detect_tampering(original_path, processed_path, model_type=model_type)
        except Exception as e:
            return jsonify({'error': f'Model error: {str(e)}'}), 500

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
        try:
            with conn.cursor() as cursor:
                sql = """INSERT INTO images 
                    (original_filename, processed_filename, report_text) 
                    VALUES (%s, %s, %s)"""
                cursor.execute(sql, (
                    os.path.basename(processed_path).replace('_processed.png', '_original.png'),
                    os.path.basename(processed_path),
                    report
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

@app.route('/processed/<filename>')
def send_processed_image(filename):
    return send_from_directory(Config.PROCESSED_DIR, filename)

if __name__ == '__main__':
    os.makedirs(Config.ORIGINAL_DIR, exist_ok=True)
    os.makedirs(Config.PROCESSED_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)