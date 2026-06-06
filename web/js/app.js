// ============================================================================
// 智慧交通前端应用 - JavaScript 逻辑
// ============================================================================
// 功能说明：
// 1. 摄像头控制（启动、停止、视频流处理）
// 2. 抓拍分析（调用 Go 后端 API 进行综合分析）
// 3. 数据展示（排队长度、紧急车辆、天气、信号灯状态）
// 4. 历史记录管理（抓拍记录存储与展示）
//
// 作者：AI Assistant
// 创建时间：2026-06-06
// ============================================================================

// ==================== 全局变量定义 ====================
// 视频流对象
let videoStream = null;
// 定时分析任务 ID
let analysisInterval = null;
// 抓拍记录数组
let snapshots = [];
// API 基础地址（Go 后端服务）
const API_BASE_URL = 'http://localhost:8080/api';

// 模拟历史车流数据（用于 LSTM 预测）
let historicalTraffic = [45, 48, 52, 49, 55, 58, 53, 50, 47, 52, 56, 54];

// ==================== 初始化 ====================
// 页面加载完成后执行初始化
document.addEventListener('DOMContentLoaded', function() {
    // 更新时间显示
    updateTime();
    // 每秒更新一次时间
    setInterval(updateTime, 1000);
    // 加载天气信息
    loadWeather();
    // 每 5 分钟更新一次天气
    setInterval(loadWeather, 300000);
});

// ==================== 时间显示 ====================
/**
 * 更新时间显示
 * 格式：YYYY-MM-DD HH:MM:SS
 */
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleString('zh-CN');
}

// ==================== 摄像头控制 ====================
/**
 * 启动摄像头
 * 使用浏览器 MediaDevices API 获取摄像头权限
 */
async function startCamera() {
    try {
        const video = document.getElementById('videoElement');
        const loading = document.getElementById('videoLoading');
        
        // 显示加载提示
        loading.style.display = 'flex';
        
        // 请求摄像头权限（1280x720 分辨率）
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        });
        
        // 将视频流绑定到 video 元素
        video.srcObject = videoStream;
        loading.style.display = 'none';
        
        // 更新摄像头状态为在线
        document.getElementById('cameraStatus').className = 'status-indicator status-online';
        document.getElementById('cameraStatusText').textContent = '摄像头在线';
        
    } catch (error) {
        console.error('摄像头启动失败:', error);
        alert('摄像头启动失败，请检查权限设置');
        document.getElementById('videoLoading').style.display = 'none';
    }
}

/**
 * 停止摄像头
 * 关闭视频流并清理相关资源
 */
function stopCamera() {
    if (videoStream) {
        // 停止所有视频轨道
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
        document.getElementById('videoElement').srcObject = null;
        
        // 更新摄像头状态为离线
        document.getElementById('cameraStatus').className = 'status-indicator status-offline';
        document.getElementById('cameraStatusText').textContent = '摄像头离线';
        
        // 停止定时分析任务
        if (analysisInterval) {
            clearInterval(analysisInterval);
            analysisInterval = null;
        }
    }
}

// ==================== 抓拍分析 ====================
/**
 * 抓拍并分析当前帧
 * 1. 从视频流截取当前帧
 * 2. 添加到抓拍记录
 * 3. 调用后端 API 进行综合分析
 */
async function captureSnapshot() {
    const video = document.getElementById('videoElement');
    if (!video.srcObject) {
        alert('请先启动摄像头');
        return;
    }

    // 创建 canvas 进行截图
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    // 获取图片数据（Base64 格式）
    const imageData = canvas.toDataURL('image/jpeg');
    
    // 添加到抓拍记录
    addSnapshot(imageData);
    
    // 进行综合分析
    await performAnalysis(canvas);
}

/**
 * 添加抓拍记录到相册
 * @param {string} imageData - Base64 编码的图片数据
 */
