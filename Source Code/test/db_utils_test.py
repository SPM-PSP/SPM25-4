import unittest
from unittest.mock import patch, MagicMock
from utils.db_utils import (
    create_connection,
    init_db,
    insert_detection_result,
    insert_image_record,
    get_detection_result_id,
    get_detected_objects,
    get_image_report,
    get_full_detection_data,
    insert_video_record
)
from config import Config

class TestDatabaseOperations(unittest.TestCase):
    @patch("pymysql.connect")
    def test_create_connection(self, mock_connect):
        # 模拟数据库连接
        mock_connect.return_value = MagicMock()
        conn = create_connection()
        self.assertIsNotNone(conn)

    @patch("pymysql.connect")
    def test_init_db(self, mock_connect):
        # 模拟数据库连接
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.return_value = None

        # 调用 init_db
        init_db()

        # 验证是否调用了正确的 SQL 语句
        self.assertEqual(mock_cursor.execute.call_count, 2)


    @patch("pymysql.connect")
    def test_insert_image_record(self, mock_connect):
        # 模拟数据库连接
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.return_value = None

        # 调用 insert_image_record
        insert_image_record(
            original_filename="original.jpg",
            processed_filename="processed.jpg",
            report_text="Test report",
            created_at="2023-10-01 12:00:00"
        )

        # 验证是否调用了正确的 SQL 语句
        mock_cursor.execute.assert_called_once()

    @patch("pymysql.connect")
    def test_get_detection_result_id(self, mock_connect):
        # 模拟数据库连接
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {"id": 1}

        # 调用 get_detection_result_id
        result_id = get_detection_result_id(processed_filename="test_image.jpg")

        # 验证结果
        self.assertEqual(result_id, 1)

    @patch("pymysql.connect")
    def test_get_detected_objects(self, mock_connect):
        # 模拟数据库连接
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            {"class_name": "tampered", "confidence": 0.95, "center_x": 50, "center_y": 50}
        ]

        # 调用 get_detected_objects
        objects = get_detected_objects(detection_result_id=1)

        # 验证结果
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0]["class_name"], "tampered")

    @patch("pymysql.connect")
    def test_get_image_report(self, mock_connect):
        # 模拟数据库连接
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {
            "report_text": "Test report",
            "created_at": "2023-10-01 12:00:00"
        }

        # 调用 get_image_report
        report = get_image_report(processed_filename="test_image.jpg")

        # 验证结果
        self.assertEqual(report["report_text"], "Test report")
        self.assertEqual(report["created_at"], "2023-10-01 12:00:00")

    @patch("pymysql.connect")
    def test_get_full_detection_data(self, mock_connect):
        # 模拟数据库连接
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {"id": 1}
        mock_cursor.fetchall.return_value = [
            {"class_name": "tampered", "confidence": 0.95, "center_x": 50, "center_y": 50}
        ]

        # 调用 get_full_detection_data
        data = get_full_detection_data(processed_filename="test_image.jpg")

        # 验证结果
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["class_name"], "tampered")

    @patch("pymysql.connect")
    def test_insert_video_record(self, mock_connect):
        # 模拟数据库连接
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.return_value = None

        # 调用 insert_video_record
        insert_video_record(
            original_filename="original_video.mp4",
            frame_folder_name="frames_folder"
        )

        # 验证是否调用了正确的 SQL 语句
        mock_cursor.execute.assert_called_once()

if __name__ == "__main__":
    unittest.main()