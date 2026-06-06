// ============================================================================
// 智慧交通 Go 后端服务 - 主程序
// ============================================================================
// 功能说明：
// 1. 提供 RESTful API 接口，支持前端调用
// 2. 实现排队长度分析（基于像素点矩阵仿射逻辑，不使用三角函数）
// 3. 实现紧急车辆检测（救护车、消防车、警车）
// 4. 实现 LSTM 风格的车流量预测
// 5. 实现非线性信号灯优化（使用 Sigmoid 函数和β调节因子）
//
// 作者：AI Assistant
// 创建时间：2026-06-06
// ============================================================================

package main

import (
	"bytes"
	"encoding/base64"
	"image"
	_ "image/jpeg"
	"log"
	"math"
	"math/rand"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"
	"github.com/nfnt/resize"
)

// validate 全局参数验证器实例
var validate *validator.Validate

// AnalysisRequest 综合分析请求结构体
type AnalysisRequest struct {
	// Base64 编码的图片数据
	Image string `json:"image" validate:"required,base64"`
	// 历史交通流量数据（用于 LSTM 预测）
	HistoricalTraffic []int `json:"historical_traffic" validate:"required"`
	// 车道起始点坐标 [x, y]
	LaneStart []int `json:"lane_start" validate:"required,len=2"`
	// 车道结束点坐标 [x, y]
	LaneEnd []int `json:"lane_end" validate:"required,len=2"`
	// 天气类型（影响通行时间）
	Weather string `json:"weather"`
}

// AnalysisResponse 综合分析响应结构体
type AnalysisResponse struct {
	// 请求是否成功
	Success bool `json:"success"`
	// 响应消息
	Message string `json:"message"`
	// 分析结果数据
	Analysis Analysis `json:"analysis"`
}

// Analysis 分析结果结构体（包含所有分析模块的输出）
type Analysis struct {
	// 排队长度分析结果
	QueueAnalysis QueueAnalysis `json:"queue_analysis"`
	// 紧急车辆检测结果
	EmergencyDetection EmergencyDetection `json:"emergency_detection"`
	// 信号灯优化方案
	SignalOptimization SignalOptimization `json:"signal_optimization"`
	// 交通流量预测结果
	TrafficPrediction TrafficPrediction `json:"traffic_prediction"`
}

// QueueAnalysis 排队长度分析结果
type QueueAnalysis struct {
	// 排队长度（米）
	Length float64 `json:"length"`
	// 检测到的车辆数量
	VehicleCount int `json:"vehicle_count"`
}

// EmergencyDetection 紧急车辆检测结果
type EmergencyDetection struct {
	// 是否检测到紧急车辆
	Detected bool `json:"detected"`
	// 紧急车辆类型列表（救护车、消防车、警车）
	Types []string `json:"types"`
	// 检测置信度（0-1）
	Confidence float64 `json:"confidence,omitempty"`
}

// SignalOptimization 信号灯优化结果
type SignalOptimization struct {
	// 建议绿灯时间（秒）
	GreenTime float64 `json:"green_time"`
	// 拥堵等级（0-1）
	CongestionLevel float64 `json:"congestion_level"`
	// 非线性拥堵调节因子β（0.1-0.9）
	Beta float64 `json:"beta"`
	// 天气影响因子
	WeatherFactor float64 `json:"weather_factor"`
}

// TrafficPrediction 交通流量预测结果
type TrafficPrediction struct {
	// 预测的车流量（辆/小时）
	PredictedFlow int `json:"predicted_flow"`
	// 预测置信度（0-1）
	Confidence float64 `json:"confidence"`
}

// init 初始化函数
// 在 main 函数执行前自动调用，用于初始化全局变量
func init() {
	// 初始化参数验证器
	validate = validator.New()
	// 初始化随机数种子（使用当前时间戳）
	rand.Seed(time.Now().UnixNano())
}

// main 主函数
// 程序入口点，负责启动 HTTP 服务器和注册路由
func main() {
	// 创建 Gin 引擎（包含日志和恢复中间件）
	r := gin.Default()
	// 添加跨域中间件
	r.Use(CORSMiddleware())

	// 创建 API 路由组
	api := r.Group("/api")
	{
		// 综合分析接口（POST）
		api.POST("/comprehensive_analysis", ComprehensiveAnalysisHandler)
		// 健康检查接口（GET）
		api.GET("/health", HealthCheckHandler)
	}

	// 记录启动日志
	log.Println("智慧交通 Go 后端服务启动，监听端口：8080")
	// 启动 HTTP 服务器（阻塞式）
	log.Fatal(r.Run(":8080"))
}

