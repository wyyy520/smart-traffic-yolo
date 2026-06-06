import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Tuple

class NonlinearTrafficSignalController:
    def __init__(self, 
                 min_green_time=15, 
                 max_green_time=120,
                 beta_min=0.1, 
                 beta_max=0.9,
                 emergency_priority_factor=3.0):
        """
        非线性交通信号控制器
        
        参数:
            min_green_time: 最小绿灯时间（秒）
            max_green_time: 最大绿灯时间（秒）
            beta_min: 拥堵调节因子最小值
            beta_max: 拥堵调节因子最大值
            emergency_priority_factor: 紧急车辆优先因子
        """
        self.min_green_time = min_green_time
        self.max_green_time = max_green_time
        self.beta_min = beta_min
        self.beta_max = beta_max
        self.emergency_priority_factor = emergency_priority_factor
        
        # 历史数据用于平滑
        self.historical_green_times = []
        self.historical_betas = []
        
        # 天气影响系数映射表
        self.weather_factors = {
            'sunny': 1.0,      # 晴天：无影响
            'cloudy': 1.0,     # 多云：无影响
            'light_rain': 1.1, # 小雨：增加10%
            'heavy_rain': 1.2, # 大雨：增加20%
            'light_snow': 1.2, # 小雪：增加20%
            'heavy_snow': 1.3, # 大雪：增加30%
            'fog': 1.4,        # 雾：增加40%
            'sleet': 1.35,     # 雨夹雪：增加35%
            'hail': 1.3,       # 冰雹：增加30%
            'default': 1.0     # 默认：无影响
        }
        
    def get_weather_factor(self, weather_type):
        """
        获取天气影响因子
        
        雨雪雾天气会增加通行时间，因为：
        - 雨天路面湿滑，车辆制动距离增加
        - 雪天路面结冰，能见度降低
        - 雾天能见度差，车辆行驶速度降低
        
        参数:
            weather_type: 天气类型字符串
                可选值: 'sunny', 'cloudy', 'light_rain', 'heavy_rain',
                        'light_snow', 'heavy_snow', 'fog', 'sleet', 'hail'
            
        返回:
            weather_factor: 天气影响因子 (1.0-1.4)
        """
        # 尝试精确匹配
        if weather_type in self.weather_factors:
            return self.weather_factors[weather_type]
        
        # 模糊匹配：检查天气描述中是否包含关键词
        weather_lower = weather_type.lower()
        if '雨' in weather_lower or 'rain' in weather_lower:
            if '大' in weather_lower or 'heavy' in weather_lower:
                return self.weather_factors['heavy_rain']
            else:
                return self.weather_factors['light_rain']
        elif '雪' in weather_lower or 'snow' in weather_lower:
            if '大' in weather_lower or 'heavy' in weather_lower:
                return self.weather_factors['heavy_snow']
            else:
                return self.weather_factors['light_snow']
        elif '雾' in weather_lower or 'fog' in weather_lower:
            return self.weather_factors['fog']
        elif '夹雪' in weather_lower or 'sleet' in weather_lower:
            return self.weather_factors['sleet']
        elif '冰雹' in weather_lower or 'hail' in weather_lower:
            return self.weather_factors['hail']
        
        # 默认返回1.0（无影响）
        return self.weather_factors['default']
    
    def calculate_congestion_level(self, queue_length, vehicle_count, predicted_flow):
        """
        计算拥堵等级 (0-1)
        
        参数:
            queue_length: 排队长度（米）
            vehicle_count: 车辆数量
            predicted_flow: 预测车流量
            
        返回:
            congestion_level: 拥堵等级 (0-1)
        """
        # 归一化各指标
        normalized_queue = min(queue_length / 200.0, 1.0)  # 假设200米为最大排队长度
        normalized_count = min(vehicle_count / 50.0, 1.0)   # 假设50辆车为最大车辆数
        normalized_flow = min(predicted_flow / 100.0, 1.0)  # 假设100为最大车流量
        
        # 使用加权组合计算拥堵等级
        weights = [0.4, 0.3, 0.3]  # 排队长度、车辆数、预测流量的权重
        congestion_level = sum(w * v for w, v in zip(weights, 
                            [normalized_queue, normalized_count, normalized_flow]))
        
        return congestion_level
    
    def calculate_beta(self, congestion_level, emergency_detected=False):
        """
        计算非线性拥堵调节因子β
        
        β的作用：
        - 防止通行时间过大：当拥堵严重时，β会限制时间增长
        - 防止通行时间过小：当拥堵轻微时，β会保证最小通行时间
        - 防止突变：使用平滑函数避免时间突变
        
        参数:
            congestion_level: 拥堵等级 (0-1)
            emergency_detected: 是否检测到紧急车辆
            
        返回:
            beta: 拥堵调节因子
        """
        if emergency_detected:
            # 紧急车辆情况下，使用较大的β值以快速响应
            beta = self.beta_max
        else:
            # 使用Sigmoid函数实现平滑的非线性映射
            # β = β_min + (β_max - β_min) * sigmoid(k * (congestion - threshold))
            k = 6  # 控制曲线陡峭程度
            threshold = 0.5  # 拥堵阈值
            
            sigmoid = 1 / (1 + np.exp(-k * (congestion_level - threshold)))
            beta = self.beta_min + (self.beta_max - self.beta_min) * sigmoid
        
        # 记录历史β值用于平滑
        self.historical_betas.append(beta)
        if len(self.historical_betas) > 10:
            self.historical_betas.pop(0)
        
        # 使用移动平均平滑β值
        if len(self.historical_betas) >= 3:
            beta = np.mean(self.historical_betas[-3:])
        
        return beta
    
    def nonlinear_green_time_model(self, base_time, beta, queue_length, predicted_flow):
        """
        非线性绿灯时间模型
        
        使用非线性函数计算绿灯时间：
        T_green = base_time * (1 + β * f(queue, flow))
        
        其中f(queue, flow)是非线性函数，考虑排队长度和预测流量
        
        参数:
            base_time: 基础绿灯时间
            beta: 拥堵调节因子
            queue_length: 排队长度
            predicted_flow: 预测车流量
            
        返回:
            green_time: 计算的绿灯时间
        """
        # 非线性函数：使用对数函数避免线性增长
        # f(queue, flow) = log(1 + α1*queue + α2*flow)
        alpha1 = 0.05  # 排队长度系数
        alpha2 = 0.1   # 预测流量系数
        
        nonlinear_factor = np.log1p(alpha1 * queue_length + alpha2 * predicted_flow)
        
        # 计算绿灯时间
        green_time = base_time * (1 + beta * nonlinear_factor)
        
        # 限制在合理范围内
        green_time = np.clip(green_time, self.min_green_time, self.max_green_time)
        
        return green_time
    
    def smooth_green_time(self, current_green_time, previous_green_time=None):
        """
        平滑绿灯时间，防止突变
        
        参数:
            current_green_time: 当前计算的绿灯时间
            previous_green_time: 之前的绿灯时间
            
        返回:
            smoothed_time: 平滑后的绿灯时间
        """
        if previous_green_time is None:
            return current_green_time
        
        # 使用指数移动平均
        alpha = 0.7  # 平滑因子
        smoothed_time = alpha * current_green_time + (1 - alpha) * previous_green_time
        
        # 确保在合理范围内
        smoothed_time = np.clip(smoothed_time, self.min_green_time, self.max_green_time)
        
        return smoothed_time
    
    def optimize_green_time(self, 
                           queue_length, 
                           vehicle_count, 
                           predicted_flow, 
                           emergency_detected=False,
                           current_phase_time=None,
                           weather_type='sunny'):
        """
        优化绿灯时间（主函数）
        
        参数:
            queue_length: 排队长度（米）
            vehicle_count: 车辆数量
            predicted_flow: 预测车流量
            emergency_detected: 是否检测到紧急车辆
            current_phase_time: 当前相位时间
            weather_type: 天气类型（影响通行时间）
            
        返回:
            result: 包含优化结果的字典
        """
        # 计算拥堵等级
        congestion_level = self.calculate_congestion_level(queue_length, vehicle_count, predicted_flow)
        
        # 计算拥堵调节因子β
        beta = self.calculate_beta(congestion_level, emergency_detected)
        
        # 获取天气影响因子
        weather_factor = self.get_weather_factor(weather_type)
        
        # 基础绿灯时间（根据当前相位时间或默认值）
        if current_phase_time is not None:
            base_time = current_phase_time
        else:
            base_time = 30  # 默认30秒
        
        # 如果检测到紧急车辆，大幅增加绿灯时间
        if emergency_detected:
            base_time *= self.emergency_priority_factor
        
        # 使用非线性模型计算绿灯时间（考虑天气影响）
        green_time = self.nonlinear_green_time_model(base_time, beta, queue_length, predicted_flow)
        
        # 应用天气影响因子（雨雪雾天气增加通行时间）
        green_time *= weather_factor
        
        # 平滑绿灯时间
        previous_time = self.historical_green_times[-1] if self.historical_green_times else None
        smoothed_time = self.smooth_green_time(green_time, previous_time)
        
        # 记录历史数据
        self.historical_green_times.append(smoothed_time)
        if len(self.historical_green_times) > 10:
            self.historical_green_times.pop(0)
        
        result = {
            'green_time': smoothed_time,
            'congestion_level': congestion_level,
            'beta': beta,
            'emergency_mode': emergency_detected,
            'queue_length': queue_length,
            'vehicle_count': vehicle_count,
            'predicted_flow': predicted_flow,
            'weather_type': weather_type,
            'weather_factor': weather_factor
        }
        
        return result
    
    def multi_phase_optimization(self, 
                                lanes_data: List[Dict],
                                emergency_lanes: List[int] = None,
                                weather_type='sunny'):
        """
        多相位优化
        
        参数:
            lanes_data: 各车道数据列表
                [{'queue_length': x, 'vehicle_count': y, 'predicted_flow': z}, ...]
            emergency_lanes: 检测到紧急车辆的车道索引列表
            weather_type: 天气类型（影响所有车道的通行时间）
            
        返回:
            phase_schedule: 各相位的绿灯时间安排
        """
        if emergency_lanes is None:
            emergency_lanes = []
        
        phase_schedule = []
        
        for i, lane_data in enumerate(lanes_data):
            is_emergency = i in emergency_lanes
            
            result = self.optimize_green_time(
                queue_length=lane_data['queue_length'],
                vehicle_count=lane_data['vehicle_count'],
                predicted_flow=lane_data['predicted_flow'],
                emergency_detected=is_emergency,
                weather_type=weather_type
            )
            
            phase_schedule.append({
                'phase': i,
                'green_time': result['green_time'],
                'emergency_mode': result['emergency_mode'],
                'beta': result['beta']
            })
        
        # 如果有紧急车辆，调整其他相位时间
        if emergency_lanes:
            total_normal_time = sum(p['green_time'] for p in phase_schedule 
                                  if not p['emergency_mode'])
            
            if total_normal_time > 0:
                # 减少非紧急车道的绿灯时间
                reduction_factor = 0.6  # 减少到60%
                for phase in phase_schedule:
                    if not phase['emergency_mode']:
                        phase['green_time'] = max(
                            self.min_green_time,
                            phase['green_time'] * reduction_factor
                        )
        
        return phase_schedule
    
    def reset_history(self):
        """
        重置历史数据
        """
        self.historical_green_times = []
        self.historical_betas = []


