import cv2
import os
import sys
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



if __name__ == "__main__":
    video_path = sys.argv[1]
    file_id = sys.argv[2]
    output_folder = os.path.join(Config.VIDEOS_UPLOADS_DIR, 'frame', file_id)
    extract_frames(video_path, output_folder)
