// DOM元素引用
const fileInput = document.getElementById('fileInput');
const loadingOverlay = document.getElementById('loading-overlay');
const originalImage = document.getElementById('originalImage');
const processedImage = document.getElementById('processedImage');
const reportText = document.getElementById('reportText');
const resultSection = document.getElementById('resultSection');

// 事件监听器初始化[1,2](@ref)
document.addEventListener('DOMContentLoaded', () => {
    // 文件选择监听
    fileInput.addEventListener('change', handleFileSelect);

    // 模型选择按钮监听
    document.querySelectorAll('.model-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modelType = e.target.dataset.model;
            uploadFile(modelType);
        });
    });
});

// 处理文件选择（保持原有逻辑）
function handleFileSelect() {
    if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            originalImage.src = e.target.result;
            resultSection.classList.add('hidden');
        }
        reader.readAsDataURL(this.files[0]);
    }
}

// 文件上传主逻辑（改造后）
async function uploadFile(modelType) {
    if (!fileInput.files[0]) {
        alert('请先选择要上传的图片');
        return;
    }

    try {
        showLoading();
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('model_type', modelType);  // 新增模型类型参数[4](@ref)

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error(`服务器错误: ${response.status}`);

        const data = await response.json();
        handleUploadResponse(data, modelType);

    } catch (error) {
        console.error('上传失败:', error);
        alert(`上传失败: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// 处理服务器响应（新增模型类型参数）
function handleUploadResponse(data, modelType) {
    if (data.error) {
        alert(data.error);
        return;
    }

    resultSection.classList.remove('hidden');
    processedImage.src = data.processed_url;

    // 根据模型类型显示不同报告[9](@ref)
    reportText.textContent = `${modelType.toUpperCase()}检测报告：\n${data.report}`;
    reportText.classList.add(`${modelType}-report`);

    // 自动滚动到结果区域
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 新增加载状态控制[4](@ref)
function showLoading() {
    loadingOverlay.style.display = 'block';
    document.querySelectorAll('.model-btn').forEach(btn => btn.disabled = true);
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
    document.querySelectorAll('.model-btn').forEach(btn => btn.disabled = false);
}