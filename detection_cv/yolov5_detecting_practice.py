"""
YOLOv5 기반 객체 검출 실습 코드
- 목적: 이미지/영상 입력에 대해 객체를 탐지하고, 결과를 시각화하는 파이프라인을 정리한 예제
- 포트폴리오 포인트: 데이터 준비, 모델 로딩, 추론, 결과 저장까지의 흐름을 한 파일에서 확인할 수 있도록 구성
"""

# =============================================================================
# 1. 환경 설정 및 라이브러리 로드
# =============================================================================

import os
import cv2
import torch
import numpy as np
from pathlib import Path


# =============================================================================
# 2. 모델 및 입력 설정
# =============================================================================

MODEL_PATH = "weights/yolov5s.pt"
INPUT_PATH = "data/input.mp4"
OUTPUT_DIR = "outputs"
CONF_THRES = 0.25
IOU_THRES = 0.45

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_model(model_path):
    """
    YOLOv5 모델을 불러오는 함수.
    - 사전 학습된 가중치를 사용해 객체 검출 모델을 초기화한다.
    """
    model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path, trust_repo=True)
    model.conf = CONF_THRES
    model.iou = IOU_THRES
    return model


def draw_boxes(frame, results):
    """
    검출 결과를 프레임 위에 시각화한다.
    - 객체 클래스, 신뢰도, 바운딩 박스를 함께 표시한다.
    """
    for *box, conf, cls in results.xyxy[0].cpu().numpy():
        x1, y1, x2, y2 = map(int, box)
        label = f"{results.names[int(cls)]} {conf:.2f}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame


def run_detection(model, input_path, output_dir):
    """
    이미지 또는 영상 입력에 대해 객체 검출을 수행하고 결과를 저장한다.
    """
    suffix = Path(input_path).suffix.lower()

    if suffix in [".jpg", ".jpeg", ".png", ".bmp"]:
        image = cv2.imread(input_path)
        if image is None:
            raise FileNotFoundError(f"입력 이미지를 찾을 수 없습니다: {input_path}")

        results = model(image)
        annotated = draw_boxes(image.copy(), results)
        output_path = os.path.join(output_dir, f"result{suffix}")
        cv2.imwrite(output_path, annotated)
        print(f"결과 저장 완료: {output_path}")

    else:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"입력 영상을 열 수 없습니다: {input_path}")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_path = os.path.join(output_dir, "result.mp4")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            annotated = draw_boxes(frame, results)
            writer.write(annotated)

        cap.release()
        writer.release()
        print(f"결과 저장 완료: {output_path}")


def main():
    """
    실행 진입점.
    - 모델을 로드한 뒤 입력 데이터에 대해 검출을 수행한다.
    """
    model = load_model(MODEL_PATH)
    run_detection(model, INPUT_PATH, OUTPUT_DIR)


if __name__ == "__main__":
    main()