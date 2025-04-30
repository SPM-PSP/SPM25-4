import unittest
import os
import json
import io
from unittest.mock import patch, MagicMock, mock_open
from app import app
from config import Config


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        # 配置测试环境
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        # 创建必要的目录结构
        os.makedirs(Config.ORIGINAL_DIR, exist_ok=True)
        os.makedirs(Config.PROCESSED_DIR, exist_ok=True)
        os.makedirs(os.path.join(Config.VIDEOS_UPLOADS_DIR, 'original'), exist_ok=True)
        os.makedirs(os.path.join(Config.VIDEOS_UPLOADS_DIR, 'frame'), exist_ok=True)
        os.makedirs(Config.REPORT_DIR, exist_ok=True)


    def tearDown(self):
        # 清理测试环境，删除测试中创建的文件
        pass


    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)


    def test_image_detect_route(self):
        response = self.app.get('/image_detect')
        self.assertEqual(response.status_code, 200)


    def test_video_detect_route(self):
        response = self.app.get('/video_detect')
        self.assertEqual(response.status_code, 200)


    @patch('app.detect_tampering')
    @patch('app.insert_detection_result')
    @patch('uuid.uuid4')
    def test_yolo_detect_valid_image(self, mock_uuid, mock_insert, mock_detect):
        # 模拟UUID生成
        mock_uuid.return_value = "test-uuid-123"

        # 模拟检测函数返回值
        mock_detect.return_value = {
            "objects": [{"type": "face", "confidence": 0.95}]
        }

        # 创建测试文件
        test_image = (io.BytesIO(b"test image content"), 'test_image.jpg')

        response = self.app.post(
            '/yolo_detect',
            data={
                'file': test_image,
                'model_type': 'ps'
            },
            content_type='multipart/form-data'
        )

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('processed_url', data)
        self.assertIn('processed_path', data)
        self.assertEqual(data['model_type'], 'ps')

        # 验证函数调用
        mock_detect.assert_called_once()
        mock_insert.assert_called_once()


    def test_yolo_detect_no_file(self):
        response = self.app.post('/yolo_detect', data={'model_type': 'ps'})
        self.assertEqual(response.status_code, 400)


    def test_yolo_detect_invalid_model_type(self):
        test_image = (io.BytesIO(b"test image content"), 'test_image.jpg')
        response = self.app.post(
            '/yolo_detect',
            data={
                'file': test_image,
                'model_type': 'invalid_model'
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)


    @patch('app.generate_report')
    @patch('app.insert_image_record')
    def test_generate_report_route(self, mock_insert, mock_generate_report):
        # 模拟报告生成
        mock_generate_report.return_value = "This is a test report"

        response = self.app.post(
            '/generate_report',
            data=json.dumps({
                'processed_path': '/path/to/test_uuid-123_processed.png',
                'model_type': 'ps'
            }),
            content_type='application/json'
        )

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['report'], "This is a test report")
        self.assertEqual(data['model_type'], 'ps')

        # 验证函数调用
        mock_generate_report.assert_called_once()
        mock_insert.assert_called_once()


    @patch('app.generate_followup_response')
    def test_generate_followup(self, mock_generate_response):
        # 模拟回复生成
        mock_generate_response.return_value = "This is a test follow-up response"

        response = self.app.post(
            '/generate_followup',
            data=json.dumps({
                'processed_path': '/path/to/test.png',
                'question': 'Are there any signs of manipulation?',
                'previous_messages': []
            }),
            content_type='application/json'
        )

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['response'], "This is a test follow-up response")
        mock_generate_response.assert_called_once()


    @patch('app.send_from_directory')
    def test_send_processed_image(self, mock_send):
        mock_send.return_value = "image data"
        response = self.app.get('/processed/test_image.png')
        mock_send.assert_called_with(Config.PROCESSED_DIR, 'test_image.png')


    @patch('cv2.VideoCapture')
    @patch('subprocess.run')
    @patch('threading.Thread')
    @patch('uuid.uuid4')
    def test_upload_video(self, mock_uuid, mock_thread, mock_subprocess, mock_cv2):
        # 模拟UUID生成
        mock_uuid.return_value = "test-video-uuid-123"

        # 模拟视频帧计数
        mock_video = MagicMock()
        mock_video.get.return_value = 100
        mock_cv2.return_value = mock_video

        # 模拟线程启动
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # 创建测试视频文件
        test_video = (io.BytesIO(b"test video content"), 'test_video.mp4')

        response = self.app.post(
            '/upload_video',
            data={'video': test_video},
            content_type='multipart/form-data'
        )

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['total_frames'], 100)
        self.assertEqual(data['file_id'], 'test-video-uuid-123')

        # 验证线程启动
        mock_thread_instance.start.assert_called_once()


    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('app.insert_video_record')
    def test_start_detection(self, mock_insert, mock_makedirs, mock_subprocess):
        response = self.app.post(
            '/start_detection',
            data=json.dumps({
                'file_id': 'test-file-id',
                'original_ext': 'mp4'
            }),
            content_type='application/json'
        )

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('processed_video_url', data)
        mock_insert.assert_called_once()
        self.assertEqual(mock_subprocess.call_count, 2)  # 应该调用了两次subprocess.run


    @patch('builtins.open', new_callable=mock_open, read_data='50')
    def test_check_processing_progress(self, mock_file):
        response = self.app.get('/check_processing_progress')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['processed_frames'], 50)


    @patch('app.send_from_directory')
    def test_serve_processed_video(self, mock_send):
        mock_send.return_value = "video data"
        response = self.app.get('/processed_video/test_video.mp4')
        mock_send.assert_called_once()


    @patch('app.get_detection_result_id')
    @patch('app.get_detected_objects')
    def test_get_detection_info(self, mock_get_objects, mock_get_result_id):
        # 模拟数据库查询结果
        mock_get_result_id.return_value = 123
        mock_get_objects.return_value = [{"type": "face", "confidence": 0.95}]

        response = self.app.post(
            '/get_detection_info',
            data=json.dumps({
                'processed_filename': 'test_processed.png'
            }),
            content_type='application/json'
        )

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('detection_info', data)
        mock_get_result_id.assert_called_with('test_processed.png')
        mock_get_objects.assert_called_with(123)


    @patch('app.get_image_report')
    @patch('app.get_full_detection_data')
    @patch('app.ReportGenerator')
    @patch('app.send_file')
    def test_export_report(self, mock_send_file, mock_report_gen, mock_get_data, mock_get_report):
        # 模拟报告数据
        mock_get_report.return_value = {"title": "Test Report", "created_at": "2023-01-01"}
        mock_get_data.return_value = [{"type": "face", "confidence": 0.95}]

        # 模拟PDF生成
        mock_generator = MagicMock()
        mock_generator.generate_pdf.return_value = "/path/to/report.pdf"
        mock_report_gen.return_value = mock_generator

        # 模拟文件发送
        mock_send_file.return_value = "PDF file"

        response = self.app.post(
            '/export_report',
            data=json.dumps({
                'processed_filename': 'test\\processed.png'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        mock_get_report.assert_called_once()
        mock_get_data.assert_called_once()
        mock_generator.generate_pdf.assert_called_once()
        mock_send_file.assert_called_with('/path/to/report.pdf', as_attachment=True)


if __name__ == 'main':
    unittest.main()