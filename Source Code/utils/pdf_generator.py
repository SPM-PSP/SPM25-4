from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from PIL import Image
import os

class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.style = getSampleStyleSheet()['Normal']
        self.style.fontName = 'SimHei'
        self.style.fontSize = 12

    def _draw_image(self, c, path, y_pos):
        """通用图片绘制方法"""
        if not os.path.exists(path):
            return y_pos

        try:
            img = Image.open(path)
            img_width, img_height = img.size
            aspect = img_height / img_width
            c.drawImage(path, 50, y_pos, width=200, height=200 * aspect)
            return y_pos - 250  # 调整下一个元素的位置
        except Exception as e:
            print(f"Image drawing error: {str(e)}")
            return y_pos

    def generate_pdf(self, processed_filename, report_data):
        """生成PDF报告"""
        pdf_path = os.path.join(
            self.config.REPORT_DIR,
            f"{processed_filename.replace('.png', '')}_report.pdf"
        )

        c = canvas.Canvas(pdf_path, pagesize=letter)

        # 标题和基础信息
        c.setFont('SimHei', 20)
        c.drawString(50, 750, '图像篡改检测报告')
        c.setFont('SimHei', 12)
        c.drawString(50, 720, f'检测完成时间: {report_data["created_at"]}')

        # 添加原始图片
        original_path = os.path.join(
            self.config.ORIGINAL_DIR,
            processed_filename.replace('_processed.png', '_original.jpg')
        )
        current_y = self._draw_image(c, original_path, 500)

        # 添加处理后图片
        processed_path = os.path.join(
            self.config.PROCESSED_DIR,
            processed_filename
        )
        self._draw_image(c, processed_path, current_y)

        # LLM报告内容
        report_para = Paragraph(report_data["report_text"], self.style)
        report_para.wrapOn(c, 500, 700)
        report_para.drawOn(c, 50, 670)

        # 检测信息分页
        c.showPage()
        c.setFont('SimHei', 12)
        c.drawString(50, 760, '目标检测信息')
        info_text = '<br/>'.join(
            [f'类别: {o["class_name"]}, 置信度: {o["confidence"]:.2f}, 坐标: ({o["center_x"]}, {o["center_y"]})'
             for o in report_data["detection_objects"]]
        )
        info_para = Paragraph(info_text, self.style)
        info_para.wrapOn(c, 500, 700)
        info_para.drawOn(c, 50, 720)

        c.save()
        return pdf_path