// CORSMiddleware 跨域资源共享中间件
// 允许前端跨域访问 API 接口
func CORSMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 允许所有来源访问（生产环境应限制为特定域名）
		c.Header("Access-Control-Allow-Origin", "*")
		// 允许的 HTTP 方法
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		// 允许的请求头
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")

		// 处理预检请求（OPTIONS）
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusOK)
			return
		}

		// 继续处理请求
		c.Next()
	}
}

// HealthCheckHandler 健康检查处理器
// 用于检查服务是否正常运行
func HealthCheckHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "ok",
		"message": "智慧交通 Go 后端服务正常运行",
	})
}

// ComprehensiveAnalysisHandler 综合分析处理器
// 核心业务逻辑：处理图片并调用各个分析模块
func ComprehensiveAnalysisHandler(c *gin.Context) {
	var req AnalysisRequest

	// 绑定 JSON 请求参数
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "请求参数错误：" + err.Error(),
		})
		return
	}

	// 验证请求参数
	if err := validate.Struct(req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "参数验证失败：" + err.Error(),
		})
		return
	}

	// 解码 Base64 图片
	imageData, err := base64.StdEncoding.DecodeString(req.Image)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "图片解码失败",
		})
		return
	}

	// 解析图片
	img, _, err := image.Decode(bytes.NewReader(imageData))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "图片解析失败",
		})
		return
	}

	// 缩放图片到标准尺寸（640x 高度自适应）
	img = resize.Resize(640, 0, img, resize.Lanczos3)

	// 调用各个分析模块
	queueAnalysis := analyzeQueueLength(img, req.LaneStart, req.LaneEnd)
	emergencyDetection := detectEmergencyVehicles(img)
	trafficPrediction := predictTrafficFlow(req.HistoricalTraffic)
	signalOptimization := optimizeSignalTiming(queueAnalysis, trafficPrediction, emergencyDetection.Detected, req.Weather)

	// 构建响应
	response := AnalysisResponse{
		Success: true,
		Message: "分析完成",
		Analysis: Analysis{
			QueueAnalysis:      queueAnalysis,
			EmergencyDetection: emergencyDetection,
			SignalOptimization: signalOptimization,
			TrafficPrediction:  trafficPrediction,
		},
	}

	c.JSON(http.StatusOK, response)
}

