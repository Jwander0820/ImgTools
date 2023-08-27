import cv2
import numpy as np
from PIL import Image


def rotate_image(img_path, angle, times=1):
    """
    旋轉圖片

    :param img_path: 圖片路徑
    :param angle: 旋轉角度
    :param times: 旋轉次數
    :return: 旋轉後的圖片
    """
    img = Image.open(img_path)
    img = img.convert("L")
    img = np.uint8(img)

    for _ in range(times):
        matrix = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), angle, 1.0)
        img = cv2.warpAffine(img, matrix, (img.shape[1], img.shape[0]), borderValue=255)
        _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)  # 二值化可關閉，此為強制轉黑白

    return img


def test_rotation(img_path, angle, times, case):
    rotated_img = rotate_image(img_path, angle, times)
    rotated_img = Image.fromarray(rotated_img)
    rotated_img.save(f"rotated_case{case}_{angle}度_{times}次.tif", dpi=(600, 600), compression="tiff_lzw")



if __name__ == '__main__':
    img_path = r"./test_img.tif"
    # 測試多次旋轉對圖像造成的影響

    test_cases = [
        {'case': 1, 'angle': 0.01, 'times': 1000},
        {'case': 2, 'angle': 10, 'times': 1},
        {'case': 3, 'angle': 0.5, 'times': 10},
        {'case': 4, 'angle': 5, 'times': 1},
        {'case': 5, 'angle': 1, 'times': 360},
        {'case': 6, 'angle': 360, 'times': 1},
        {'case': 7, 'angle': 0.5, 'times': 100},
        {'case': 8, 'angle': 50, 'times': 1},
    ]

    for test_case in test_cases:
        test_rotation(img_path, test_case['angle'], test_case['times'], test_case['case'])