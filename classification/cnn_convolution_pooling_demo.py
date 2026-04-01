#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNN convolution and pooling demo

이 예제는 합성곱(Convolution)과 풀링(Pooling)이
이미지 특징을 어떻게 추출하고 압축하는지 보여주는 설명용 데모입니다.

포트폴리오에서 보여주는 포인트:
- 필터가 국소 패턴을 어떻게 반응하는지
- 풀링이 특징 맵의 크기를 어떻게 줄이는지
- CNN의 핵심 아이디어를 시각적으로 설명하는 방식
"""

import numpy as np
import matplotlib.pyplot as plt


def _convolve2d(image, kernel):
    image_h, image_w = image.shape
    kernel_h, kernel_w = kernel.shape
    out_h = image_h - kernel_h + 1
    out_w = image_w - kernel_w + 1
    output = np.zeros((out_h, out_w))

    for i in range(out_h):
        for j in range(out_w):
            output[i, j] = np.sum(image[i:i + kernel_h, j:j + kernel_w] * kernel)
    return output


def _max_pool2d(feature_map, pool_size=2):
    h, w = feature_map.shape
    out_h = h // pool_size
    out_w = w // pool_size
    output = np.zeros((out_h, out_w))

    for i in range(out_h):
        for j in range(out_w):
            patch = feature_map[
                i * pool_size:(i + 1) * pool_size,
                j * pool_size:(j + 1) * pool_size,
            ]
            output[i, j] = np.max(patch)
    return output


def main():
    image = np.array(
        [
            [0, 0, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0],
        ],
        dtype=float,
    )

    kernel = np.array(
        [
            [1, 0, -1],
            [1, 0, -1],
            [1, 0, -1],
        ],
        dtype=float,
    )

    feature_map = _convolve2d(image, kernel)
    pooled_map = _max_pool2d(feature_map)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(image, cmap="gray")
    axes[0].set_title("Input Image")
    axes[0].axis("off")

    axes[1].imshow(feature_map, cmap="viridis")
    axes[1].set_title("Convolution")
    axes[1].axis("off")

    axes[2].imshow(pooled_map, cmap="viridis")
    axes[2].set_title("Max Pooling")
    axes[2].axis("off")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()