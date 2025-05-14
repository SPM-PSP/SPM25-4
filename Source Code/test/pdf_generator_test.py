import unittest
from unittest.mock import MagicMock, patch, call

from utils.pdf_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.REPORT_DIR = '/reports'
        self.mock_config.ORIGINAL_DIR = '/originals'
        self.mock_config.PROCESSED_DIR = '/processed'

        self.report_generator = ReportGenerator(self.mock_config)
        self.sample_data = {
            "created_at": "2023-01-01 12:00",
            "report_text": "检测到可疑修改",
            "detection_objects": [
                {
                    "class_name": "splicing",
                    "confidence": 0.95,
                    "center_x": 100,
                    "center_y": 200
                }
            ]
        }

    @patch('os.path.exists')
    @patch('PIL.Image.open')
    def test_draw_image_success(self, mock_image_open, mock_exists):
        # 模拟图片存在且正常打开
        mock_exists.return_value = True
        mock_img = MagicMock()
        mock_img.size = (400, 300)  # width, height
        mock_image_open.return_value = mock_img

        mock_canvas = MagicMock()
        y_pos = 500

        new_y = self.report_generator._draw_image(mock_canvas, 'test.jpg', y_pos)

        # 验证计算的高度是否正确 (300/400=0.75, 200 * 0.75=150)
        mock_canvas.drawImage.assert_called_once_with(
            'test.jpg', 50, 500, width=200, height=150
        )
        self.assertEqual(new_y, 500 - 250)  # 检查y轴位置调整

    @patch('os.path.exists')
    def test_draw_image_not_exist(self, mock_exists):
        mock_exists.return_value = False
        mock_canvas = MagicMock()
        y_pos = 500

        new_y = self.report_generator._draw_image(mock_canvas, 'missing.jpg', y_pos)

        mock_canvas.drawImage.assert_not_called()
        self.assertEqual(new_y, 500)

    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('PIL.Image.open')
    def test_draw_image_exception(self, mock_image_open, mock_exists, mock_print):
        mock_exists.return_value = True
        mock_image_open.side_effect = Exception("Invalid image")