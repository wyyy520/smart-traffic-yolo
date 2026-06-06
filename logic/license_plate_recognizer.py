# 车牌识别 OCR 模块
# 支持多种车牌类型识别：普通蓝牌、黄牌、新能源车牌、港澳车牌等

import cv2
import numpy as np
import os

class LicensePlateRecognizer:
    """车牌识别器"""
    
    def __init__(self, use_easyocr=True, use_paddleocr=False):
        """
        初始化车牌识别器
        :param use_easyocr: 是否使用 EasyOCR
        :param use_paddleocr: 是否使用 PaddleOCR
        """
        self.use_easyocr = use_easyocr
        self.use_paddleocr = use_paddleocr
        
        # 车牌字符集
        self.chinese_chars = '京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领'
        self.letter_chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # 不含 I, O
        self.number_chars = '0123456789'
        
        # 车牌颜色映射
        self.color_map = {
            0: 'blue',      # 蓝牌
            1: 'yellow',    # 黄牌
            2: 'green',     # 绿牌（新能源）
            3: 'white',     # 白牌（警用车）
            4: 'black'      # 黑牌（港澳）
        }
        
        # 初始化 OCR 引擎
        self.easyocr_reader = None
        self.paddleocr_detector = None
        
        if self.use_easyocr:
            try:
                from easyocr import Reader
                self.easyocr_reader = Reader(['ch_sim', 'en'], gpu=False)
            except ImportError:
                print("警告：EasyOCR 未安装")
                self.use_easyocr = False
        
        if self.use_paddleocr:
            try:
                from paddleocr import PaddleOCR
                self.paddleocr_detector = PaddleOCR(use_angle_cls=True, lang='ch')
            except ImportError:
                print("警告：PaddleOCR 未安装")
                self.use_paddleocr = False
    
    def preprocess_image(self, image):
        """
        图像预处理：增强对比度、去噪、边缘检测
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 高斯模糊去噪
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 自适应阈值二值化
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return morph
    
    def detect_plate_region(self, image):
        """
        检测车牌区域
        :return: 车牌区域列表 [(x1, y1, x2, y2), ...]
        """
        morph = self.preprocess_image(image)
        
        # 轮廓检测
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        plate_regions = []
        
        for contour in contours:
            # 计算轮廓面积
            area = cv2.contourArea(contour)
            if area < 300 or area > 5000:
                continue
            
            # 获取边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 检查宽高比（车牌宽高比约为 3:1）
            aspect_ratio = w / float(h)
            if aspect_ratio < 2.5 or aspect_ratio > 5.0:
                continue
            
            # 检查面积占比
            rect_area = w * h
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / float(hull_area)
            
            if solidity > 0.8:
                plate_regions.append((x, y, x + w, y + h))
        
        return plate_regions
    
    def recognize_plate(self, image):
        """
        识别车牌
        :param image: 图像（BGR格式）
        :return: 识别结果列表 [{'plate': '车牌号码', 'confidence': 置信度, 'color': '颜色', 'bbox': 边界框}, ...]
        """
        results = []
        
        # 检测车牌区域
        plate_regions = self.detect_plate_region(image)
        
        for (x1, y1, x2, y2) in plate_regions:
            # 提取车牌区域
            plate_roi = image[y1:y2, x1:x2]
            
            # 识别车牌号码
            plate_text, confidence = self._ocr_recognize(plate_roi)
            
            # 判断车牌颜色
            plate_color = self._detect_plate_color(plate_roi)
            
            if plate_text and confidence > 0.7:
                results.append({
                    'plate': plate_text,
                    'confidence': confidence,
                    'color': plate_color,
                    'bbox': [x1, y1, x2, y2]
                })
        
        # 按置信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return results
    
    def _ocr_recognize(self, plate_image):
        """
        使用 OCR 识别车牌号码
        """
        text = ""
        confidence = 0.0
        
        # 优先使用 PaddleOCR
        if self.use_paddleocr and self.paddleocr_detector:
            try:
                result = self.paddleocr_detector.ocr(plate_image, cls=True)
                if result and len(result) > 0:
                    for line in result:
                        for word in line:
                            text += word[1][0]
                            confidence = max(confidence, word[1][1])
            except Exception as e:
                print(f"PaddleOCR 错误: {e}")
        
        # 如果 PaddleOCR 失败，使用 EasyOCR
        if not text and self.use_easyocr and self.easyocr_reader:
            try:
                result = self.easyocr_reader.readtext(plate_image)
                for detection in result:
                    text += detection[1]
                    confidence = max(confidence, detection[2])
            except Exception as e:
                print(f"EasyOCR 错误: {e}")
        
        # 清理识别结果
        text = self._clean_plate_text(text)
        
        return text, confidence
    
    def _clean_plate_text(self, text):
        """
        清理车牌文本：只保留有效字符
        """
        cleaned = ""
        valid_chars = self.chinese_chars + self.letter_chars + self.number_chars
        
        for char in text:
            if char in valid_chars:
                cleaned += char
        
        # 验证车牌格式
        if len(cleaned) >= 7:
            # 第一个字符应该是省份简称
            if cleaned[0] not in self.chinese_chars:
                # 尝试从第二个字符开始
                if len(cleaned) > 1 and cleaned[1] in self.chinese_chars:
                    cleaned = cleaned[1:]
        
        return cleaned[:8]  # 最多8个字符
    
    def _detect_plate_color(self, plate_image):
        """
        检测车牌颜色
        """
        # 获取图像的平均颜色
        hsv = cv2.cvtColor(plate_image, cv2.COLOR_BGR2HSV)
        
        # 定义颜色范围
        color_ranges = {
            'blue': [(90, 50, 50), (130, 255, 255)],
            'yellow': [(20, 100, 100), (30, 255, 255)],
            'green': [(40, 50, 50), (80, 255, 255)],
            'white': [(0, 0, 200), (180, 30, 255)],
            'black': [(0, 0, 0), (180, 255, 50)]
        }
        
        # 计算每个颜色范围内的像素数
        max_count = 0
        detected_color = 'blue'
        
        for color, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            count = cv2.countNonZero(mask)
            
            if count > max_count:
                max_count = count
                detected_color = color
        
        return detected_color
    
    def is_valid_plate(self, plate_text):
        """
        验证车牌号码是否有效
        """
        if len(plate_text) < 7 or len(plate_text) > 8:
            return False
        
        # 第一个字符必须是省份简称
        if plate_text[0] not in self.chinese_chars:
            return False
        
        # 第二个字符必须是字母
        if plate_text[1] not in self.letter_chars:
            return False
        
        # 其余字符必须是字母或数字
        for char in plate_text[2:]:
            if char not in self.letter_chars + self.number_chars:
                return False
        
        return True

class LicensePlateDatabase:
    """车牌数据库管理"""
    
    def __init__(self, db_path='license_plates.db'):
        """
        初始化车牌数据库
        """
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT UNIQUE,
                color TEXT,
                vehicle_type TEXT,
                owner_info TEXT,
                registered_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def add_plate(self, plate, color='blue', vehicle_type='car', owner_info=''):
        """添加车牌记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO plates 
                (plate, color, vehicle_type, owner_info, registered_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (plate, color, vehicle_type, owner_info))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加车牌失败: {e}")
            return False
    
    def query_plate(self, plate):
        """查询车牌信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM plates WHERE plate = ?', (plate,))
        result = cursor.fetchone()
        
        if result:
            return {
                'id': result[0],
                'plate': result[1],
                'color': result[2],
                'vehicle_type': result[3],
                'owner_info': result[4],
                'registered_at': result[5],
                'created_at': result[6]
            }
        return None
    
    def delete_plate(self, plate):
        """删除车牌记录"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM plates WHERE plate = ?', (plate,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_all_plates(self):
        """获取所有车牌记录"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM plates ORDER BY created_at DESC')
        results = cursor.fetchall()
        
        plates = []
        for result in results:
            plates.append({
                'id': result[0],
                'plate': result[1],
                'color': result[2],
                'vehicle_type': result[3],
                'owner_info': result[4],
                'registered_at': result[5],
                'created_at': result[6]
            })
        
        return plates
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

# 示例使用
if __name__ == '__main__':
    # 初始化识别器
    recognizer = LicensePlateRecognizer(use_easyocr=True, use_paddleocr=False)
    
    # 加载测试图像
    # test_image = cv2.imread('test_plate.jpg')
    
    # 模拟识别
    print("车牌识别器初始化完成")
    print("支持的车牌类型：蓝牌、黄牌、绿牌、白牌、黑牌")
    
    # 测试数据库
    db = LicensePlateDatabase()
    db.add_plate('京A12345', 'blue', 'car', '测试车辆')
    result = db.query_plate('京A12345')
    print(f"查询结果: {result}")
    db.close()