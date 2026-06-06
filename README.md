[README.md](https://github.com/user-attachments/files/28663517/README.md)
# 🚦 智慧交通Agent系统

> 基于 YOLO + LSTM + 非线性控制的自适应交通管理系统

[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-v8.0-blue.svg)](https://github.com/ultralytics/ultralytics)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg)](https://www.python.org/)

## ⚡ 快速启动

### 一键启动（推荐）

双击 `start_system.vbs` 即可启动系统（无窗口后台运行）

> 🎉 自动完成：
> 1. 启动 Go 后端服务（完全隐藏）
> 2. 打开前端页面（自动打开浏览器）

---

## 📋 功能特性

- ✅ **紧急车辆检测** - YOLOv8 检测救护车、消防车、警车
- ✅ **车流量预测** - LSTM 神经网络预测未来交通流量
- ✅ **排队长度计算** - 像素点矩阵仿射逻辑（无三角函数）
- ✅ **信号灯优化** - 非线性模型 + β调节因子
- ✅ **天气影响** - 雨雪雾天气自动调整通行时间
- ✅ **实时分析** - 前端实时展示 + Go 后端 API

## 🚀 快速开始

### 1. 一键启动（推荐）

双击运行 **`start_system.bat`**

### 2. 手动启动

```bash
cd go_backend
"C:\Users\13069\go\pkg\mod\golang.org\toolchain@v0.0.1-go1.26.3.windows-amd64\bin\go.exe" run main.go
```

后端将在 `http://localhost:8080` 启动

### 3. 打开前端界面

在浏览器中打开：
```
web/html/index.html
```

### 4. 使用系统

1. 点击 **启动摄像头** 开启视频流
2. 点击 **抓拍分析** 进行单次分析
3. 点击 **实时分析** 开启自动模式（每5秒）
4. 查看右侧 **实时数据**：
   - 📊 排队长度
   - 🚨 紧急车辆
   - ⏱️ 信号灯建议
   - 🌤️ 天气信息

## 📁 项目结构

```
smart-traffic-yolo-main/
├── go_backend/                    # Go 后端服务
│   ├── main.go                   # 主程序
│   ├── go.mod                    # Go 模块配置
│   └── go.sum                    # 依赖锁定
│
├── logic/                         # Python AI 模块
│   ├── emergency_detector.py      # 紧急车辆检测（YOLO）
│   ├── lstm_predictor.py         # LSTM 车流预测
│   ├── queue_calculator.py        # 排队长度计算
│   └── traffic_controller.py      # 非线性信号灯优化
│
├── web/                          # 前端界面
│   ├── html/index.html           # 主页面
│   ├── css/style.css            # 样式
│   └── js/app.js                # JavaScript 逻辑
│
├── yolo/                         # YOLO 模型
│   ├── best.pt                   # 训练好的模型（6.2MB）
│   └── detect.py                 # 检测脚本
│
├── start_system.vbs              # ⭐ 一键启动脚本（VBS）
├── README.md                     # 项目说明文档
└── requirements.txt              # Python 依赖
```

## 🔧 核心算法

### 1. 排队长度计算（像素点矩阵仿射）

使用二次多项式拟合，避免三角函数：

```
real_distance = a × pixel² + b × pixel + c
```

**特点**：
- 计算效率高
- 精度可靠
- 无需三角函数

### 2. 非线性信号灯优化

#### β调节因子（Sigmoid函数）
```
β = 0.1 + 0.8 × sigmoid(6 × (congestion - 0.5))
```

**作用**：防止通行时间突变

#### 绿灯时间（对数函数）
```
green_time = min + (max-min) × log(1+base_time) / log(101)
```

**作用**：避免通行时间线性增长

### 3. 天气影响因子

| 天气 | 影响因子 | 说明 |
|------|:--------:|------|
| ☀️ 晴天/多云 | 1.0 | 无影响 |
| 🌧️ 小雨 | 1.1 | +10% |
| 🌧️ 大雨 | 1.2 | +20% |
| 🌨️ 小雪 | 1.2 | +20% |
| 🌨️ 大雪 | 1.3 | +30% |
| 🌫️ 雾 | 1.4 | +40% |
| 🌧️🌨️ 雨夹雪 | 1.35 | +35% |
| 冰雹 | 1.3 | +30% |

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

## 🎨 界面预览

前端界面包含：
- 📹 实时摄像头画面
- 📸 抓拍记录
- 📊 排队长度统计
- 🚨 紧急车辆检测
- ⏱️ 信号灯优化建议
- 🌤️ 天气信息（高德API）

## 📦 安装依赖

### Go 依赖（自动安装）

```bash
cd go_backend
go mod tidy
```

### Python 依赖（可选）

```bash
pip install -r requirements.txt
```

**主要依赖**：
- `ultralytics` - YOLOv8
- `tensorflow` - LSTM 模型
- `opencv-python` - 图像处理
- `flask` - Python API（可选）

## ⚠️ 注意事项

### 1. 摄像头权限
- 必须通过 `localhost` 或 `127.0.0.1` 访问
- 允许浏览器访问摄像头

### 2. 天气 API
- 已配置高德地图 API Key：`72185d0baa8bf5211c25a929606bc156`
- 城市：郑州
- 网络异常时使用默认天气数据

### 3. Go 环境
如果 `go run` 不可用，使用：
```bash
start_system.vbs
```

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

### 问题：启动脚本无法运行
**解决**：
1. 右键 `start_system.vbs` → 用记事本打开
2. 检查 Go 路径是否正确
3. 手动启动：
   ```bash
   cd go_backend
   go run main.go
   ```

## 📚 技术栈

| 层次 | 技术 |
|------|------|
| **后端** | Go 1.21+ / Gin 框架 |
| **前端** | HTML5 / CSS3 / JavaScript |
| **AI** | YOLOv8 / LSTM / TensorFlow |
| **图像** | OpenCV / Pillow |
| **天气** | 高德地图 API |

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**：v1.0  
**更新时间**：2026-06-06  
**作者**：AI Assistant
