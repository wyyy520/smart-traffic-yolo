# smart-traffic-yolo
智能交通 | 基于 YOLOv8 的紧急车辆检测系统

## 项目介绍
本项目使用 YOLOv8n 训练实现对紧急车辆的实时检测，可应用于智慧路口、车路协同、应急优先通行等场景。

## 检测类别
- 0: ambulance 救护车
- 1: police 警车
- 2: fire truck 消防车

## 模型信息
- 模型：YOLOv8n
- 训练轮数：50 epochs
- 训练环境：CPU
- 数据集：314 张标注图片

## 功能
- 批量识别图片
- 输出带标注框的检测结果
- 可直接部署用于智能交通项目

## 使用方法
```python
from ultralytics import YOLO

# 加载模型
model = YOLO("best.pt")

# 识别图片
results = model("test.jpg")
results[0].save("result.jpg")