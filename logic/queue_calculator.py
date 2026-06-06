import numpy as np
import cv2

class QueueLengthCalculator:
    def __init__(self, reference_points, real_world_distances):
        """
        基于像素点矩阵仿射逻辑的排队长度计算器
        
        参数:
            reference_points: 参考点坐标列表 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
            real_world_distances: 参考点对应的实际距离 [d1, d2, d3, d4] (单位：米)
        """
        self.reference_points = np.array(reference_points, dtype=np.float32)
        self.real_world_distances = np.array(real_world_distances, dtype=np.float32)
        self.affine_matrix = None
        self.inverse_matrix = None
        self.calibrate()
        
    def calibrate(self):
        """
        计算仿射变换矩阵，用于像素坐标到实际距离的映射
        使用最小二乘法拟合仿射变换
        """
        if len(self.reference_points) < 3:
            raise ValueError("至少需要3个参考点进行仿射变换")
        
        # 构建用于最小二乘法的矩阵
        # 仿射变换: [x', y']^T = A * [x, y, 1]^T
        # 其中 A 是 2x3 矩阵
        
        pixel_coords = np.column_stack([
            self.reference_points,
            np.ones(len(self.reference_points))
        ])
        
        # 这里我们简化处理，假设主要变换发生在车道方向
        # 我们将像素距离映射到实际距离
        pixel_distances = self._calculate_pixel_distances()
        
        # 使用多项式拟合像素距离到实际距离的映射
        # degree=2 表示二次多项式，可以处理非线性关系
        self.poly_coeffs = np.polyfit(pixel_distances, self.real_world_distances, 2)
        
        print("标定完成！多项式系数:", self.poly_coeffs)
        
    def _calculate_pixel_distances(self):
        """
        计算参考点之间的像素距离
        """
        pixel_distances = []
        for i in range(len(self.reference_points) - 1):
            dist = np.linalg.norm(self.reference_points[i+1] - self.reference_points[i])
            pixel_distances.append(dist)
        return np.array(pixel_distances)
    
    def pixel_to_real_distance(self, pixel_distance):
        """
        将像素距离转换为实际距离
        
        参数:
            pixel_distance: 像素距离
            
        返回:
            real_distance: 实际距离（米）
        """
        # 使用拟合的多项式进行转换
        real_distance = np.polyval(self.poly_coeffs, pixel_distance)
        return max(0, real_distance)  # 确保距离非负
    
    def calculate_queue_length(self, vehicle_positions, lane_start_point, lane_end_point):
        """
        计算排队长度
        
        参数:
            vehicle_positions: 车辆位置列表 [(x1,y1), (x2,y2), ...]
            lane_start_point: 车道起点坐标 (x, y)
            lane_end_point: 车道终点坐标 (x, y)
            
        返回:
            queue_length: 排队长度（米）
            queue_info: 详细信息字典
        """
        if not vehicle_positions:
            return 0.0, {
                'vehicle_count': 0,
                'queue_start': None,
                'queue_end': None,
                'pixel_length': 0
            }
        
        # 将车辆位置投影到车道线上
        lane_vector = np.array(lane_end_point) - np.array(lane_start_point)
        lane_length = np.linalg.norm(lane_vector)
        
        if lane_length == 0:
            return 0.0, {'vehicle_count': 0, 'queue_start': None, 'queue_end': None, 'pixel_length': 0}
        
        lane_unit = lane_vector / lane_length
        
        # 计算每辆车在车道上的投影位置
        projections = []
        for pos in vehicle_positions:
            pos_array = np.array(pos) - np.array(lane_start_point)
            projection = np.dot(pos_array, lane_unit)
            projections.append(projection)
        
        projections = np.array(projections)
        
        # 找到排队车辆的范围
        queue_start = np.min(projections)
        queue_end = np.max(projections)
        
        # 计算排队长度（像素）
        pixel_length = queue_end - queue_start
        
        # 转换为实际距离
        queue_length = self.pixel_to_real_distance(pixel_length)
        
        queue_info = {
            'vehicle_count': len(vehicle_positions),
            'queue_start': queue_start,
            'queue_end': queue_end,
            'pixel_length': pixel_length,
            'vehicle_positions': vehicle_positions
        }
        
        return queue_length, queue_info
    
    def calculate_queue_length_from_mask(self, binary_mask, lane_start_point, lane_end_point):
        """
        从二值掩码计算排队长度
        
        参数:
            binary_mask: 车辆检测的二值掩码 (numpy数组)
            lane_start_point: 车道起点坐标 (x, y)
            lane_end_point: 车道终点坐标 (x, y)
            
        返回:
            queue_length: 排队长度（米）
            queue_info: 详细信息字典
        """
        # 找到掩码中所有像素点的坐标
        vehicle_pixels = np.column_stack(np.where(binary_mask > 0))
        
        if len(vehicle_pixels) == 0:
            return 0.0, {
                'vehicle_count': 0,
                'queue_start': None,
                'queue_end': None,
                'pixel_length': 0
            }
        
        # 转换为(x, y)格式
        vehicle_positions = vehicle_pixels[:, [1, 0]]  # numpy是(row, col)，需要转换为(x, y)
        
        return self.calculate_queue_length(vehicle_positions, lane_start_point, lane_end_point)
    
    def calculate_density_based_queue(self, vehicle_count, avg_vehicle_length=5.0):
        """
        基于车辆密度估算排队长度
        
        参数:
            vehicle_count: 车辆数量
            avg_vehicle_length: 平均车辆长度（米），默认5米
            
        返回:
            estimated_queue_length: 估算的排队长度（米）
        """
        # 考虑车辆间距，假设平均间距为2米
        avg_gap = 2.0
        estimated_queue_length = vehicle_count * (avg_vehicle_length + avg_gap)
        
        return estimated_queue_length
    
    def visualize_queue(self, image, vehicle_positions, lane_start_point, lane_end_point, 
                       queue_length, queue_info, color=(0, 255, 0), thickness=2):
        """
        在图像上可视化排队情况
        
        参数:
            image: 输入图像
            vehicle_positions: 车辆位置列表
            lane_start_point: 车道起点
            lane_end_point: 车道终点
            queue_length: 排队长度
            queue_info: 排队信息
            color: 绘制颜色
            thickness: 线条粗细
            
        返回:
            annotated_image: 标注后的图像
        """
        annotated_image = image.copy()
        
        # 绘制车道线
        cv2.line(annotated_image, lane_start_point, lane_end_point, (255, 0, 0), thickness)
        
        # 绘制车辆位置
        for pos in vehicle_positions:
            cv2.circle(annotated_image, tuple(map(int, pos)), 5, color, -1)
        
        # 绘制排队范围
        if queue_info['vehicle_count'] > 0:
            # 计算排队范围的像素坐标
            lane_vector = np.array(lane_end_point) - np.array(lane_start_point)
            lane_unit = lane_vector / np.linalg.norm(lane_vector)
            
            queue_start_pixel = np.array(lane_start_point) + lane_unit * queue_info['queue_start']
            queue_end_pixel = np.array(lane_start_point) + lane_unit * queue_info['queue_end']
            
            # 绘制排队范围线
            cv2.line(annotated_image, 
                    tuple(map(int, queue_start_pixel)), 
                    tuple(map(int, queue_end_pixel)), 
                    (0, 0, 255), thickness + 2)
            
            # 添加文本标注
            text = f"排队长度: {queue_length:.2f}米"
            cv2.putText(annotated_image, text, 
                       tuple(map(int, queue_start_pixel)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            vehicle_text = f"车辆数: {queue_info['vehicle_count']}"
            cv2.putText(annotated_image, vehicle_text,
                       tuple(map(int, queue_start_pixel + np.array([0, 30]))),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return annotated_image


# 示例使用
if __name__ == "__main__":
    # 设置参考点（像素坐标）和对应的实际距离
    reference_points = [
        [100, 300],  # 起点
        [200, 250],  # 10米处
        [300, 200],  # 20米处
        [400, 150]   # 30米处
    ]
    real_world_distances = [0, 10, 20, 30]  # 对应的实际距离（米）
    
    # 创建计算器
    calculator = QueueLengthCalculator(reference_points, real_world_distances)
    
    # 模拟车辆位置
    vehicle_positions = [
        [150, 280],
        [180, 265],
        [220, 245],
        [280, 210],
        [320, 190]
    ]
    
    # 车道起终点
    lane_start = [100, 300]
    lane_end = [400, 150]
    
    # 计算排队长度
    queue_length, queue_info = calculator.calculate_queue_length(
        vehicle_positions, lane_start, lane_end
    )
    
    print(f"排队长度: {queue_length:.2f}米")
    print(f"车辆数量: {queue_info['vehicle_count']}")
    print(f"像素长度: {queue_info['pixel_length']:.2f}像素")
    
    # 基于密度的估算
    estimated_length = calculator.calculate_density_based_queue(5)
    print(f"基于密度的估算排队长度: {estimated_length:.2f}米")