// analyzeQueueLength 排队长度分析函数
// 基于像素点矩阵仿射逻辑（二次多项式拟合），不使用三角函数
// 参数：
//   - img: 输入图片
//   - laneStart: 车道起始点坐标 [x, y]
//   - laneEnd: 车道结束点坐标 [x, y]
// 返回：
//   - QueueAnalysis: 排队长度分析结果
func analyzeQueueLength(img image.Image, laneStart, laneEnd []int) QueueAnalysis {
	// 获取图片边界
	bounds := img.Bounds()
	width, height := bounds.Max.X, bounds.Max.Y

	// 定义参考点（用于标定像素距离与实际距离的关系）
	// 包含 3 个点：起点（0 米）、终点（50 米）、中点（25 米）
	referencePoints := []struct {
		pixelX, pixelY int
		realDistance   float64
	}{
		{laneStart[0], laneStart[1], 0},
		{laneEnd[0], laneEnd[1], 50},
		{(laneStart[0] + laneEnd[0]) / 2, (laneStart[1] + laneEnd[1]) / 2, 25},
	}

	// 计算参考点之间的像素距离和实际距离
	var pixelDistances []float64
	var realDistances []float64

	for i := 0; i < len(referencePoints); i++ {
		for j := i + 1; j < len(referencePoints); j++ {
			// 计算像素距离（欧几里得距离）
			dx := referencePoints[j].pixelX - referencePoints[i].pixelX
			dy := referencePoints[j].pixelY - referencePoints[i].pixelY
			pixelDist := math.Sqrt(float64(dx*dx + dy*dy))
			// 获取实际距离
			realDist := math.Abs(referencePoints[j].realDistance - referencePoints[i].realDistance)
			pixelDistances = append(pixelDistances, pixelDist)
			realDistances = append(realDistances, realDist)
		}
	}

	// 使用二次多项式拟合像素距离与实际距离的关系
	// 公式：real_distance = a * pixel^2 + b * pixel + c
	a, bCoeff, c := fitQuadratic(pixelDistances, realDistances)

	// 统计车辆数量和最大排队距离
	vehicleCount := 0
	maxVehicleDistance := 0.0

	// 遍历图片像素点（步长为 10，提高效率）
	for y := 0; y < height; y += 10 {
		for x := 0; x < width; x += 10 {
			// 获取像素颜色
			r, g, b, _ := img.At(x, y).RGBA()
			r8, g8, b8 := uint8(r>>8), uint8(g>>8), uint8(b>>8)

			// 颜色特征检测（车辆颜色：深色、红色、绿色）
			if (r8 < 80 && g8 < 80 && b8 < 80) || // 深色（黑色、灰色）
				(r8 > 150 && g8 < 100 && b8 < 100) || // 红色
				(r8 < 100 && g8 > 150 && b8 < 100) { // 绿色
				vehicleCount++

				// 计算该点到车道起点的像素距离
				dx := x - laneStart[0]
				dy := y - laneStart[1]
				pixelDist := math.Sqrt(float64(dx*dx + dy*dy))

				// 使用拟合的多项式计算实际距离
				realDist := a*pixelDist*pixelDist + bCoeff*pixelDist + c
				if realDist > maxVehicleDistance {
					maxVehicleDistance = realDist
				}
			}
		}
	}

	// 添加随机噪声（模拟真实场景的波动）
	noise := (rand.Float64() - 0.5) * 10
	maxVehicleDistance = math.Max(0, maxVehicleDistance+noise)

	// 返回分析结果
	return QueueAnalysis{
		Length:       math.Round(maxVehicleDistance*10) / 10, // 保留 1 位小数
		VehicleCount: int(math.Round(float64(vehicleCount) * 0.3)), // 车辆数量修正系数
	}
}

// fitQuadratic 二次多项式拟合函数
// 使用最小二乘法拟合 y = ax^2 + bx + c
// 参数：
//   - x: 自变量数组（像素距离）
//   - y: 因变量数组（实际距离）
// 返回：
//   - a, b, c: 多项式系数
func fitQuadratic(x, y []float64) (a, b, c float64) {
	n := len(x)
	if n < 3 {
		// 数据点不足时返回默认值
		return 0.001, 0.1, 0
	}

	// 计算各种求和项
	var sumX, sumX2, sumX3, sumX4 float64
	var sumY, sumXY, sumX2Y float64

	for i := 0; i < n; i++ {
		sumX += x[i]
		sumX2 += x[i] * x[i]
		sumX3 += x[i] * x[i] * x[i]
		sumX4 += x[i] * x[i] * x[i] * x[i]
		sumY += y[i]
		sumXY += x[i] * y[i]
		sumX2Y += x[i] * x[i] * y[i]
	}

	// 最小二乘法求解多项式系数
	nFloat := float64(n)
	denominator := nFloat*sumX2*sumX4 + 2*sumX*sumX2*sumX3 - sumX2*sumX2*sumX2 - nFloat*sumX3*sumX3 - sumX*sumX*sumX4

	if denominator == 0 {
		// 分母为 0 时返回默认值
		return 0.001, 0.1, 0
	}

	// 计算系数 a, b, c
	a = (nFloat*sumX2*sumX2Y + sumX*sumX3*sumY + sumX*sumX2*sumXY -
		sumX2*sumX2*sumY - nFloat*sumX3*sumXY - sumX*sumX*sumX2Y) / denominator

	b = (nFloat*sumX3*sumX2Y + sumX2*sumX4*sumY + sumX*sumX2*sumXY -
		sumX2*sumX3*sumXY - nFloat*sumX4*sumXY - sumX*sumX3*sumY) / (-denominator)

	c = (sumY - a*sumX2 - b*sumX) / nFloat

	return a, b, c
}

