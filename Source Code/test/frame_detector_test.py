import unittest
import os
from utils.frame_detector import process_frames
from config import Config

class TestProcessFrames(unittest.TestCase):
    def setUp(self):
        # 设置测试文件夹路径
        self.test_dir = os.path.join(os.path.dirname(__file__), "data")  # 假设图片在 tests/data 文件夹中
        self.input_folder = os.path.join(self.test_dir, "input")
        self.output_folder = os.path.join(self.test_dir, "output")

        # 确保输入文件夹存在
        self.assertTrue(os.path.exists(self.input_folder), f"输入文件夹 {self.input_folder} 不存在")

        # 清理输出文件夹
        if os.path.exists(self.output_folder):
            for filename in os.listdir(self.output_folder):
                os.remove(os.path.join(self.output_folder, filename))
        else:
            os.makedirs(self.output_folder)

    def test_process_frames_with_real_images(self):
        # 确保输入文件夹中有测试图片
        input_files = [f for f in os.listdir(self.input_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
        self.assertTrue(len(input_files) > 0, "输入文件夹中没有测试图片")

        # 调用函数
        process_frames(self.input_folder, self.output_folder)

        # 验证输出文件夹中是否生成了处理后的图片
        output_files = os.listdir(self.output_folder)
        self.assertEqual(len(input_files), len(output_files), "处理后的图片数量不匹配")

        # 验证每个输出文件是否正确生成
        for filename in input_files:
            output_path = os.path.join(self.output_folder, filename)
            self.assertTrue(os.path.exists(output_path), f"处理后的图片 {output_path} 未生成")


if __name__ == "__main__":
    unittest.main()