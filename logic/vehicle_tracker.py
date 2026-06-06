# ByteTrack 目标追踪模块
# 基于 ByteTrack 算法实现高精度多目标追踪
# 支持遮挡环境下的 ID 保持

import numpy as np
from collections import OrderedDict

class STrack:
    """单目标追踪对象"""
    shared_kalman = None
    
    def __init__(self, tlwh, score, cls):
        self.tlwh = np.asarray(tlwh, dtype=np.float32)
        self.score = score
        self.cls = cls
        self.track_id = 0
        self.is_activated = False
        self.state = 'New'
        
        self.frame_id = 0
        self.start_frame = 0
        self.detection_count = 1
        
        self.history = OrderedDict()
        self.features = []
        self.curr_feature = None
        
        # 速度估计
        self.velocity = np.array([0.0, 0.0])
        self.last_tlwh = self.tlwh.copy()
    
    def update(self, new_tlwh, score, frame_id):
        """更新追踪状态"""
        self.last_tlwh = self.tlwh.copy()
        self.tlwh = np.asarray(new_tlwh, dtype=np.float32)
        self.score = score
        self.frame_id = frame_id
        self.detection_count += 1
        
        # 计算速度
        delta_x = self.tlwh[0] - self.last_tlwh[0]
        delta_y = self.tlwh[1] - self.last_tlwh[1]
        self.velocity = np.array([delta_x, delta_y])
        
        # 记录历史轨迹
        self.history[frame_id] = self.tlwh.copy()
        if len(self.history) > 50:
            self.history.popitem(last=False)
    
    def predict(self):
        """预测下一帧位置（基于速度）"""
        predicted = self.tlwh.copy()
        predicted[0] += self.velocity[0]
        predicted[1] += self.velocity[1]
        return predicted
    
    def get_state(self):
        """获取状态"""
        return 'Tracking' if self.is_activated else 'Lost'
    
    @property
    def tlbr(self):
        """转换为 tlbr 格式"""
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret
    
    @property
    def center(self):
        """获取中心点"""
        return np.array([
            self.tlwh[0] + self.tlwh[2] / 2,
            self.tlwh[1] + self.tlwh[3] / 2
        ])

