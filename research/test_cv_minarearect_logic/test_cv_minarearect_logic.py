import glob
import os

import cv2
import numpy as np
from PIL import Image


def rotate_image(img, angle, times=1):
    """
    旋轉圖片
    :param img: 圖片(cv)
    :param angle: 旋轉角度
    :param times: 旋轉次數
    :return: 旋轉後的圖片
    """
    for _ in range(times):
        matrix = cv2.getRotationMatrix2D(
            (img.shape[1] / 2, img.shape[0] / 2), angle, 1.0
        )
        img = cv2.warpAffine(img, matrix, (img.shape[1], img.shape[0]), borderValue=255)
        _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

        org_angle = cal_skew_average_angle(img)
        org_text = f"org_angle    : {round(org_angle, 5)}"
        adj_angle = adjust_angle(org_angle)
        adj_text = f"adjust_angle : {round(adj_angle, 5)}"

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, org_text, (10, 30), font, 1, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, adj_text, (10, 70), font, 1, (0, 0, 0), 3, cv2.LINE_AA)

    return img, org_angle, adj_angle


def cal_skew_average_angle(img):
    """
    計算給定圖像的偏斜角度
    :param img: 要進行計算的圖像
    :return: 圖像的偏斜角度
    """
    # 二值化處理 (如果確定為連續處理，可省去中間的兩次二值化)
    _, tmp = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    # 提取輪廓
    contours, _ = cv2.findContours(tmp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 計算輪廓角度(含限制校正角度)
    rect = cv2.minAreaRect(contours[0])
    center, size, angle = rect
    return angle


def adjust_angle(angle):
    """
    調整最終計算角度，若超過限制則取消歪斜校正(angle設為0)
    :param angle: 計算過後的角度
    :return:
    """
    # print("Before", angle)
    if angle < -45:
        angle += 90
    elif angle >= 45:
        angle -= 90
    return angle


def convert_images_to_gif(output_file):
    # 讀取目錄下圖片，用Pillow模組的Image將所有圖片合併成一張gif
    images = glob.glob(f"tmp_img/*")
    images.sort()
    frames = [Image.open(image) for image in images]
    frame_one = frames[0]
    frame_one.save(output_file, format="GIF", append_images=frames[1:],
                   save_all=True, duration=40, loop=0)


if __name__ == '__main__':
    """
    測試cv2.minAreaRect計算的邏輯 (0 ~ -90)，根據檢測到的矩形最底邊的點為原點，向右向上分別為x,y
    從原點開始水平向上旋轉，直到碰到邊界為止，計算出旋轉的角度，但計算出來的只是旋轉角度，還需要經過處理才是真實需要旋轉的角度
    adjust_angle 負責處理要往哪邊轉，以45度為界，若為-0~-45代表會轉回垂直的矩形，若為-45~-90則會轉成水平的矩形 (以長邊來看)
    """
    img_path = r"./test_rect.tif"

    org_img = Image.open(img_path)
    org_img = org_img.convert("L")
    org_img = np.uint8(org_img)

    if not os.path.exists("tmp_img"):
        os.makedirs("tmp_img")

    for angle in range(360):
        rotated_img, cal_angle, adj_angle = rotate_image(org_img, angle + 1)

        rotated_img = Image.fromarray(rotated_img)
        rotated_img.save(
            f"./tmp_img/rotated_旋轉{str(angle + 1).zfill(3)}度_cv計算角度{round(cal_angle, 5)}_最終角度{round(adj_angle, 5)}.tif",
            dpi=(600, 600), compression="tiff_lzw")

    # 如果想要轉成gif觀察旋轉的連續變化，可以啟用以下函數生成gif
    # convert_images_to_gif("rotated_0-360.gif")
