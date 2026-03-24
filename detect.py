# detect.py
from ultralytics import YOLO
import os

def main():
    # 加载你训练好的紧急车辆模型
    model = YOLO("best.pt")

    # 待识别的图片文件夹
    image_folder = "val/images"
    save_folder = "detect_results"

    os.makedirs(save_folder, exist_ok=True)

    # 批量识别
    for img_name in os.listdir(image_folder):
        if img_name.endswith((".jpg", ".jpeg", ".png", ".bmp")):
            img_path = os.path.join(image_folder, img_name)
            results = model(img_path)
            save_path = os.path.join(save_folder, img_name)
            results[0].save(save_path)
            print(f"已识别：{img_name}")

    print("✅ 识别完成！结果保存在 detect_results 文件夹")

if __name__ == "__main__":
    main()