class ByteTrack:
    """ByteTrack 多目标追踪器"""
    
    def __init__(self, max_age=30, min_hits=3, iou_threshold=0.5):
        self.max_age = max_age  # 最大丢失帧数
        self.min_hits = min_hits  # 最小命中次数激活追踪
        self.iou_threshold = iou_threshold  # IOU 匹配阈值
        
        self.tracked_stracks = []  # 正在追踪的目标
        self.lost_stracks = []     # 丢失的目标
        self.removed_stracks = []  # 已移除的目标
        
        self.frame_id = 0
        self.next_id = 1
    
    def update(self, detections):
        """
        更新追踪状态
        detections: list of [x1, y1, x2, y2, score, cls]
        """
        self.frame_id += 1
        
        # 将检测框转换为 tlwh 格式
        if len(detections) > 0:
            dets = np.array(detections)
            dets_tlwh = self._tlbr_to_tlwh(dets[:, :4])
            det_scores = dets[:, 4]
            det_cls = dets[:, 5] if dets.shape[1] > 5 else np.zeros(len(dets))
        else:
            dets_tlwh = np.empty((0, 4))
            det_scores = np.empty(0)
            det_cls = np.empty(0)
        
        # 步骤1: 预测所有追踪目标的位置
        for track in self.tracked_stracks:
            track.predict()
        
        # 步骤2: 匹配检测与追踪目标
        matched_indices, unmatched_dets, unmatched_tracks = self._match(
            self.tracked_stracks, dets_tlwh, det_scores
        )
        
        # 步骤3: 更新匹配到的追踪目标
        for m in matched_indices:
            track = self.tracked_stracks[m[0]]
            track.update(dets_tlwh[m[1]], det_scores[m[1]], self.frame_id)
            track.is_activated = True
        
        # 步骤4: 处理未匹配的检测（作为新目标）
        for i in unmatched_dets:
            track = STrack(dets_tlwh[i], det_scores[i], det_cls[i])
            track.track_id = self.next_id
            self.next_id += 1
            track.frame_id = self.frame_id
            track.start_frame = self.frame_id
            track.is_activated = False
            self.tracked_stracks.append(track)
        
        # 步骤5: 处理未匹配的追踪目标（标记为丢失）
        for i in unmatched_tracks:
            track = self.tracked_stracks[i]
            if track.state != 'Lost':
                track.state = 'Lost'
                self.lost_stracks.append(track)
        
        # 步骤6: 从丢失列表中恢复匹配
        if len(self.lost_stracks) > 0 and len(dets_tlwh) > 0:
            matched_indices, unmatched_dets, unmatched_tracks = self._match(
                self.lost_stracks, dets_tlwh, det_scores
            )
            
            for m in matched_indices:
                track = self.lost_stracks[m[0]]
                track.update(dets_tlwh[m[1]], det_scores[m[1]], self.frame_id)
                track.state = 'Tracking'
                self.tracked_stracks.append(track)
            
            self.lost_stracks = [self.lost_stracks[i] for i in unmatched_tracks]
        
        # 步骤7: 移除长时间丢失的目标
        self.lost_stracks = [
            t for t in self.lost_stracks 
            if self.frame_id - t.frame_id < self.max_age
        ]
        self.tracked_stracks = [
            t for t in self.tracked_stracks 
            if self.frame_id - t.frame_id < self.max_age
        ]
        
        # 步骤8: 激活满足条件的追踪目标
        active_tracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                if self.frame_id - track.start_frame >= self.min_hits:
                    track.is_activated = True
                    active_tracks.append(track)
            else:
                active_tracks.append(track)
        
        return active_tracks
    
    def _match(self, tracks, dets, scores):
        """IOU 匹配算法"""
        if len(tracks) == 0 or len(dets) == 0:
            return [], list(range(len(dets))), list(range(len(tracks)))
        
        # 计算 IOU 矩阵
        iou_matrix = self._compute_iou_matrix(tracks, dets)
        
        # 贪心匹配
        matched_indices = []
        unmatched_dets = list(range(len(dets)))
        unmatched_tracks = list(range(len(tracks)))
        
        while True:
            # 找到最大 IOU
            max_iou = -1
            max_i = -1
            max_j = -1
            
            for i in unmatched_tracks:
                for j in unmatched_dets:
                    if iou_matrix[i, j] > max_iou and iou_matrix[i, j] > self.iou_threshold:
                        max_iou = iou_matrix[i, j]
                        max_i = i
                        max_j = j
            
            if max_iou < self.iou_threshold:
                break
            
            matched_indices.append([max_i, max_j])
            unmatched_tracks.remove(max_i)
            unmatched_dets.remove(max_j)
        
        return matched_indices, unmatched_dets, unmatched_tracks
    
    def _compute_iou_matrix(self, tracks, dets):
        """计算 IOU 矩阵"""
        iou_matrix = np.zeros((len(tracks), len(dets)))
        
        for i, track in enumerate(tracks):
            track_tlbr = track.tlbr
            for j, det in enumerate(dets):
                det_tlbr = np.array([det[0], det[1], det[0]+det[2], det[1]+det[3]])
                iou_matrix[i, j] = self._iou(track_tlbr, det_tlbr)
        
        return iou_matrix
    
    def _iou(self, box1, box2):
        """计算两个矩形的 IOU"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        w = max(0, x2 - x1)
        h = max(0, y2 - y1)
        inter = w * h
        
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        return inter / (area1 + area2 - inter)
    
    def _tlbr_to_tlwh(self, tlbr):
        """tlbr 转 tlwh"""
        tlwh = tlbr.copy()
        tlwh[:, 2] -= tlwh[:, 0]
        tlwh[:, 3] -= tlwh[:, 1]
        return tlwh
    
    def get_tracks(self):
        """获取所有活跃追踪目标"""
        return [t for t in self.tracked_stracks if t.is_activated]

class VehicleTracker:
    """车辆追踪器（封装 ByteTrack）"""
    
    def __init__(self):
        self.tracker = ByteTrack(
            max_age=30,
            min_hits=2,
            iou_threshold=0.45
        )
        self.track_history = {}
    
    def process_frame(self, detections, frame=None):
        """
        处理一帧检测结果
        detections: list of [x1, y1, x2, y2, score, cls]
        """
        tracks = self.tracker.update(detections)
        
        results = []
        for track in tracks:
            track_id = track.track_id
            tlbr = track.tlbr
            center = track.center
            
            # 更新轨迹历史
            if track_id not in self.track_history:
                self.track_history[track_id] = []
            self.track_history[track_id].append((center[0], center[1]))
            
            # 限制历史长度
            if len(self.track_history[track_id]) > 100:
                self.track_history[track_id] = self.track_history[track_id][-50:]
            
            results.append({
                'track_id': track_id,
                'bbox': tlbr.tolist(),
                'score': track.score,
                'class': int(track.cls),
                'center': center.tolist(),
                'velocity': track.velocity.tolist(),
                'history': self.track_history[track_id],
                'age': self.tracker.frame_id - track.start_frame
            })
        
        return results
    
    def draw_tracks(self, frame, results):
        """在图像上绘制追踪结果"""
        import cv2
        
        for res in results:
            track_id = res['track_id']
            bbox = res['bbox']
            center = res['center']
            history = res['history']
            
            # 绘制边界框
            cv2.rectangle(frame, 
                        (int(bbox[0]), int(bbox[1])), 
                        (int(bbox[2]), int(bbox[3])), 
                        (0, 255, 0), 2)
            
            # 绘制轨迹
            if len(history) > 1:
                for i in range(1, len(history)):
                    cv2.line(frame,
                            (int(history[i-1][0]), int(history[i-1][1])),
                            (int(history[i][0]), int(history[i][1])),
                            (0, 255, 0), 2)
            
            # 绘制追踪ID
            cv2.putText(frame, f'ID:{track_id}',
                        (int(bbox[0]), int(bbox[1])-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame

# 示例使用
if __name__ == '__main__':
    tracker = VehicleTracker()
    
    # 模拟检测结果
    detections = [
        [50, 50, 150, 150, 0.95, 0],
        [200, 100, 300, 200, 0.92, 1],
        [350, 150, 450, 250, 0.88, 0]
    ]
    
    results = tracker.process_frame(detections)
    print(f"追踪到 {len(results)} 个目标")
    for res in results:
        print(f"ID: {res['track_id']}, BBox: {res['bbox']}")