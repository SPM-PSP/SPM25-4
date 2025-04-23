// DOM元素引用
const fileInput = document.getElementById('fileInput');
const loadingOverlay = document.getElementById('loading-overlay');
const videoPreview = document.getElementById('videoPreview');
const resultSection = document.getElementById('resultSection');
const reportText = document.getElementById('reportText');
const uploadButton = document.querySelector('.upload-btn');
const startDetectButton = document.querySelector('.start-detect-btn');
const uploadProgressBar = document.getElementById('uploadProgressBar');
const uploadProgress = document.getElementById('uploadProgress');
const uploadProgressText = document.getElementById('uploadProgressText');
const processingProgressBar = document.getElementById('processingProgressBar');
const processingProgress = document.getElementById('processingProgress');
const processingProgressText = document.getElementById('processingProgressText');

let videoDuration;
let selectedFile;

// 检查DOM元素是否正确获取
if (!fileInput ||!loadingOverlay ||!videoPreview ||!resultSection ||!reportText ||!uploadButton ||!startDetectButton ||!uploadProgressBar ||!uploadProgress ||!uploadProgressText ||!processingProgressBar ||!processingProgress ||!processingProgressText) {
    console.error('部分DOM元素未正确获取，请检查HTML结构。');
}

// 事件监听器初始化
document.addEventListener('DOMContentLoaded', () => {
    // 文件选择监听
    fileInput.addEventListener('change', handleFileSelect);
    uploadButton.addEventListener('click', handleUploadClick);
    startDetectButton.addEventListener('click', handleStartDetectClick);
});

function handleFileSelect() {
    if (this.files && this.files[0]) {
        selectedFile = this.files[0];
        const url = URL.createObjectURL(selectedFile);
        videoPreview.src = url;
        videoPreview.onloadedmetadata = () => {
            videoDuration = videoPreview.duration;
            if (videoDuration > 300) {
                alert('请选择5分钟以内的视频');
                videoPreview.src = '';
                fileInput.value = '';
                selectedFile = null;
            }
        };
    }
}

function handleUploadClick() {
    if (selectedFile && videoDuration <= 300) {
        const formData = new FormData();
        formData.append('video', selectedFile);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload_video', true);

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                uploadProgress.style.width = percentComplete + '%';
                uploadProgressText.textContent = `上传进度：${Math.round(percentComplete)}%`;
            }
        });

        xhr.onreadystatechange = () => {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        uploadProgressBar.style.display = 'none';
                        processingProgressBar.style.display = 'block';
                        startProcessingProgress(response.total_frames);
                    } else {
                        alert('上传失败: ' + response.error);
                    }
                } else {
                    alert('上传失败: ' + xhr.statusText);
                }
            }
        };

        uploadProgressBar.style.display = 'block';
        uploadProgress.style.width = '0%';
        uploadProgressText.textContent = '上传进度：0%';
        xhr.send(formData);
    } else {
        alert('请先选择一个有效的视频');
    }
}

function startProcessingProgress(totalFrames) {
    let processedFrames = 0;
    const intervalId = setInterval(() => {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '/check_processing_progress', true);
        xhr.onreadystatechange = () => {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    processedFrames = response.processed_frames;
                    const percentComplete = (processedFrames / totalFrames) * 100;
                    processingProgress.style.width = percentComplete + '%';
                    processingProgressText.textContent = `处理进度：${Math.round(percentComplete)}%`;
                    if (processedFrames >= totalFrames) {
                        clearInterval(intervalId);
                        processingProgressBar.style.display = 'none';
                        startDetectButton.disabled = false;
                        resultSection.classList.remove('hidden');
                        reportText.textContent = '视频处理完成，可开始检测。';
                    }
                }
            }
        };
        xhr.send();
    }, 1000);
}

function handleStartDetectClick() {
    // 暂时没有功能，等待后续添加
    alert('开始检测功能暂未实现。');
}

// 加载状态控制
function showLoading() {
    loadingOverlay.style.display = 'block';
    uploadButton.disabled = true;
    startDetectButton.disabled = true;
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
    uploadButton.disabled = false;
    startDetectButton.disabled = false;
}

window.onload = function () {
    document.body.classList.add('loaded');
};