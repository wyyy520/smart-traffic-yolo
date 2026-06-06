import cv2
import numpy as np
from ultralytics import YOLO
import time
from datetime import datetime
import os
from typing import Dict, List, Tuple, Optional
import json

class EmergencyVehicleDetector:
    def __init__(self, model_path='../yolo/best.pt', confidence_threshold=0.5):
        """
        紧急车辆检测器
        
        参数:
            model_path: YOLO模型路径
            confidence_threshold: 置信度阈值
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.class_names = {
            0: 'ambulance',    # 救护车
            1: 'police',       # 警车
            2: 'fire_truck'    # 消防车
        }
        self.detection_history = []
        self.load_model()
        
    def load_model(self):
        """
        加载YOLO模型
        """
        try:
            self.model = YOLO(self.model_path)
            print(f"✅ 模型加载成功: {self.model_path}")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise
    
    def detect_image(self, image_path: str) -> Dict:
        """
        检测单张图片
        
        参数:
            image_path: 图片路径
            
        返回:
            detection_result: 检测结果字典
        """
        if not os.path.exists(image_path):
            return {'error': f'图片不存在: {image_path}'}
        
        image = cv2.imread(image_path)
        if image is None:
            return {'error': f'无法读取图片: {image_path}'}
        
        return self.detect_frame(image)
    
    def detect_frame(self, frame: np.ndarray) -> Dict:
        """
        检测视频帧
        
        参数:
            frame: 视频帧 (numpy数组)
            
        返回:
            detection_result: 检测结果字典
        """
        if self.model is None:
            return {'error': '模型未加载'}
        
        # 使用YOLO进行检测
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        emergency_detected = False
        emergency_types = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 获取检测信息
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                
                # 转换为整数坐标
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # 获取类别名称
                class_name = self.class_names.get(class_id, 'unknown')
                
                detection = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'center': [(x1 + x2) // 2, (y1 + y2) // 2]
                }
                
                detections.append(detection)
                
                # 检查是否为紧急车辆
                if class_name in ['ambulance', 'police', 'fire_truck']:
                    emergency_detected = True
                    if class_name not in emergency_types:
                        emergency_types.append(class_name)
        
        # 记录检测历史
        detection_record = {
            'timestamp': datetime.now().isoformat(),
            'emergency_detected': emergency_detected,
            'emergency_types': emergency_types,
            'detection_count': len(detections),
            'detections': detections
        }
        self.detection_history.append(detection_record)
        
        # 保持历史记录在合理范围内
        if len(self.detection_history) > 1000:
            self.detection_history = self.detection_history[-1000:]
        
        return {
            'success': True,
            'emergency_detected': emergency_detected,
            'emergency_types': emergency_types,
            'detection_count': len(detections),
            'detections': detections,
            'timestamp': detection_record['timestamp']
        }
    
    def detect_video_stream(self, video_source=0, display_result=True, 
                           save_result=False, output_path='output.mp4'):
        """
        实时视频流检测
        
        参数:
            video_source: 视频源（摄像头索引或视频文件路径）
            display_result: 是否显示检测结果
            save_result: 是否保存检测结果
            output_path: 输出视频路径
        """
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            print(f"❌ 无法打开视频源: {video_source}")
            return
        
        # 获取视频信息
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 设置视频写入器
        video_writer = None
        if save_result:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 检测帧
                result = self.detect_frame(frame)
                
                # 在帧上绘制检测结果
                annotated_frame = self.draw_detections(frame, result)
                
                # 添加信息文本
                info_text = f"紧急车辆: {'是' if result['emergency_detected'] else '否'}"
                if result['emergency_types']:
                    info_text += f" | 类型: {', '.join(result['emergency_types'])}"
                
                cv2.putText(annotated_frame, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # 显示结果
                if display_result:
                    cv2.imshow('Emergency Vehicle Detection', annotated_frame)
                    
                    # 按'q'退出
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # 保存结果
                if save_result and video_writer is not None:
                    video_writer.write(annotated_frame)
                
                frame_count += 1
                
                # 计算FPS
                if frame_count % 30 == 0:
                    elapsed_time = time.time() - start_time
                    current_fps = frame_count / elapsed_time
                    print(f"处理帧数: {frame_count}, FPS: {current_fps:.2f}")
        
        except KeyboardInterrupt:
            print("\n检测被用户中断")
        
        finally:
            cap.release()
            if video_writer is not None:
                video_writer.release()
            cv2.destroyAllWindows()
            
            print(f"\n检测完成！")
            print(f"总帧数: {frame_count}")
            print(f"检测到紧急车辆的帧数: {sum(1 for r in self.detection_history if r['emergency_detected'])}")
    
    def draw_detections(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """
        在帧上绘制检测结果
        
        参数:
            frame: 原始帧
            result: 检测结果
            
        返回:
            annotated_frame: 标注后的帧
        """
        annotated_frame = frame.copy()
        
        # 定义颜色
        colors = {
            'ambulance': (0, 255, 255),    # 黄色
            'police': (255, 0, 0),         # 蓝色
            'fire_truck': (0, 0, 255),     # 红色
            'unknown': (128, 128, 128)     # 灰色
        }
        
        for detection in result.get('detections', []):
            class_name = detection['class_name']
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            color = colors.get(class_name, colors['unknown'])
            
            # 绘制边界框
            cv2.rectangle(annotated_frame, 
                         (bbox[0], bbox[1]), 
                         (bbox[2], bbox[3]), 
                         color, 2)
            
            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # 绘制标签背景
            cv2.rectangle(annotated_frame,
                         (bbox[0], bbox[1] - label_size[1] - 10),
                         (bbox[0] + label_size[0], bbox[1]),
                         color, -1)
            
            # 绘制标签文本
            cv2.putText(annotated_frame, label,
                       (bbox[0], bbox[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated_frame
    
    def get_emergency_vehicle_positions(self, result: Dict) -> List[Tuple[int, int]]:
        """
        获取紧急车辆位置
        
        参数:
            result: 检测结果
            
        返回:
            positions: 紧急车辆中心坐标列表
        """
        positions = []
        for detection in result.get('detections', []):
            if detection['class_name'] in ['ambulance', 'police', 'fire_truck']:
                positions.append(tuple(detection['center']))
        return positions
    
    def get_detection_statistics(self) -> Dict:
        """
        获取检测统计信息
        
        返回:
            statistics: 统计信息字典
        """
        if not self.detection_history:
            return {'total_detections': 0}
        
        total_frames = len(self.detection_history)
        emergency_frames = sum(1 for r in self.detection_history if r['emergency_detected'])
        
        # 统计各类紧急车辆出现次数
        type_counts = {'ambulance': 0, 'police': 0, 'fire_truck': 0}
        for record in self.detection_history:
            for emergency_type in record['emergency_types']:
                if emergency_type in type_counts:
                    type_counts[emergency_type] += 1
        
        statistics = {
            'total_frames': total_frames,
            'emergency_frames': emergency_frames,
            'emergency_rate': emergency_frames / total_frames if total_frames > 0 else 0,
            'type_counts': type_counts,
            'total_detections': sum(r['detection_count'] for r in self.detection_history)
        }
        
        return statistics
    
    def save_detection_history(self, file_path='detection_history.json'):
        """
        保存检测历史记录
        
        参数:
            file_path: 保存路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.detection_history, f, ensure_ascii=False, indent=2)
            print(f"✅ 检测历史已保存到: {file_path}")
        except Exception as e:
            print(f"❌ 保存检测历史失败: {e}")
    
    def load_detection_history(self, file_path='detection_history.json'):
        """
        加载检测历史记录
        
        参数:
            file_path: 加载路径
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.detection_history = json.load(f)
                print(f"✅ 检测历史已从 {file_path} 加载")
                return True
        except Exception as e:
            print(f"❌ 加载检测历史失败: {e}")
        return False
    
    def batch_detect_images(self, image_folder: str, output_folder: str = 'detect_results'):
        """
        批量检测图片
        
        参数:
            image_folder: 图片文件夹路径
            output_folder: 输出文件夹路径
        """
        if not os.path.exists(image_folder):
            print(f"❌ 图片文件夹不存在: {image_folder}")
            return
        
        os.makedirs(output_folder, exist_ok=True)
        
        image_files = [f for f in os.listdir(image_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        print(f"找到 {len(image_files)} 张图片")
        
        for i, image_file in enumerate(image_files, 1):
            image_path = os.path.join(image_folder, image_file)
            result = self.detect_image(image_path)
            
            if result.get('success'):
                # 读取并标注图片
                image = cv2.imread(image_path)
                annotated_image = self.draw_detections(image, result)
                
                # 保存结果
                output_path = os.path.join(output_folder, f"detected_{image_file}")
                cv2.imwrite(output_path, annotated_image)
                
                print(f"[{i}/{len(image_files)}] {image_file}: "
                      f"检测到 {result['detection_count']} 个目标, "
                      f"紧急车辆: {'是' if result['emergency_detected'] else '否'}")
        
        print(f"✅ 批量检测完成！结果保存在: {output_folder}")


# 示例使用
if __name__ == "__main__":
    # 创建检测器
    detector = EmergencyVehicleDetector(
        model_path='../yolo/best.pt',
        confidence_threshold=0.5
    )
    
    print("=== 紧急车辆检测系统 ===")
    print("1. 检测单张图片")
    print("2. 批量检测图片")
    print("3. 实时视频流检测")
    print("4. 获取检测统计")
    
    choice = input("请选择功能 (1-4): ")
    
    if choice == '1':
        image_path = input("请输入图片路径: ")
        result = detector.detect_image(image_path)
        print(f"检测结果: {result}")
        
    elif choice == '2':
        image_folder = input("请输入图片文件夹路径: ")
        detector.batch_detect_images(image_folder)
        
    elif choice == '3':
        print("开始实时检测（按'q'退出）...")
        detector.detect_video_stream(video_source=0, display_result=True)
        
    elif choice == '4':
        stats = detector.get_detection_statistics()
        print(f"检测统计: {stats}")
    
    # 保存检测历史
    detector.save_detection_history()