function addSnapshot(imageData) {
    const gallery = document.getElementById('snapshotGallery');
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN');
    
    // 创建抓拍记录项
    const snapshotItem = document.createElement('div');
    snapshotItem.className = 'snapshot-item';
    snapshotItem.innerHTML = `
        <img src="${imageData}" alt="抓拍记录">
        <div class="snapshot-time">${timeStr}</div>
    `;
    
    // 添加到相册开头
    gallery.insertBefore(snapshotItem, gallery.firstChild);
    
    // 记录到数组
    snapshots.push({
        time: now,
        imageData: imageData
    });
    
    // 限制记录数量（最多 20 条）
    if (snapshots.length > 20) {
        snapshots.shift();
        // 移除最后一个元素
        if (gallery.children.length > 20) {
            gallery.removeChild(gallery.lastChild);
        }
    }
}

// ==================== 综合分析 ====================
/**
 * 执行综合分析
 * 调用 Go 后端 API 进行：
 * 1. 排队长度分析
 * 2. 紧急车辆检测
 * 3. 车流量预测
 * 4. 信号灯优化
 * 
 * @param {HTMLCanvasElement} canvas - 包含图片数据的 canvas
 */
async function performAnalysis(canvas) {
    try {
        // 获取图片数据（Base64）
        const imageData = canvas.toDataURL('image/jpeg').split(',')[1];
        
        // 获取当前天气信息（用于信号灯优化）
        const weatherElement = document.getElementById('weather');
        const temperatureElement = document.getElementById('temperature');
        const currentWeather = weatherElement ? weatherElement.textContent : '晴';
        const currentTemperature = temperatureElement ? temperatureElement.textContent : '25°C';
        
        // 构建请求数据
        const requestData = {
            image: imageData,
            historical_traffic: historicalTraffic,
            lane_start: [100, 500],  // 车道起始点坐标
            lane_end: [500, 500],     // 车道结束点坐标
            weather: currentWeather    // 天气信息（影响通行时间）
        };
        
        // 调用后端 API
        const response = await fetch(`${API_BASE_URL}/comprehensive_analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error('API 请求失败');
        }
        
        const result = await response.json();
        
        if (result.success) {
            // 更新 UI 显示分析结果
            updateAnalysisResults(result.analysis);
            
            // 更新历史车流数据（用于下次预测）
            historicalTraffic.push(result.analysis.traffic_prediction.predicted_flow);
            if (historicalTraffic.length > 12) {
                historicalTraffic.shift();
            }
        }
        
    } catch (error) {
        console.error('分析失败:', error);
        alert('分析失败，请稍后重试');
    }
}

/**
 * 更新分析结果显示
 * @param {Object} analysis - 分析结果数据
 */
function updateAnalysisResults(analysis) {
    // 更新排队长度
    document.getElementById('queueLength').textContent = 
        analysis.queue_analysis.length.toFixed(1) + ' 米';
    document.getElementById('vehicleCount').textContent = 
        analysis.queue_analysis.vehicle_count + ' 辆';
    
    // 更新紧急车辆检测
    const emergencyDiv = document.getElementById('emergencyStatus');
    if (analysis.emergency_detection.detected) {
        emergencyDiv.textContent = '⚠️ ' + analysis.emergency_detection.types.join(', ');
        emergencyDiv.style.color = '#ff4444';
        emergencyDiv.style.fontWeight = 'bold';
    } else {
        emergencyDiv.textContent = '无紧急车辆';
        emergencyDiv.style.color = '#333';
        emergencyDiv.style.fontWeight = 'normal';
    }
    
    // 更新信号灯状态
    const signalDiv = document.getElementById('signalStatus');
    signalDiv.innerHTML = `
        <div>绿灯时间：${analysis.signal_optimization.green_time.toFixed(1)}秒</div>
        <div>拥堵等级：${(analysis.signal_optimization.congestion_level * 100).toFixed(0)}%</div>
        <div>β因子：${analysis.signal_optimization.beta.toFixed(3)}</div>
    `;
    
    // 更新流量预测
    const predictionDiv = document.getElementById('trafficPrediction');
    predictionDiv.innerHTML = `
        <div>预测流量：${analysis.traffic_prediction.predicted_flow} 辆/小时</div>
        <div>置信度：${(analysis.traffic_prediction.confidence * 100).toFixed(0)}%</div>
    `;
}

// ==================== 天气信息 ====================
/**
 * 加载天气信息
 * 调用高德地图天气 API 获取郑州中原区的天气数据
 */
async function loadWeather() {
    // 高德地图 API Key（用户提供）
    const AMAP_API_KEY = '72185d0baa8bf5211c25a929606bc156';
    // 城市：郑州（中原区）
    const city = '郑州'; // 郑州城市编码：410100
    
    try {
        // 调用高德天气 API
        const response = await fetch(
            `https://restapi.amap.com/v3/weather/weatherInfo?city=${city}&key=${AMAP_API_KEY}`
        );
        
        if (!response.ok) {
            throw new Error('天气 API 请求失败');
        }
        
        const data = await response.json();
        
        if (data.status === '1' && data.lives && data.lives.length > 0) {
            const weather = data.lives[0];
            // 更新各个天气显示元素
            document.getElementById('temperature').textContent = weather.temperature + '°C';
            document.getElementById('weather').textContent = weather.weather;
            document.getElementById('humidity').textContent = (weather.humidity || '--') + '%';
            document.getElementById('wind').textContent = weather.windpower + '级';
            
            console.log('天气数据加载成功:', weather);
        } else {
            // API返回数据异常，使用默认数据
            console.warn('天气 API 返回数据异常:', data);
            useDefaultWeather();
        }
        
    } catch (error) {
        console.error('天气加载失败:', error);
        // 使用默认天气数据
        useDefaultWeather();
    }
}

