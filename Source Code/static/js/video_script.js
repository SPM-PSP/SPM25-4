// DOM元素引用
const fileInput = document.getElementById('fileInput');
const loadingOverlay = document.getElementById('loading-overlay');
const originalVideo = document.getElementById('originalVideo');
const processedVideo = document.getElementById('processedVideo');
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
let fileId;

// 检查DOM元素是否正确获取
if (!fileInput ||!loadingOverlay ||!originalVideo ||!processedVideo ||!resultSection ||!reportText ||!uploadButton ||!startDetectButton ||!uploadProgressBar ||!uploadProgress ||!uploadProgressText ||!processingProgressBar ||!processingProgress ||!processingProgressText) {
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
        originalVideo.src = url;
        originalVideo.onloadedmetadata = () => {
            videoDuration = originalVideo.duration;
            if (videoDuration > 300) {
                alert('请选择5分钟以内的视频');
                originalVideo.src = '';
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
                        fileId = response.file_id; // 从响应中获取 file_id
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
    if (fileId) {
        const data = {
            file_id: fileId,
            original_ext: selectedFile.name.split('.').pop().toLowerCase()
        };
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/start_detection', true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onreadystatechange = () => {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        alert('检测和视频生成完成');
                        hideLoading(); // 隐藏加载状态
                        reportText.textContent = '检测和视频生成完成';
                        // 设置处理后视频的URL
                        processedVideo.src = response.processed_video_url;
                    } else {
                        alert('检测和视频生成失败: ' + response.error);
                        hideLoading(); // 隐藏加载状态
                    }
                } else {
                    alert('检测和视频生成失败: ' + xhr.statusText);
                    hideLoading(); // 隐藏加载状态
                }
            }
        };

        showLoading();
        xhr.send(JSON.stringify(data));
    } else {
        alert('文件ID未获取到，请重新上传视频');
    }
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
