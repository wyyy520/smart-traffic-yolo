import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import joblib
import os

class TrafficFlowPredictor:
    def __init__(self, look_back=10, lstm_units=50, dropout_rate=0.2):
        """
        LSTM车流预测器
        
        参数:
            look_back: 历史时间步长
            lstm_units: LSTM隐藏单元数
            dropout_rate: Dropout比率
        """
        self.look_back = look_back
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
    def prepare_data(self, data):
        """
        准备训练数据
        
        参数:
            data: 车流量数据，格式为DataFrame或数组，包含时间戳和车流量
            
        返回:
            X, y: 训练数据和标签
        """
        if isinstance(data, pd.DataFrame):
            traffic_data = data['traffic_flow'].values.reshape(-1, 1)
        else:
            traffic_data = np.array(data).reshape(-1, 1)
        
        # 数据归一化
        scaled_data = self.scaler.fit_transform(traffic_data)
        
        X, y = [], []
        for i in range(len(scaled_data) - self.look_back):
            X.append(scaled_data[i:i + self.look_back, 0])
            y.append(scaled_data[i + self.look_back, 0])
        
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape):
        """
        构建LSTM模型
        
        参数:
            input_shape: 输入数据形状 (look_back, 1)
        """
        model = Sequential([
            LSTM(self.lstm_units, return_sequences=True, input_shape=input_shape),
            Dropout(self.dropout_rate),
            LSTM(self.lstm_units, return_sequences=False),
            Dropout(self.dropout_rate),
            Dense(25, activation='relu'),
            Dense(1, activation='linear')
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        self.model = model
        return model
    
    def train(self, data, epochs=100, batch_size=32, validation_split=0.2):
        """
        训练模型
        
        参数:
            data: 训练数据
            epochs: 训练轮数
            batch_size: 批次大小
            validation_split: 验证集比例
        """
        X, y = self.prepare_data(data)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        if self.model is None:
            self.build_model((X.shape[1], X.shape[2]))
        
        # 早停策略
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stopping],
            verbose=1
        )
        
        return history
    
    def predict(self, historical_data, steps_ahead=1):
        """
        预测未来车流量
        
        参数:
            historical_data: 历史车流数据
            steps_ahead: 预测步数
            
        返回:
            predictions: 预测结果
        """
        if len(historical_data) < self.look_back:
            raise ValueError(f"历史数据长度不足，需要至少{self.look_back}个数据点")
        
        # 取最后look_back个数据点
        recent_data = historical_data[-self.look_back:]
        scaled_data = self.scaler.transform(recent_data.reshape(-1, 1))
        
        predictions = []
        current_input = scaled_data.copy()
        
        for _ in range(steps_ahead):
            X = current_input.reshape(1, self.look_back, 1)
            pred_scaled = self.model.predict(X, verbose=0)
            pred = self.scaler.inverse_transform(pred_scaled)
            predictions.append(pred[0, 0])
            
            # 更新输入
            current_input = np.roll(current_data, -1)
            current_input[-1] = pred_scaled[0, 0]
        
        return np.array(predictions)
    
    def save_model(self, model_path='traffic_lstm_model.h5', scaler_path='traffic_scaler.pkl'):
        """
        保存模型和缩放器
        """
        if self.model is not None:
            self.model.save(model_path)
            joblib.dump(self.scaler, scaler_path)
            print(f"模型已保存到 {model_path}")
            print(f"缩放器已保存到 {scaler_path}")
    
    def load_model(self, model_path='traffic_lstm_model.h5', scaler_path='traffic_scaler.pkl'):
        """
        加载模型和缩放器
        """
        from tensorflow.keras.models import load_model
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.model = load_model(model_path)
            self.scaler = joblib.load(scaler_path)
            print(f"模型已从 {model_path} 加载")
            print(f"缩放器已从 {scaler_path} 加载")
            return True
        else:
            print("模型文件不存在")
            return False


# 示例使用
if __name__ == "__main__":
    # 生成模拟数据
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='5min')
    base_traffic = 50 + 30 * np.sin(np.arange(1000) * 2 * np.pi / 96)  # 日周期
    noise = np.random.normal(0, 10, 1000)
    traffic_flow = base_traffic + noise
    traffic_flow = np.maximum(traffic_flow, 0)  # 确保非负
    
    data = pd.DataFrame({
        'timestamp': dates,
        'traffic_flow': traffic_flow
    })
    
    # 创建预测器
    predictor = TrafficFlowPredictor(look_back=12, lstm_units=64)
    
    # 训练模型
    print("开始训练LSTM模型...")
    history = predictor.train(data, epochs=50, batch_size=32)
    
    # 预测
    print("\n预测未来30分钟的车流量...")
    predictions = predictor.predict(data['traffic_flow'].values, steps_ahead=6)
    
    print(f"预测结果: {predictions}")
    
    # 保存模型
    predictor.save_model()