// DOM元素引用
const fileInput = document.getElementById('fileInput');
const loadingOverlay = document.getElementById('loading-overlay');
const originalImage = document.getElementById('originalImage');
const processedImage = document.getElementById('processedImage');
const reportText = document.getElementById('reportText');
const resultSection = document.getElementById('resultSection');
const questionInput = document.getElementById('questionInput');
const sendQuestion = document.getElementById('sendQuestion');
const chatMessages = document.getElementById('chatMessages');
const loadingInChat = document.createElement('div');
loadingInChat.className = 'loading-in-chat';
// 修改提示信息
loadingInChat.innerHTML = '<div class="spinner"></div><p>等待AI助手响应...</p>';
chatMessages.parentNode.insertBefore(loadingInChat, chatMessages.nextSibling);

let cropper;
let processedPath;
let previousMessages = [];
let reportGenerated = false; // 新增：记录报告是否生成完成

// 检查DOM元素是否正确获取
if (!fileInput || !loadingOverlay || !originalImage || !processedImage || !reportText || !resultSection || !questionInput || !sendQuestion || !chatMessages) {
    console.error('部分DOM元素未正确获取，请检查HTML结构。');
}

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
                    // 首次上传图片分析时显示等待提示
                    showLoadingInChat();
                    reportGenerated = false; // 每次上传图片时重置报告生成状态
                    uploadFile(formData, modelType);
                });
            } else {
                alert('请先选择并裁剪图片');
            }
        });
    });

    // 发送问题按钮监听
    sendQuestion.addEventListener('click', async () => {
        const question = questionInput.value;
        if (question) {
            if (!processedPath) {
                const noImageMessage = document.createElement('p');
                noImageMessage.textContent = '对不起，您没有上传图片哦，我暂时不能回答您的问题，请上传一张需要我检测的图片';
                noImageMessage.classList.add('ai-message');
                chatMessages.appendChild(noImageMessage);
                return;
            }
            await sendQuestionToLLM(question);
        }
    });

    // 监听回车事件
    questionInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const question = questionInput.value;
            if (question) {
                if (!processedPath) {
                    const noImageMessage = document.createElement('p');
                    noImageMessage.textContent = '对不起，您没有上传图片哦，我暂时不能回答您的问题，请上传一张需要我检测的图片';
                    noImageMessage.classList.add('ai-message');
                    chatMessages.appendChild(noImageMessage);
                    return;
                }
                await sendQuestionToLLM(question);
            }
        }
    });

    // 导出报告按钮监听
    const exportReportBtn = document.getElementById('exportReportBtn');
    exportReportBtn.addEventListener('click', async () => {
        if (!processedPath) {
            alert('请先上传并处理图片');
            return;
        }
        if (!reportGenerated) {
            alert('AI报告正在生成中，请稍后再导出');
            return;
        }

        // 获取处理后的文件名
        const processedFilename = processedPath.split('/').pop();

        try {
            const response = await fetch('/export_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    processed_filename: processedFilename
                })
            });

            if (!response.ok) throw new Error(`服务器错误: ${response.status}`);

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${processedFilename.replace('.png', '.pdf')}`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('导出报告失败:', error);
            alert(`导出报告失败: ${error.message}`);
        }
    });
});

async function sendQuestionToLLM(question) {
    showLoadingInChat();
    const data = {
        processed_path: processedPath,
        question: question,
        previous_messages: previousMessages
    };
    try {
        const response = await fetch('/generate_followup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`服务器错误: ${response.status}`);
        const responseData = await response.json();
        if (responseData.error) {
            alert(responseData.error);
        } else {
            const userMessage = document.createElement('p');
            userMessage.textContent = question;
            userMessage.classList.add('user-message');
            chatMessages.appendChild(userMessage);
            const aiMessage = document.createElement('p');
            aiMessage.textContent = responseData.response;
            aiMessage.classList.add('ai-message');
            chatMessages.appendChild(aiMessage);
            previousMessages.push({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            });
            previousMessages.push({
                "role": "assistant",
                "content": responseData.response
            });
        }
    } catch (error) {
        console.error('提问失败:', error);
        alert(`提问失败: ${error.message}`);
    } finally {
        hideLoadingInChat();
        questionInput.value = '';
    }
}

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
            // 允许自由调整裁剪比例
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
        processedPath = yoloData.processed_path;

        // 第二步：进行AI API调用
        const reportResponse = await fetch('/generate_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                processed_path: processedPath,
                model_type: modelType
            })
        });

        if (!reportResponse.ok) throw new Error(`服务器错误: ${reportResponse.status}`);

        const reportData = await reportResponse.json();
        handleReportResponse(reportData, modelType);
        previousMessages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": reportData.report
                    }
                ]
            },
            {
                "role": "assistant",
                "content": reportData.report
            }
        ];
        const initialMessage = document.createElement('p');
        initialMessage.textContent = reportData.report;
        initialMessage.classList.add('ai-message');
        chatMessages.appendChild(initialMessage);
        reportGenerated = true; // 报告生成完成，更新标志

    } catch (error) {
        console.error('上传失败:', error);
        alert(`上传失败: ${error.message}`);
    } finally {
        hideLoading();
        // 首次上传图片分析完成后隐藏等待提示
        hideLoadingInChat();
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
    if (reportText) {
        reportText.textContent = `${modelType.toUpperCase()}检测结果已生成，正在调用AI进行分析...`;
        reportText.classList.add(`${modelType}-report`);
    }
    resultSection.scrollIntoView({ behavior: 'smooth' });
    hideLoading();
}

// 处理AI API调用结果
function handleReportResponse(data, modelType) {
    if (data.error) {
        alert(data.error);
        return;
    }
    if (reportText) {
        reportText.textContent = `${modelType.toUpperCase()}检测报告：\n${data.report}`;
    }
}

// 加载状态控制
function showLoading() {
    loadingOverlay.style.display = 'block';
    document.querySelectorAll('.model-btn').forEach(btn => btn.disabled = true);
    sendQuestion.disabled = true;
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
    document.querySelectorAll('.model-btn').forEach(btn => btn.disabled = false);
    sendQuestion.disabled = false;
}

function showLoadingInChat() {
    loadingInChat.style.display = 'block';
    sendQuestion.disabled = true;
}

function hideLoadingInChat() {
    loadingInChat.style.display = 'none';
    sendQuestion.disabled = false;
}

window.onload = function () {
    document.body.classList.add('loaded');
};