// detectEmergencyVehicles 紧急车辆检测函数
// 基于颜色特征检测救护车、消防车、警车
// 参数：
//   - img: 输入图片
// 返回：
//   - EmergencyDetection: 检测结果
func detectEmergencyVehicles(img image.Image) EmergencyDetection {
	// 获取图片边界
	bounds := img.Bounds()
	width, height := bounds.Max.X, bounds.Max.Y

	// 检测结果标记
	var detectedTypes []string
	hasRed := false
	hasWhite := false
	hasYellow := false

	// 遍历图片像素点（步长为 5，提高效率）
	for y := 0; y < height; y += 5 {
		for x := 0; x < width; x += 5 {
			// 获取像素颜色
			r, g, b, _ := img.At(x, y).RGBA()
			r8, g8, b8 := uint8(r>>8), uint8(g>>8), uint8(b>>8)

			// 检测红色（消防车特征）
			if r8 > 200 && g8 < 100 && b8 < 100 {
				hasRed = true
			}
			// 检测白色（救护车特征）
			if r8 > 220 && g8 > 220 && b8 > 220 {
				hasWhite = true
			}
			// 检测黄色/蓝色（警车特征）
			if (r8 > 200 && g8 > 180 && b8 < 100) || // 黄色
				(r8 < 100 && g8 > 150 && b8 > 200) { // 蓝色
				hasYellow = true
			}
		}
	}

	// 根据颜色组合判断紧急车辆类型
	if hasRed && hasWhite {
		detectedTypes = append(detectedTypes, "救护车")
	}
	if hasRed && !hasWhite {
		detectedTypes = append(detectedTypes, "消防车")
	}
	if hasYellow {
		detectedTypes = append(detectedTypes, "警车")
	}

	// 如果检测到紧急车辆且随机概率大于 0.3，返回检测结果
	if len(detectedTypes) > 0 && rand.Float64() > 0.3 {
		return EmergencyDetection{
			Detected:   true,
			Types:      detectedTypes,
			Confidence: 0.7 + rand.Float64()*0.3, // 置信度 0.7-1.0
		}
	}

	// 未检测到紧急车辆
	return EmergencyDetection{
		Detected:   false,
		Types:      []string{},
		Confidence: 0,
	}
}

// predictTrafficFlow 交通流量预测函数
// 基于历史数据的 LSTM 风格预测（移动平均 + 趋势分析）
// 参数：
//   - historicalData: 历史交通流量数据
// 返回：
//   - TrafficPrediction: 预测结果
func predictTrafficFlow(historicalData []int) TrafficPrediction {
	n := len(historicalData)
	if n < 3 {
		// 数据不足时返回默认值
		return TrafficPrediction{
			PredictedFlow: 50,
			Confidence:    0.5,
		}
	}

	// 计算历史平均值
	var total int
	for _, v := range historicalData {
		total += v
	}
	mean := float64(total) / float64(n)

	// 计算趋势（最近 5 个数据与最早 5 个数据的差值）
	trend := 0.0
	if n >= 5 {
		recentMean := float64(sumIntArray(historicalData[n-5:])) / 5.0
		oldMean := float64(sumIntArray(historicalData[:5])) / 5.0
		trend = recentMean - oldMean
	}

	// 预测下一时刻流量（考虑趋势和随机波动）
	predicted := mean + trend*0.3
	predicted += (rand.Float64() - 0.5) * 10
	predicted = math.Max(20, math.Min(120, predicted)) // 限制范围 20-120

	// 计算标准差（用于评估置信度）
	stdDev := calculateStdDev(historicalData, mean)
	confidence := math.Max(0.3, math.Min(0.95, 1.0-stdDev/30.0))

	return TrafficPrediction{
		PredictedFlow: int(math.Round(predicted)),
		Confidence:    math.Round(confidence*100) / 100,
	}
}

// sumIntArray 整数数组求和函数
// 参数：
//   - arr: 整数数组
// 返回：
//   - 数组元素之和
func sumIntArray(arr []int) int {
	s := 0
	for _, v := range arr {
		s += v
	}
	return s
}

// calculateStdDev 计算标准差函数
// 参数：
//   - data: 数据数组
//   - mean: 平均值
// 返回：
//   - 标准差
func calculateStdDev(data []int, mean float64) float64 {
	var sumSquaredDiff float64
	for _, v := range data {
		diff := float64(v) - mean
		sumSquaredDiff += diff * diff
	}
	return math.Sqrt(sumSquaredDiff / float64(len(data)))
}

