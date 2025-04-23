import http.client
import json
import base64
from config import Config

def generate_report(processed_path):
    with open(processed_path, 'rb') as image_file:
        # 读取图片文件内容
        image_data = image_file.read()
        # 转换为Base64编码
        base64_encoded_data = base64.b64encode(image_data)
        # 将bytes类型转换为str类型
        base64_message = base64_encoded_data.decode('utf-8')

    conn = http.client.HTTPSConnection(Config.API_ENDPOINT)
    payload = json.dumps({
        "model": Config.API_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": Config.API_PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_message}"
                        }
                    }
                ]
            }
        ]
    })
    headers = {
        'Authorization': Config.API_KEY,
        'Content-Type': 'application/json'
    }
    conn.request("POST", Config.API_URL, payload, headers)
    res = conn.getresponse()
    data = res.read().decode('utf-8')
    parsed_data = json.loads(data)
    # 异常处理
    try:
        content = parsed_data["choices"][0]["message"]["content"]
        return content
    except (KeyError, IndexError) as e:
        print(f"提取失败：{e}")
        return '报告生成失败'

def generate_followup_response(processed_path, question, previous_messages):
    with open(processed_path, 'rb') as image_file:
        image_data = image_file.read()
        base64_encoded_data = base64.b64encode(image_data)
        base64_message = base64_encoded_data.decode('utf-8')

    new_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": question
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_message}"
                }
            }
        ]
    }
    all_messages = previous_messages + [new_message]

    conn = http.client.HTTPSConnection(Config.API_ENDPOINT)
    payload = json.dumps({
        "model": Config.API_MODEL,
        "messages": all_messages
    })
    headers = {
        'Authorization': Config.API_KEY,
        'Content-Type': 'application/json'
    }
    conn.request("POST", Config.API_URL, payload, headers)
    res = conn.getresponse()
    data = res.read().decode('utf-8')
    parsed_data = json.loads(data)
    try:
        content = parsed_data["choices"][0]["message"]["content"]
        return content
    except (KeyError, IndexError) as e:
        print(f"提取失败：{e}")
        return '后续回复生成失败'    