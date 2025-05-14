import unittest
from utils.image_detector import detect_tampering  # 替换为你的模块名
import os

class TestDetectTampering(unittest.TestCase):
    def setUp(self):
        # 设置测试图片路径
        self.test_dir = os.path.join(os.path.dirname(__file__), "data")  # 假设图片在 tests/data 文件夹中
        self.ps_image_path = os.path.join(self.test_dir, "test_ps.png")
        self.faceapp_image_path = os.path.join(self.test_dir, "test_faceapp.png")
        self.processed_path = os.path.join(self.test_dir, "test_processed.jpg")

        # 确保测试图片存在
        self.assertTrue(os.path.exists(self.ps_image_path), f"测试图片 {self.ps_image_path} 不存在")
        self.assertTrue(os.path.exists(self.faceapp_image_path), f"测试图片 {self.faceapp_image_path} 不存在")

    def test_detect_tampering_with_ps_image(self):
        # 测试 PS 图片
        report_data = detect_tampering(self.ps_image_path, self.processed_path, model_type="ps")

        # 验证结果
        self.assertIn("num_objects", report_data)
        self.assertIn("objects", report_data)
        self.assertIsInstance(report_data["num_objects"], int)
        self.assertIsInstance(report_data["objects"], list)

        # 验证是否生成了处理后的图片
        self.assertTrue(os.path.exists(self.processed_path), "处理后的图片未生成")

    def test_detect_tampering_with_faceapp_image(self):
        # 测试 FaceApp 图片
        report_data = detect_tampering(self.faceapp_image_path, self.processed_path, model_type="faceapp")

        # 验证结果
        self.assertIn("num_objects", report_data)
        self.assertIn("objects", report_data)
        self.assertIsInstance(report_data["num_objects"], int)
        self.assertIsInstance(report_data["objects"], list)

        # 验证是否生成了处理后的图片
        self.assertTrue(os.path.exists(self.processed_path), "处理后的图片未生成")

if __name__ == "__main__":
    unittest.main()