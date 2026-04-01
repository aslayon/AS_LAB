#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kernel / weight visualizer

이 예제는 학습된 모델의 커널 또는 가중치를 시각화해
모델이 어떤 패턴을 학습했는지 해석하는 데 초점을 둔 데모입니다.

포트폴리오에서 보여주는 포인트:
- 학습된 파라미터를 시각적으로 점검하는 방법
- 커널/가중치의 구조를 통해 모델의 해석 가능성을 설명하는 방식
- AutoML 결과를 "성능"뿐 아니라 "설명 가능성" 관점에서 보여주는 예제
"""

import numpy as np
import matplotlib.pyplot as plt


def main():
    kernels = np.array(
        [
            [[1, 0, -1], [1, 0, -1], [1, 0, -1]],
            [[1, 1, 1], [0, 0, 0], [-1, -1, -1]],
            [[0, -1, 0], [-1, 4, -1], [0, -1, 0]],
        ],
        dtype=float,
    )

    fig, axes = plt.subplots(1, kernels.shape[0], figsize=(12, 4))
    for idx, ax in enumerate(np.atleast_1d(axes)):
        ax.imshow(kernels[idx], cmap="coolwarm")
        ax.set_title(f"Kernel {idx + 1}")
        ax.axis("off")

    plt.suptitle("Kernel Weight Visualizer")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()