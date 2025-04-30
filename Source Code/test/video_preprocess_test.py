import unittest
import os
import cv2
from unittest.mock import patch, MagicMock
from config import Config


def extract_frames(video_path, output_folder, fps=15):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = cap.get(cv2.CAP_PROP_FPS) / fps

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            if frame_count % frame_interval < 1:
                frame_filename = os.path.join(output_folder, f'frame_{int(frame_count / frame_interval)}.jpg')
                cv2.imwrite(frame_filename, frame)
            frame_count += 1
            # 保存处理进度
            with open(Config.PROGRESS_TXT_PATH, 'w') as f:
                f.write(str(frame_count))
        else:
            break
    cap.release()


class TestExtractFrames(unittest.TestCase):

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('cv2.imwrite')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_extract_frames(self, mock_open, mock_imwrite, mock_makedirs, mock_exists, mock_video_capture):
        video_path = 'test_video.mp4'
        output_folder = 'test_output'
        fps = 15

        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [100, 30]  # 模拟总帧数和帧率
        mock_cap.read.side_effect = [(True, MagicMock())] * 100 + [(False, None)]  # 模拟读取帧
        mock_exists.return_value = False

        extract_frames(video_path, output_folder, fps)

        mock_video_capture.assert_called_once_with(video_path)
        mock_exists.assert_called_once_with(output_folder)
        mock_makedirs.assert_called_once_with(output_folder)
        mock_cap.release.assert_called_once()


if __name__ == '__main__':
    unittest.main()