/**
 * 使用默认天气数据（当 API 调用失败时）
 */
function useDefaultWeather() {
    document.getElementById('temperature').textContent = '25°C';
    document.getElementById('weather').textContent = '晴';
    document.getElementById('humidity').textContent = '60%';
    document.getElementById('wind').textContent = '2级';
}

// ==================== 辅助功能 ====================
/**
 * 启动/停止 自动分析
 */
function toggleAutoAnalysis() {
    const btn = document.getElementById('autoAnalysisBtn');
    
    if (analysisInterval) {
        // 停止自动分析
        clearInterval(analysisInterval);
        analysisInterval = null;
        btn.textContent = '启动自动分析';
        btn.classList.remove('active');
    } else {
        // 启动自动分析（每 5 秒一次）
        analysisInterval = setInterval(() => {
            captureSnapshot();
        }, 5000);
        btn.textContent = '停止自动分析';
        btn.classList.add('active');
    }
}

/**
 * 清空抓拍记录
 */
function clearSnapshots() {
    const gallery = document.getElementById('snapshotGallery');
    gallery.innerHTML = '';
    snapshots = [];
}

/**
 * 导出抓拍记录
 */
function exportSnapshots() {
    if (snapshots.length === 0) {
        alert('没有可导出的记录');
        return;
    }
    
    // 创建导出数据的 JSON
    const exportData = {
        exportTime: new Date().toISOString(),
        totalSnapshots: snapshots.length,
        snapshots: snapshots.map(s => ({
            time: s.time.toISOString(),
            imageData: s.imageData
        }))
    };
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(exportData)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `snapshots_${new Date().getTime()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// ==================== 页面事件绑定 ====================
// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    stopCamera();
    if (analysisInterval) {
        clearInterval(analysisInterval);
    }
});

// ==================== 打开 Dashboard ====================
/**
 * 打开 Streamlit Dashboard
 * Dashboard 是一个独立的可视化页面，需要先安装依赖并启动
 */
function openDashboard() {
    // Dashboard 地址
    const dashboardUrl = 'http://localhost:8501';
    
    // 检查 Dashboard 是否已启动
    fetch(dashboardUrl, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                // Dashboard 已启动，直接打开
                window.open(dashboardUrl, '_blank');
            } else {
                // Dashboard 未启动，提示用户
                alert('Dashboard 未启动！\n\n请在项目目录下运行：\nstreamlit run dashboard.py\n\n然后访问：http://localhost:8501');
            }
        })
        .catch(() => {
            // 无法连接，提示用户启动 Dashboard
            alert('Dashboard 未启动！\n\n请打开终端并运行：\nstreamlit run dashboard.py\n\n然后访问：http://localhost:8501');
        });
}

// 导出全局函数供 HTML 调用
window.startCamera = startCamera;
window.stopCamera = stopCamera;
window.captureSnapshot = captureSnapshot;
window.toggleAutoAnalysis = toggleAutoAnalysis;
window.clearSnapshots = clearSnapshots;
window.exportSnapshots = exportSnapshots;
window.openDashboard = openDashboard;
