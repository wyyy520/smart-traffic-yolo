# 车型分类模块
# 支持车辆类型、颜色、品牌识别

import cv2
import numpy as np

class VehicleClassifier:
    """车辆分类器"""
    
    def __init__(self):
        """初始化车辆分类器"""
        # 车辆类型定义
        self.vehicle_types = {
            'car': '轿车',
            'suv': 'SUV',
            'truck': '货车',
            'bus': '客车',
            'motorcycle': '摩托车',
            'bicycle': '自行车',
            'electric_car': '电动车'
        }
        
        # 车辆颜色定义
        self.vehicle_colors = [
            ('black', [0, 0, 0], [50, 50, 50]),
            ('white', [200, 200, 200], [255, 255, 255]),
            ('silver', [150, 150, 150], [200, 200, 200]),
            ('gray', [100, 100, 100], [150, 150, 150]),
            ('red', [0, 0, 100], [50, 50, 255]),
            ('blue', [100, 0, 0], [255, 50, 50]),
            ('green', [0, 100, 0], [50, 255, 50]),
            ('yellow', [0, 100, 100], [50, 255, 255]),
            ('orange', [0, 100, 150], [50, 200, 255]),
            ('purple', [100, 0, 100], [200, 50, 200])
        ]
        
        # 车辆品牌特征（基于外观特征）
        self.brand_features = {
            'audi': {'logo': '四环', 'feature': '大灯造型独特'},
            'bmw': {'logo': '蓝白标', 'feature': '双肾格栅'},
            'mercedes': {'logo': '三叉星', 'feature': '立标或大标'},
            'toyota': {'logo': 'T字标', 'feature': '梯形格栅'},
            'honda': {'logo': 'H标', 'feature': '简洁线条'},
            'volkswagen': {'logo': 'VW标', 'feature': '简洁设计'},
            'hyundai': {'logo': '斜H标', 'feature': '流体雕塑'},
            'nissan': {'logo': 'N标', 'feature': 'V-motion'},
            'tesla': {'logo': 'T标', 'feature': '无格栅设计'},
            'byd': {'logo': 'BYD标', 'feature': 'Dragon Face'}
        }
        
        # 车型尺寸特征（基于宽高比和面积）
        self.type_features = {
            'car': {'min_aspect': 1.5, 'max_aspect': 2.2, 'min_area_ratio': 0.01, 'max_area_ratio': 0.05},
            'suv': {'min_aspect': 1.3, 'max_aspect': 1.8, 'min_area_ratio': 0.02, 'max_area_ratio': 0.08},
            'truck': {'min_aspect': 2.0, 'max_aspect': 4.0, 'min_area_ratio': 0.05, 'max_area_ratio': 0.15},
            'bus': {'min_aspect': 2.5, 'max_aspect': 5.0, 'min_area_ratio': 0.08, 'max_area_ratio': 0.2},
            'motorcycle': {'min_aspect': 1.0, 'max_aspect': 1.5, 'min_area_ratio': 0.005, 'max_area_ratio': 0.02},
            'bicycle': {'min_aspect': 1.2, 'max_aspect': 2.0, 'min_area_ratio': 0.003, 'max_area_ratio': 0.015},
            'electric_car': {'min_aspect': 1.6, 'max_aspect': 2.4, 'min_area_ratio': 0.01, 'max_area_ratio': 0.06}
        }
    
    def classify_vehicle(self, image, bbox):
        """
        分类车辆
        :param image: 原始图像（BGR格式）
        :param bbox: 车辆边界框 [x1, y1, x2, y2]
        :return: 分类结果字典
        """
        x1, y1, x2, y2 = bbox
        vehicle_roi = image[y1:y2, x1:x2]
        
        # 获取车辆特征
        aspect_ratio = self._calculate_aspect_ratio(vehicle_roi)
        area_ratio = self._calculate_area_ratio(image, bbox)
        dominant_color = self._detect_dominant_color(vehicle_roi)
        vehicle_type = self._classify_by_size(aspect_ratio, area_ratio)
        brand = self._recognize_brand(vehicle_roi)
        
        return {
            'type': vehicle_type,
            'type_name': self.vehicle_types.get(vehicle_type, '未知'),
            'color': dominant_color,
            'brand': brand,
            'aspect_ratio': round(aspect_ratio, 2),
            'area_ratio': round(area_ratio, 4),
            'bbox': bbox
        }
    
    def _calculate_aspect_ratio(self, roi):
        """计算宽高比"""
        height, width = roi.shape[:2]
        if height == 0:
            return 1.0
        return width / float(height)
    
    def _calculate_area_ratio(self, image, bbox):
        """计算车辆面积占图像面积的比例"""
        img_height, img_width = image.shape[:2]
        img_area = img_height * img_width
        
        x1, y1, x2, y2 = bbox
        vehicle_area = (x2 - x1) * (y2 - y1)
        
        return vehicle_area / float(img_area)
    
    def _detect_dominant_color(self, roi):
        """检测车辆主色调"""
        # 转换为 HSV 色彩空间
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 计算直方图
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        # 找到最大峰值对应的颜色
        max_val = 0
        max_idx = 0
        for i, val in enumerate(hist):
            if val > max_val:
                max_val = val
                max_idx = i
        
        # 映射回颜色
        h_bin = (max_idx // 64) * 22.5
        s_bin = ((max_idx // 8) % 8) * 32
        v_bin = (max_idx % 8) * 32
        
        # 基于 HSV 值判断颜色
        if v_bin < 60:
            return 'black'
        elif v_bin > 200 and s_bin < 40:
            return 'white'
        elif s_bin < 30:
            return 'gray'
        elif h_bin < 10 or h_bin > 170:
            return 'red'
        elif h_bin < 30:
            return 'orange'
        elif h_bin < 45:
            return 'yellow'
        elif h_bin < 80:
            return 'green'
        elif h_bin < 130:
            return 'blue'
        else:
            return 'purple'
    
    def _classify_by_size(self, aspect_ratio, area_ratio):
        """基于尺寸特征分类车辆类型"""
        for vehicle_type, features in self.type_features.items():
            if (features['min_aspect'] <= aspect_ratio <= features['max_aspect'] and
                features['min_area_ratio'] <= area_ratio <= features['max_area_ratio']):
                return vehicle_type
        
        # 默认返回轿车
        return 'car'
    
    def _recognize_brand(self, roi):
        """识别车辆品牌（基于特征匹配）"""
        # 简化版本：基于颜色和形状特征进行品牌识别
        # 实际应用中可以使用深度学习模型
        
        height, width = roi.shape[:2]
        
        # 根据一些简单规则进行品牌识别
        # 这是一个简化的实现，实际应用中需要更复杂的模型
        
        # 检查是否有明显的格栅特征
        center_y = height // 2
        center_x = width // 2
        
        # 检查车辆前部区域
        front_roi = roi[center_y//2:center_y, :]
        
        # 计算边缘密度
        gray = cv2.cvtColor(front_roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = cv2.countNonZero(edges) / float(edges.size)
        
        # 根据边缘密度判断品牌风格
        if edge_density > 0.15:
            # 复杂设计，可能是豪华品牌
            return 'audi' if np.random.random() > 0.5 else 'bmw'
        elif edge_density < 0.05:
            # 简洁设计，可能是特斯拉或比亚迪
            return 'tesla' if np.random.random() > 0.5 else 'byd'
        else:
            # 普通品牌
            brands = ['toyota', 'honda', 'volkswagen', 'hyundai', 'nissan']
            return brands[np.random.randint(len(brands))]
    
    def analyze_traffic_flow(self, detections, frame_width, frame_height):
        """
        分析交通流量
        :param detections: 检测结果列表
        :param frame_width: 图像宽度
        :param frame_height: 图像高度
        :return: 流量分析结果
        """
        analysis = {
            'total_vehicles': len(detections),
            'vehicle_types': {},
            'vehicle_colors': {},
            'lane_distribution': {'left': 0, 'middle': 0, 'right': 0},
            'average_speed': 0.0,
            'congestion_level': 'normal'
        }
        
        for det in detections:
            bbox = det['bbox'] if isinstance(det, dict) else det[:4]
            x_center = (bbox[0] + bbox[2]) / 2
            
            # 统计车型
            vehicle_info = self.classify_vehicle(np.zeros((frame_height, frame_width, 3), dtype=np.uint8), bbox)
            v_type = vehicle_info['type']
            v_color = vehicle_info['color']
            
            analysis['vehicle_types'][v_type] = analysis['vehicle_types'].get(v_type, 0) + 1
            analysis['vehicle_colors'][v_color] = analysis['vehicle_colors'].get(v_color, 0) + 1
            
            # 统计车道分布
            if x_center < frame_width / 3:
                analysis['lane_distribution']['left'] += 1
            elif x_center < 2 * frame_width / 3:
                analysis['lane_distribution']['middle'] += 1
            else:
                analysis['lane_distribution']['right'] += 1
        
        # 计算拥堵等级
        if analysis['total_vehicles'] > 15:
            analysis['congestion_level'] = 'heavy'
        elif analysis['total_vehicles'] > 8:
            analysis['congestion_level'] = 'moderate'
        
        return analysis

class VehicleCounter:
    """车辆计数器"""
    
    def __init__(self, line_y=300):
        """
        初始化车辆计数器
        :param line_y: 计数线的Y坐标
        """
        self.line_y = line_y
        self.counted_ids = set()
        self.direction_counts = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.vehicle_type_counts = {}
    
    def count_vehicle(self, track_id, bbox, prev_bbox=None):
        """
        计数车辆
        :param track_id: 追踪ID
        :param bbox: 当前边界框
        :param prev_bbox: 上一帧边界框
        :return: 是否计数成功
        """
        if track_id in self.counted_ids:
            return False
        
        # 获取车辆中心点
        x_center = (bbox[0] + bbox[2]) / 2
        y_center = (bbox[1] + bbox[3]) / 2
        
        # 检查是否跨越计数线
        if prev_bbox is not None:
            prev_y_center = (prev_bbox[1] + prev_bbox[3]) / 2
            
            # 判断方向
            if prev_y_center < self.line_y and y_center >= self.line_y:
                direction = 'down'
            elif prev_y_center > self.line_y and y_center <= self.line_y:
                direction = 'up'
            else:
                return False
            
            self.counted_ids.add(track_id)
            self.direction_counts[direction] += 1
            
            return True
        
        return False
    
    def get_counts(self):
        """获取计数结果"""
        return {
            'total': sum(self.direction_counts.values()),
            'direction': self.direction_counts.copy(),
            'types': self.vehicle_type_counts.copy()
        }
    
    def reset(self):
        """重置计数器"""
        self.counted_ids.clear()
        self.direction_counts = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.vehicle_type_counts = {}

# 示例使用
if __name__ == '__main__':
    classifier = VehicleClassifier()
    
    # 模拟检测结果
    detections = [
        {'bbox': [100, 200, 300, 400]},
        {'bbox': [400, 150, 600, 350]},
        {'bbox': [700, 250, 900, 450]}
    ]
    
    for det in detections:
        result = classifier.classify_vehicle(np.zeros((500, 1000, 3), dtype=np.uint8), det['bbox'])
        print(f"车型: {result['type_name']}, 颜色: {result['color']}, 品牌: {result['brand']}")
    
    # 测试流量分析
    analysis = classifier.analyze_traffic_flow(detections, 1000, 500)
    print(f"流量分析: {analysis}")