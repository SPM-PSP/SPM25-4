// image_script.js
// DOM元素引用
const fileInput = document.getElementById('fileInput');
const loadingOverlay = document.getElementById('loading-overlay');
const originalImage = document.getElementById('originalImage');
const processedImage = document.getElementById('processedImage');
const reportText = document.getElementById('reportText');
const resultSection = document.getElementById('resultSection');

let cropper;

// 事件监听器初始化
document.addEventListener('DOMContentLoaded', () => {
    // 文件选择监听
    fileInput.addEventListener('change', handleFileSelect);

    // 模型选择按钮监听
    document.querySelectorAll('.model-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modelType = e.target.dataset.model;
            if (cropper) {
                const croppedCanvas = cropper.getCroppedCanvas();
                const croppedBlob = new Promise((resolve) => {
                    croppedCanvas.toBlob((blob) => {
                        resolve(blob);
                    }, 'image/jpeg');
                });
                croppedBlob.then((blob) => {
                    const formData = new FormData();
                    formData.append('file', blob, 'cropped_image.jpg');
                    formData.append('model_type', modelType);
                    uploadFile(formData, modelType);
                });
            } else {
                alert('请先选择并裁剪图片');
            }
        });
    });
});

// 处理文件选择
function handleFileSelect() {
    if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            originalImage.src = e.target.result;
            resultSection.classList.add('hidden');
            if (cropper) {
                cropper.destroy();
            }
            // 移除固定的裁剪比例，允许自由调整
            cropper = new Cropper(originalImage, {
                aspectRatio: NaN,
                viewMode: 1,
                zoomOnWheel: true
            });
        };
        reader.readAsDataURL(this.files[0]);
    }
}

// 文件上传主逻辑
async function uploadFile(formData, modelType) {
    try {
        showLoading();

        // 第一步：进行YOLO分割模型检测
        const yoloResponse = await fetch('/yolo_detect', {
            method: 'POST',
            body: formData
        });

        if (!yoloResponse.ok) throw new Error(`服务器错误: ${yoloResponse.status}`);

        const yoloData = await yoloResponse.json();
        handleYoloResponse(yoloData, modelType);

        // 第二步：进行AI API调用
        const reportResponse = await fetch('/generate_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                processed_path: yoloData.processed_path,
                model_type: modelType
            })
        });

        if (!reportResponse.ok) throw new Error(`服务器错误: ${reportResponse.status}`);

        const reportData = await reportResponse.json();
        handleReportResponse(reportData, modelType);

    } catch (error) {
        console.error('上传失败:', error);
        alert(`上传失败: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// 处理YOLO分割模型检测结果
function handleYoloResponse(data, modelType) {
    if (data.error) {
        alert(data.error);
        return;
    }

    resultSection.classList.remove('hidden');
    processedImage.src = data.processed_url;
    reportText.textContent = `${modelType.toUpperCase()}检测结果已生成，正在调用AI进行分析...`;
    reportText.classList.add(`${modelType}-report`);
    resultSection.scrollIntoView({ behavior: 'smooth' });
    hideLoading();
}

// 处理AI API调用结果
function handleReportResponse(data, modelType) {
    if (data.error) {
        alert(data.error);
        return;
    }

    reportText.textContent = `${modelType.toUpperCase()}检测报告：\n${data.report}`;
}

// 新增加载状态控制
function showLoading() {
    loadingOverlay.style.display = 'block';
    document.querySelectorAll('.model-btn').forEach(btn => btn.disabled = true);
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
    document.querySelectorAll('.model-btn').forEach(btn => btn.disabled = false);
}

window.onload = function () {
    document.body.classList.add('loaded');
};