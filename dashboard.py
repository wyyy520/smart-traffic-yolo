# Streamlit 可视化 Dashboard
# 智慧交通数据分析平台

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json

# 页面配置
st.set_page_config(
    page_title="智慧交通 Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 模拟数据生成
def generate_mock_data():
    """生成模拟数据"""
    hours = 24
    data = []
    
    for hour in range(hours):
        # 模拟早晚高峰
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_flow = random.randint(200, 350)
        elif 0 <= hour <= 5:
            base_flow = random.randint(20, 80)
        else:
            base_flow = random.randint(80, 180)
        
        data.append({
            'hour': f"{hour:02d}:00",
            'total_vehicles': base_flow,
            'cars': int(base_flow * 0.7),
            'suvs': int(base_flow * 0.2),
            'trucks': int(base_flow * 0.08),
            'others': int(base_flow * 0.02),
            'emergency_vehicles': random.randint(0, 5),
            'avg_speed': random.randint(20, 60),
            'congestion_level': random.choice(['low', 'medium', 'high']),
            'queue_length': random.randint(0, 150),
            'weather': random.choice(['sunny', 'cloudy', 'rainy', 'foggy']),
            'temperature': random.randint(15, 35)
        })
    
    return pd.DataFrame(data)

def generate_hourly_data(days=7):
    """生成多日数据"""
    data = []
    today = datetime.now().date()
    
    for day_offset in range(days):
        date = today - timedelta(days=day_offset)
        for hour in range(24):
            base_flow = random.randint(80, 250)
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                base_flow = random.randint(200, 350)
            
            data.append({
                'date': str(date),
                'hour': hour,
                'total_vehicles': base_flow,
                'emergency_vehicles': random.randint(0, 8),
                'avg_speed': random.randint(25, 55),
                'congestion_level': random.choice(['low', 'medium', 'high'])
            })
    
    return pd.DataFrame(data)

def generate_realtime_data():
    """生成实时数据"""
    return {
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_vehicles': random.randint(50, 300),
        'emergency_vehicles': random.randint(0, 3),
        'avg_speed': random.randint(20, 60),
        'congestion_level': random.choice(['畅通', '缓行', '拥堵']),
        'queue_length': random.randint(0, 120),
        'weather': random.choice(['晴天', '多云', '小雨', '雾']),
        'temperature': random.randint(18, 32),
        'humidity': random.randint(40, 85),
        'wind_speed': random.randint(0, 15)
    }

# 主页面
def main():
    # 标题
    st.title("🚦 智慧交通数据分析平台")
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.sidebar.header("控制面板")
        
        # 时间范围选择
        time_range = st.selectbox(
            "时间范围",
            ["今日", "近7日", "近30日"]
        )
        
        # 数据刷新
        refresh_interval = st.slider(
            "数据刷新间隔(秒)",
            min_value=5,
            max_value=60,
            value=10
        )
        
        # 导出数据
        if st.button("导出数据"):
            st.success("数据导出成功！")
    
    # 实时指标卡片
    st.subheader("实时监控")
    realtime_data = generate_realtime_data()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="当前车流量",
            value=f"{realtime_data['total_vehicles']} 辆/小时",
            delta=f"{random.randint(-20, 20)}"
        )
    
    with col2:
        st.metric(
            label="紧急车辆",
            value=f"{realtime_data['emergency_vehicles']} 辆",
            delta_color="off"
        )
    
    with col3:
        st.metric(
            label="平均车速",
            value=f"{realtime_data['avg_speed']} km/h",
            delta=f"{random.randint(-5, 5)}"
        )
    
    with col4:
        st.metric(
            label="排队长度",
            value=f"{realtime_data['queue_length']} 米",
            delta_color="inverse" if realtime_data['queue_length'] > 80 else "normal"
        )
    
    with col5:
        st.metric(
            label="拥堵状态",
            value=realtime_data['congestion_level'],
            delta_color="off"
        )
    
    # 天气信息
    st.markdown("---")
    st.subheader("🌤️ 当前天气")
    weather_col1, weather_col2, weather_col3, weather_col4 = st.columns(4)
    
    with weather_col1:
        st.info(f"**天气状况**: {realtime_data['weather']}")
    with weather_col2:
        st.info(f"**温度**: {realtime_data['temperature']}°C")
    with weather_col3:
        st.info(f"**湿度**: {realtime_data['humidity']}%")
    with weather_col4:
        st.info(f"**风速**: {realtime_data['wind_speed']} m/s")
    
    # 24小时流量趋势
    st.markdown("---")
    st.subheader("📈 24小时流量趋势")
    df_24h = generate_mock_data()
    
    fig = px.line(
        df_24h,
        x='hour',
        y=['total_vehicles', 'cars', 'suvs', 'trucks'],
        title='车辆流量趋势',
        labels={'value': '车辆数', 'variable': '车辆类型'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 车辆类型分布
    st.markdown("---")
    st.subheader("🚗 车辆类型分布")
    vehicle_types = ['轿车', 'SUV', '货车', '摩托车', '其他']
    vehicle_counts = [452, 189, 76, 34, 23]
    
    fig_pie = px.pie(
        values=vehicle_counts,
        names=vehicle_types,
        title='车辆类型占比',
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # 周对比分析
    st.markdown("---")
    st.subheader("📊 周流量对比")
    df_weekly = generate_hourly_data(days=7)
    
    fig_weekly = px.line(
        df_weekly,
        x='hour',
        y='total_vehicles',
        color='date',
        title='每日流量对比',
        labels={'total_vehicles': '车辆数', 'hour': '时段'},
        height=400
    )
    st.plotly_chart(fig_weekly, use_container_width=True)
    
    # 紧急车辆统计
    st.markdown("---")
    st.subheader("🚨 紧急车辆响应")
    
    emergency_data = {
        '日期': ['06-01', '06-02', '06-03', '06-04', '06-05', '06-06'],
        '救护车': [12, 8, 15, 10, 14, 9],
        '消防车': [3, 5, 2, 4, 1, 3],
        '警车': [8, 6, 10, 7, 9, 11]
    }
    df_emergency = pd.DataFrame(emergency_data)
    
    fig_emergency = px.bar(
        df_emergency,
        x='日期',
        y=['救护车', '消防车', '警车'],
        title='紧急车辆出动统计',
        labels={'value': '数量', 'variable': '类型'},
        barmode='group',
        height=400
    )
    st.plotly_chart(fig_emergency, use_container_width=True)
    
    # 拥堵分析
    st.markdown("---")
    st.subheader("📉 拥堵时段分析")
    congestion_data = []
    hours = ['07:00', '08:00', '09:00', '17:00', '18:00', '19:00']
    
    for hour in hours:
        congestion_data.append({
            '时段': hour,
            '平均排队长度': random.randint(80, 150),
            '平均车速': random.randint(15, 35),
            '拥堵指数': random.randint(70, 95)
        })
    
    df_congestion = pd.DataFrame(congestion_data)
    
    col_congestion1, col_congestion2 = st.columns(2)
    
    with col_congestion1:
        fig_congestion = px.bar(
            df_congestion,
            x='时段',
            y='平均排队长度',
            title='高峰时段排队长度',
            color='拥堵指数',
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig_congestion, use_container_width=True)
    
    with col_congestion2:
        fig_speed = px.line(
            df_congestion,
            x='时段',
            y='平均车速',
            title='高峰时段平均车速',
            markers=True,
            color_discrete_sequence=['red']
        )
        st.plotly_chart(fig_speed, use_container_width=True)
    
    # 天气影响分析
    st.markdown("---")
    st.subheader("🌧️ 天气对交通的影响")
    weather_effect = {
        '天气': ['晴天', '多云', '小雨', '大雨', '雾', '雪'],
        '平均车速': [45, 42, 35, 28, 25, 22],
        '拥堵概率': [20, 25, 45, 70, 75, 80],
        '通行时间增加': [0, 5, 15, 30, 40, 45]
    }
    df_weather = pd.DataFrame(weather_effect)
    
    fig_weather = px.scatter(
        df_weather,
        x='平均车速',
        y='拥堵概率',
        size='通行时间增加',
        color='天气',
        title='天气与交通状况关系',
        size_max=60,
        height=400
    )
    st.plotly_chart(fig_weather, use_container_width=True)
    
    # 实时监控视频区域（模拟）
    st.markdown("---")
    st.subheader("🎥 实时监控")
    cols = st.columns(3)
    
    with cols[0]:
        st.image(
            "https://picsum.photos/400/300?random=1",
            caption="摄像头1 - 主干道",
            use_column_width=True
        )
    
    with cols[1]:
        st.image(
            "https://picsum.photos/400/300?random=2",
            caption="摄像头2 - 交叉口",
            use_column_width=True
        )
    
    with cols[2]:
        st.image(
            "https://picsum.photos/400/300?random=3",
            caption="摄像头3 - 高速入口",
            use_column_width=True
        )
    
    # 数据表格
    st.markdown("---")
    st.subheader("📋 详细数据")
    st.dataframe(df_24h, use_container_width=True)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
        **智慧交通数据分析平台** - 基于 YOLO + LSTM 的智能交通管理系统
        
        *数据每 {} 秒自动刷新*
    """.format(refresh_interval))

if __name__ == "__main__":
    main()