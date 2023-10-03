from typing import List

import cv2
import numpy as np


def load_gif_images(gif_path: str) -> List[np.ndarray]:
    gif = cv2.VideoCapture(gif_path)

    gif_images: List[np.ndarray] = []

    ret = True
    while ret:
        # 次のフレーム読み込み
        ret, frame = gif.read()
        if not ret:
            break

        gif_images.append(frame)
    
    return gif_images
