import unittest
from unittest.mock import patch, MagicMock
import json
from utils.llm_reporter import generate_report, generate_followup_response

class MockConfig:
    API_ENDPOINT = 'test_api_endpoint'
    API_MODEL = 'test_api_model'
    API_PROMPT = 'test_api_prompt'
    API_KEY = 'test_api_key'
    API_URL = 'test_api_url'


class TestReportGeneration(unittest.TestCase):
    def setUp(self):
        self.processed_path = 'test_image.png'
        self.question = 'test_question'
        self.previous_messages = [{"role": "assistant", "content": "test_previous_content"}]
        self.config_patcher = patch('utils.llm_reporter.Config', new=MockConfig)
        self.config_patcher.start()

    def tearDown(self):
        self.config_patcher.stop()

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test_image_data')
    @patch('http.client.HTTPSConnection')
    def test_generate_report_success(self, mock_conn, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": "test_report_content"
                    }
                }
            ]
        }).encode('utf-8')
        mock_conn_instance = mock_conn.return_value
        mock_conn_instance.getresponse.return_value = mock_response

        result = generate_report(self.processed_path)
        self.assertEqual(result, "test_report_content")
        mock_open.assert_called_once_with(self.processed_path, 'rb')
        mock_conn.assert_called_once_with(MockConfig.API_ENDPOINT)
        mock_conn_instance.request.assert_called_once()
        mock_conn_instance.getresponse.assert_called_once()

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test_image_data')
    @patch('http.client.HTTPSConnection')
    def test_generate_report_failure(self, mock_conn, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({}).encode('utf-8')
        mock_conn_instance = mock_conn.return_value
        mock_conn_instance.getresponse.return_value = mock_response

        result = generate_report(self.processed_path)
        self.assertEqual(result, '报告生成失败')

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test_image_data')
    @patch('http.client.HTTPSConnection')
    def test_generate_followup_response_success(self, mock_conn, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": "test_followup_content"
                    }
                }
            ]
        }).encode('utf-8')
        mock_conn_instance = mock_conn.return_value
        mock_conn_instance.getresponse.return_value = mock_response

        result = generate_followup_response(self.processed_path, self.question, self.previous_messages)
        self.assertEqual(result, "test_followup_content")

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test_image_data')
    @patch('http.client.HTTPSConnection')
    def test_generate_followup_response_failure(self, mock_conn, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({}).encode('utf-8')
        mock_conn_instance = mock_conn.return_value
        mock_conn_instance.getresponse.return_value = mock_response

        result = generate_followup_response(self.processed_path, self.question, self.previous_messages)
        self.assertEqual(result, '后续回复生成失败')


if __name__ == '__main__':
    unittest.main()