# 示例使用
if __name__ == "__main__":
    # 创建控制器
    controller = NonlinearTrafficSignalController(
        min_green_time=15,
        max_green_time=120,
        beta_min=0.1,
        beta_max=0.9
    )
    
    # 模拟单车道场景
    print("=== 单车道优化示例 ===")
    result = controller.optimize_green_time(
        queue_length=50,      # 50米排队
        vehicle_count=12,     # 12辆车
        predicted_flow=45,    # 预测车流量45
        emergency_detected=False
    )
    
    print(f"优化绿灯时间: {result['green_time']:.1f}秒")
    print(f"拥堵等级: {result['congestion_level']:.2f}")
    print(f"调节因子β: {result['beta']:.3f}")
    
    # 紧急车辆场景
    print("\n=== 紧急车辆场景 ===")
    emergency_result = controller.optimize_green_time(
        queue_length=30,
        vehicle_count=8,
        predicted_flow=35,
        emergency_detected=True
    )
    
    print(f"紧急车辆优化绿灯时间: {emergency_result['green_time']:.1f}秒")
    print(f"紧急模式: {emergency_result['emergency_mode']}")
    print(f"调节因子β: {emergency_result['beta']:.3f}")
    
    # 天气影响测试
    print("\n=== 天气影响测试 ===")
    controller.reset_history()
    
    weather_types = ['sunny', 'light_rain', 'heavy_rain', 'light_snow', 'heavy_snow', 'fog']
    for weather in weather_types:
        result = controller.optimize_green_time(
            queue_length=50,
            vehicle_count=12,
            predicted_flow=45,
            emergency_detected=False,
            weather_type=weather
        )
        print(f"{weather}: 绿灯时间={result['green_time']:.1f}秒, 天气因子={result['weather_factor']}")
    
    # 多车道场景
    print("\n=== 多车道优化示例 ===")
    lanes_data = [
        {'queue_length': 45, 'vehicle_count': 10, 'predicted_flow': 40},
        {'queue_length': 80, 'vehicle_count': 18, 'predicted_flow': 65},
        {'queue_length': 25, 'vehicle_count': 6, 'predicted_flow': 25},
        {'queue_length': 60, 'vehicle_count': 14, 'predicted_flow': 50}
    ]
    
    # 假设第2车道有紧急车辆，且天气为大雾
    schedule = controller.multi_phase_optimization(lanes_data, emergency_lanes=[1], weather_type='fog')
    
    print("各相位绿灯时间安排(大雾天气):")
    for phase in schedule:
        emergency_flag = " [紧急]" if phase['emergency_mode'] else ""
        print(f"相位{phase['phase']}: {phase['green_time']:.1f}秒{emergency_flag} (β={phase['beta']:.3f})")
    
    # 测试时间序列平滑
    print("\n=== 时间序列平滑测试 ===")
    controller.reset_history()
    
    for t in range(5):
        result = controller.optimize_green_time(
            queue_length=30 + t * 10,
            vehicle_count=8 + t * 2,
            predicted_flow=35 + t * 5,
            emergency_detected=False
        )
        print(f"时间步{t}: 绿灯时间={result['green_time']:.1f}秒, "
              f"拥堵等级={result['congestion_level']:.2f}, β={result['beta']:.3f}")