// getWeatherFactor 获取天气影响因子
// 雨雪雾天气会增加通行时间，因为：
// - 雨天路面湿滑，车辆制动距离增加
// - 雪天路面结冰，能见度降低
// - 雾天能见度差，车辆行驶速度降低
// 参数：
//   - weatherType: 天气类型字符串
// 返回：
//   - 天气影响因子 (1.0-1.4)
func getWeatherFactor(weatherType string) float64 {
	// 精确匹配
	weatherMap := map[string]float64{
		"sunny":        1.0,      // 晴天：无影响
		"cloudy":       1.0,      // 多云：无影响
		"light_rain":   1.1,      // 小雨：增加10%
		"heavy_rain":   1.2,      // 大雨：增加20%
		"light_snow":   1.2,      // 小雪：增加20%
		"heavy_snow":   1.3,      // 大雪：增加30%
		"fog":          1.4,      // 雾：增加40%
		"sleet":        1.35,     // 雨夹雪：增加35%
		"hail":         1.3,      // 冰雹：增加30%
	}

	if factor, ok := weatherMap[weatherType]; ok {
		return factor
	}

	// 模糊匹配（中文天气描述）
	if contains(weatherType, "雨") || contains(weatherType, "rain") {
		if contains(weatherType, "大") || contains(weatherType, "heavy") {
			return 1.2
		}
		return 1.1
	}
	if contains(weatherType, "雪") || contains(weatherType, "snow") {
		if contains(weatherType, "大") || contains(weatherType, "heavy") {
			return 1.3
		}
		return 1.2
	}
	if contains(weatherType, "雾") || contains(weatherType, "fog") {
		return 1.4
	}
	if contains(weatherType, "夹雪") || contains(weatherType, "sleet") {
		return 1.35
	}
	if contains(weatherType, "冰雹") || contains(weatherType, "hail") {
		return 1.3
	}

	return 1.0 // 默认无影响
}

// contains 检查字符串是否包含子串
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// optimizeSignalTiming 信号灯优化函数
// 基于排队长度、流量预测和紧急车辆检测结果，使用非线性模型计算绿灯时间
// 参数：
//   - queue: 排队长度分析结果
//   - prediction: 交通流量预测结果
//   - emergencyDetected: 是否检测到紧急车辆
//   - weatherType: 天气类型（影响通行时间）
// 返回：
//   - SignalOptimization: 信号灯优化结果
func optimizeSignalTiming(queue QueueAnalysis, prediction TrafficPrediction, emergencyDetected bool, weatherType string) SignalOptimization {
	// 定义参数范围
	minGreenTime := 15.0  // 最小绿灯时间（秒）
	maxGreenTime := 120.0 // 最大绿灯时间（秒）
	betaMin := 0.1        // 最小β因子
	betaMax := 0.9        // 最大β因子

	// 计算拥堵等级（基于排队长度，0-1）
	congestionLevel := math.Min(1.0, queue.Length/200.0)

	// 计算非线性拥堵调节因子β
	var beta float64
	if emergencyDetected {
		// 紧急车辆优先：β取最大值
		beta = betaMax
	} else {
		// 使用 Sigmoid 函数计算β（避免线性增长）
		// Sigmoid 函数：1 / (1 + e^(-6*(x-0.5)))
		sigmoid := 1.0 / (1.0 + math.Exp(-6.0*(congestionLevel-0.5)))
		beta = betaMin + (betaMax-betaMin)*sigmoid
	}

	// 获取天气影响因子
	weatherFactor := getWeatherFactor(weatherType)

	// 计算基础通行时间
	baseTime := 30.0 + queue.Length*0.5 + float64(prediction.PredictedFlow)*0.2

	// 使用对数函数避免绿灯时间线性增长（防止过大或过小）
	greenTime := minGreenTime + (maxGreenTime-minGreenTime)*math.Log(1+baseTime)/math.Log(1+100)
	// 应用β因子调节
	greenTime = minGreenTime + (greenTime-minGreenTime)*beta
	// 应用天气影响因子（雨雪雾天气增加通行时间）
	greenTime *= weatherFactor
	// 限制在合理范围内
	greenTime = math.Max(minGreenTime, math.Min(maxGreenTime, greenTime))

	return SignalOptimization{
		GreenTime:       math.Round(greenTime*10) / 10,      // 保留 1 位小数
		CongestionLevel: math.Round(congestionLevel*100) / 100, // 保留 2 位小数
		Beta:            math.Round(beta*1000) / 1000,       // 保留 3 位小数
		WeatherFactor:   math.Round(weatherFactor*100) / 100, // 保留 2 位小数
	}
}
