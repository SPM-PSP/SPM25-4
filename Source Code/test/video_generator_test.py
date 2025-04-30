import unittest
import os
import shutil
import imageio
from unittest.mock import patch, MagicMock
from io import StringIO

from utils.video_generator import natural_sort_key, combine_frames


class TestVideoGenerator(unittest.TestCase):
    def setUp(self):
        # 创建临时文件夹用于测试
        self.test_folder = 'test_input_folder'
        os.makedirs(self.test_folder, exist_ok=True)
        # 创建一些测试图片
        for i in range(5):
            image = imageio.v3.imread('https://picsum.photos/200/300')
            imageio.v3.imwrite(os.path.join(self.test_folder, f'test_image_{i}.png'), image)

    def tearDown(self):
        # 清理临时文件夹
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
        test_video_path = 'test_output_video.mp4'
        if os.path.exists(test_video_path):
            os.remove(test_video_path)

    def test_natural_sort_key(self):
        # 测试自然排序函数
        test_files = ['file1.png', 'file10.png', 'file2.png']
        sorted_files = sorted(test_files, key=natural_sort_key)
        self.assertEqual(sorted_files, ['file1.png', 'file2.png', 'file10.png'])

    @patch('sys.stdout', new_callable=StringIO)
    def test_combine_frames_no_images(self, mock_stdout):
        # 测试没有有效图片帧的情况
        empty_folder = 'empty_folder'
        os.makedirs(empty_folder, exist_ok=True)
        try:
            combine_frames(empty_folder, 'test_output.mp4')
            output = mock_stdout.getvalue()
            self.assertIn("未找到有效的图片帧。", output)
        finally:
            shutil.rmtree(empty_folder)

    @patch('utils.video_generator.imageio.get_writer')
    def test_combine_frames(self, mock_writer):
        # 测试正常生成视频的情况
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance
        output_video_path = 'test_output_video.mp4'
        combine_frames(self.test_folder, output_video_path)
        mock_writer.assert_called_once()
        self.assertEqual(mock_writer_instance.append_data.call_count, 5)
        mock_writer_instance.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
