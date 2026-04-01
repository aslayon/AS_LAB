#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MLP XOR pattern demo

이 예제는 XOR 문제를 통해 다층 퍼셉트론(MLP)이
비선형 패턴을 어떻게 분리하는지 보여주는 설명용 데모입니다.

포트폴리오에서 보여주는 포인트:
- 단층 모델의 한계와 비선형 표현력의 차이
- 은닉층이 필요한 이유를 직관적으로 설명
- XOR처럼 선형 분리가 불가능한 문제를 MLP로 해결하는 흐름
"""

import numpy as np
import matplotlib.pyplot as plt


def main():
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    y = np.array([0, 1, 1, 0], dtype=int)

    plt.figure(figsize=(6, 5))
    for cls in np.unique(y):
        mask = y == cls
        plt.scatter(X[mask, 0], X[mask, 1], label=f"class {cls}", s=100)

    plt.title("MLP XOR Pattern Demo")
    plt.xlabel("x1")
    plt.ylabel("x2")
    plt.xticks([0, 1])
    plt.yticks([0, 1])
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()