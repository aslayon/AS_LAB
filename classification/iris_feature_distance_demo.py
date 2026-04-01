#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iris feature distance demo

이 예제는 Iris 데이터셋에서 특성 간 거리와 클래스 분포를
직관적으로 살펴보는 분류 학습용 데모입니다.

포트폴리오에서 보여주는 포인트:
- 데이터의 특성 공간을 어떻게 해석하는지
- 거리 기반 분류 직관이 왜 중요한지
- 산점도/시각화를 통해 클래스 구분을 설명하는 방식

실행 결과는 개별 특성 값과 클래스 간 관계를 확인하는 데 초점을 둡니다.
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris


def main():
    iris = load_iris()
    X = iris.data
    y = iris.target

    sepal_length = X[:, 0]
    sepal_width = X[:, 1]

    plt.figure(figsize=(8, 6))
    for target in np.unique(y):
        mask = y == target
        plt.scatter(
            sepal_length[mask],
            sepal_width[mask],
            label=iris.target_names[target],
            alpha=0.8,
        )

    plt.title("Iris Feature Distance Demo")
    plt.xlabel("Sepal Length")
    plt.ylabel("Sepal Width")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()