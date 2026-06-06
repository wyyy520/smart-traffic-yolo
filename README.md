# 🚦 智慧交通Agent系统

> 基于 YOLO + LSTM + 非线性控制的自适应交通管理系统

[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-v8.0-blue.svg)](https://github.com/ultralytics/ultralytics)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io/)

---

## ⚡ 快速启动

### 一键启动（推荐）

```bash
# Windows
双击 start_system.vbs

# 或手动启动
cd go_backend && go run main.go
```

### 启动 Dashboard

```bash
streamlit run dashboard.py
```

---

## 📋 功能特性

### ✅ 核心功能
- **紧急车辆检测** - YOLOv8 实时检测救护车、消防车、警车
- **车流量预测** - LSTM 神经网络预测未来交通流量
- **排队长度计算** - 像素点矩阵仿射逻辑（无三角函数）
- **信号灯优化** - 非线性模型 + β调节因子防止突变
- **天气影响** - 雨雪雾天气自动调整通行时间

### ✅ 高级功能（新增）
- **ByteTrack 目标追踪** - 遮挡环境下高精度 ID 保持
- **车牌识别 OCR** - 支持蓝牌、黄牌、绿牌、港澳牌
- **车型分类** - 识别轿车、SUV、货车、客车等
- **Streamlit Dashboard** - 实时数据可视化平台

---

## 🚀 快速开始

### 1. 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Go | 1.21+ | 后端服务 |
| Python | 3.8+ | AI 模块 |
| Node.js | 14+ | 前端开发（可选） |

### 2. 一键启动

```bash
# 方法1：VBS 脚本（无窗口）
双击 start_system.vbs

# 方法2：手动启动
cd go_backend
go run main.go
```

### 3. 启动可视化 Dashboard

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

访问：`http://localhost:8501`

### 4. 打开前端界面

在浏览器中打开：
```
web/html/index.html
```

---

## 📁 项目结构

```
smart-traffic-yolo/
├── go_backend/                    # Go 后端服务
│   ├── main.go                   # 主程序（Gin框架）
│   ├── go.mod                    # Go 模块配置
│   ├── go.sum                    # 依赖锁定
│   └── .vscode/                  # VS Code 配置
│
├── logic/                         # Python AI 模块
│   ├── emergency_detector.py      # 紧急车辆检测（YOLO）
│   ├── lstm_predictor.py         # LSTM 车流预测
│   ├── queue_calculator.py        # 排队长度计算（像素仿射）
│   ├── traffic_controller.py      # 非线性信号灯优化
│   ├── vehicle_tracker.py         # ByteTrack 目标追踪 ⭐ 新增
│   ├── license_plate_recognizer.py # 车牌识别 OCR ⭐ 新增
│   └── vehicle_classifier.py      # 车型分类 ⭐ 新增
│
├── web/                          # 前端界面
│   ├── html/index.html           # 主页面
│   ├── css/style.css            # 样式文件
│   └── js/app.js                # JavaScript 逻辑
│
├── yolo/                         # YOLO 模型
│   ├── best.pt                   # 训练好的模型（6.2MB）
│   └── detect.py                 # 检测脚本
│
├── dashboard.py                   # Streamlit 可视化 ⭐ 新增
├── start_system.vbs              # 一键启动脚本
├── requirements.txt              # Python 依赖
└── README.md                     # 项目文档
```

---

## 🔧 核心算法

### 1. 排队长度计算（像素点矩阵仿射）

使用二次多项式拟合，避免三角函数：

```
real_distance = a × pixel² + b × pixel + c
```

**特点**：
- ✅ 计算效率高（无需三角函数）
- ✅ 精度可靠（多项式拟合）
- ✅ 扩展性强（支持多车道）

### 2. 非线性信号灯优化

#### β调节因子（Sigmoid函数）
```
β = 0.1 + 0.8 × sigmoid(6 × (congestion - 0.5))
```

**作用**：防止通行时间突变，取值范围 [0.1, 0.9]

#### 绿灯时间（对数函数）
```
green_time = min + (max-min) × log(1+base_time) / log(101)
```

**作用**：避免通行时间线性增长，实现平滑过渡

### 3. 天气影响因子

| 天气 | 影响因子 | 说明 |
|------|:--------:|------|
| ☀️ 晴天/多云 | 1.0 | 无影响 |
| 🌧️ 小雨 | 1.1 | +10% 通行时间 |
| 🌧️ 大雨 | 1.2 | +20% 通行时间 |
| 🌨️ 小雪 | 1.2 | +20% 通行时间 |
| 🌨️ 大雪 | 1.3 | +30% 通行时间 |
| 🌫️ 雾 | 1.4 | +40% 通行时间 |
| 🌧️🌨️ 雨夹雪 | 1.35 | +35% 通行时间 |
| 冰雹 | 1.3 | +30% 通行时间 |

---

## 🆕 新增高级功能

### 1. ByteTrack 目标追踪

**文件**：`logic/vehicle_tracker.py`

**功能特点**：
- 🔍 高精度多目标追踪
- 🛡️ 遮挡环境下 ID 保持能力强
- 📈 速度估计和轨迹记录
- 🔄 实时轨迹绘制

**使用示例**：
```python
from logic.vehicle_tracker import VehicleTracker

tracker = VehicleTracker()
results = tracker.process_frame(detections)
# 返回：[{track_id, bbox, score, class, center, velocity, history}]
```

### 2. 车牌识别 OCR

**文件**：`logic/license_plate_recognizer.py`

**功能特点**：
- 🔤 双引擎支持（EasyOCR + PaddleOCR）
- 🚗 支持多种车牌类型：蓝牌、黄牌、绿牌、白牌、黑牌
- 🎨 自动识别车牌颜色
- 💾 车牌数据库管理

**使用示例**：
```python
from logic.license_plate_recognizer import LicensePlateRecognizer

recognizer = LicensePlateRecognizer()
results = recognizer.recognize_plate(image)
# 返回：[{plate, confidence, color, bbox}]
```

### 3. 车型分类

**文件**：`logic/vehicle_classifier.py`

**功能特点**：
- 🚙 车辆类型识别：轿车、SUV、货车、客车、摩托车等
- 🎨 车辆颜色识别：10种常用颜色
- 🏷️ 车辆品牌识别
- 📊 交通流量分析

**使用示例**：
```python
from logic.vehicle_classifier import VehicleClassifier

classifier = VehicleClassifier()
result = classifier.classify_vehicle(image, bbox)
# 返回：{type, type_name, color, brand, aspect_ratio, area_ratio}
```

### 4. Streamlit Dashboard

**文件**：`dashboard.py`

**功能模块**：
- 📊 实时指标监控卡片
- 📈 24小时流量趋势图
- 🥧 车辆类型分布饼图
- 📉 周流量对比分析
- 🚨 紧急车辆响应统计
- 🌧️ 天气影响分析
- 🎥 实时监控视频区域

---

## 📡 API 接口

### 健康检查

```bash
GET http://localhost:8080/api/health
```

**响应**：
```json
{
  "status": "ok",
  "message": "智慧交通 Go 后端服务正常运行"
}
```

### 综合分析

```bash
POST http://localhost:8080/api/comprehensive_analysis
Content-Type: application/json
```

**请求**：
```json
{
  "image": "base64_encoded_image",
  "historical_traffic": [45, 48, 52, 49, 55, 58, 53, 50, 47, 52, 56, 54],
  "lane_start": [100, 500],
  "lane_end": [500, 500],
  "weather": "晴"
}
```

**响应**：
```json
{
  "success": true,
  "message": "分析完成",
  "analysis": {
    "queue_analysis": {
      "length": 35.5,
      "vehicle_count": 8
    },
    "emergency_detection": {
      "detected": false,
      "types": []
    },
    "signal_optimization": {
      "green_time": 42.3,
      "congestion_level": 0.35,
      "beta": 0.625,
      "weather_factor": 1.0
    },
    "traffic_prediction": {
      "predicted_flow": 48,
      "confidence": 0.85
    }
  }
}
```

---

## 🧠 AI 模型

### YOLOv8 紧急车辆检测

**模型**：`yolo/best.pt` (6.2MB)

**检测类别**：
- `0` - 🚑 ambulance (救护车)
- `1` - 🚓 police (警车)
- `2` - 🚒 fire_truck (消防车)

**测试模型**：
```python
from ultralytics import YOLO

model = YOLO('yolo/best.pt')
results = model('test.jpg', conf=0.5)
```

### LSTM 车流预测

**输入**：历史 12 个时间点的车流量数据

**输出**：下一时刻预测流量（辆/小时）

**置信度**：0.3 - 0.95

---

## 📊 Dashboard 使用指南

### 启动方式

```bash
# 安装依赖
pip install streamlit plotly pandas numpy

# 启动 Dashboard
streamlit run dashboard.py
```

### Dashboard 功能

| 模块 | 说明 |
|------|------|
| 📊 实时指标 | 车流量、紧急车辆、平均车速、排队长度 |
| 🌤️ 天气信息 | 天气状况、温度、湿度、风速 |
| 📈 流量趋势 | 24小时车辆流量变化 |
| 🥧 车型分布 | 各类车辆占比统计 |
| 📉 周对比 | 每日流量对比分析 |
| 🚨 紧急响应 | 救护车、消防车、警车统计 |
| 🌧️ 天气影响 | 天气与交通状况关系 |
| 🎥 实时监控 | 摄像头画面展示 |

---

## 📦 安装依赖

### Go 依赖（自动安装）

```bash
cd go_backend
go mod tidy
```

### Python 依赖

```bash
pip install -r requirements.txt
```

**主要依赖**：

| 依赖 | 版本 | 用途 |
|------|------|------|
| ultralytics | 8.0.196 | YOLOv8 |
| tensorflow | 2.13.0 | LSTM 模型 |
| opencv-python | 4.8.1.78 | 图像处理 |
| streamlit | 1.32.0 | Dashboard |
| plotly | 5.18.0 | 可视化图表 |
| easyocr | 1.7.0 | 车牌识别 |
| paddleocr | 2.8.0 | 车牌识别 |
| flask | 3.0.0 | Python API |

---

## ⚠️ 注意事项

### 1. 摄像头权限
- 必须通过 `localhost` 或 `127.0.0.1` 访问
- 允许浏览器访问摄像头

### 2. 天气 API
- 已配置高德地图 API Key：`72185d0baa8bf5211c25a929606bc156`
- 城市：郑州中原区
- 网络异常时使用默认天气数据

### 3. Go 环境
如果 `go run` 不可用，使用完整路径：
```bash
"C:\Users\13069\go\pkg\mod\golang.org\toolchain@v0.0.1-go1.26.3.windows-amd64\bin\go.exe" run main.go
```

---

## 🔍 故障排查

### 问题：后端无法启动
**解决**：
1. 检查 Go 版本：`go version`
2. 使用启动脚本：`start_system.vbs`
3. 检查端口占用：`netstat -ano | findstr 8080`

### 问题：天气不显示
**解决**：
1. 检查网络连接
2. 查看浏览器控制台（F12）
3. 系统会自动使用默认天气

### 问题：摄像头无法启动
**解决**：
1. 使用 `localhost` 访问
2. 允许摄像头权限
3. 检查摄像头是否被占用

### 问题：Dashboard 无法启动
**解决**：
1. 检查 Python 版本
2. 安装依赖：`pip install -r requirements.txt`
3. 检查端口占用：`netstat -ano | findstr 8501`

---

## 📚 技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| **后端** | Go / Gin | 1.21+ |
| **前端** | HTML5 / CSS3 / JavaScript | - |
| **AI** | YOLOv8 / LSTM / TensorFlow | 8.0 / 2.13 |
| **可视化** | Streamlit / Plotly | 1.32 / 5.18 |
| **图像处理** | OpenCV / Pillow | 4.8 / 10.0 |
| **OCR** | EasyOCR / PaddleOCR | 1.7 / 2.8 |
| **天气** | 高德地图 API | - |

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**：v1.1  
**更新时间**：2026-06-06  
**作者**：AI Assistant  

---

*🚦 智慧交通，让城市更畅通*
