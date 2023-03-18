import cv2
import numpy as np
import os


def crop_text(img_path):
    # 載入圖片
    image = cv2.imread(img_path)

    # 轉換成灰階圖片
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 二值化處理
    threshold_value, threshold_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 膨脹操作
    kernel = np.ones((3, 3), np.uint8)
    dilated_image = cv2.dilate(threshold_image, kernel, iterations=10)

    # 尋找輪廓
    contours, hierarchy = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 創建img資料夾
    if not os.path.exists('img'):
        os.mkdir('img')

    # 遍歷每個輪廓
    for i, contour in enumerate(contours):
        # 計算輪廓的外接矩形
        x, y, w, h = cv2.boundingRect(contour)

        # 擷取圖片
        extracted_image = image[y:y+h, x:x+w]

        # 擷取二值化圖片作為 alpha 通道
        extracted_alpha = threshold_image[y:y+h, x:x+w]

        # 去背處理
        b, g, r = cv2.split(extracted_image)
        rgba = [b, g, r, extracted_alpha]
        extracted_image_rgba = cv2.merge(rgba, 4)

        # 建立透明底圖
        transparent_image = np.zeros((160, 160, 4), dtype=np.uint8)

        # 計算圖片置中位置
        center_x = int(transparent_image.shape[1] / 2)
        center_y = int(transparent_image.shape[0] / 2)
        offset_x = int(w / 2)
        offset_y = int(h / 2)
        x1 = center_x - offset_x
        y1 = center_y - offset_y
        x2 = x1 + w
        y2 = y1 + h

        # 將圖片置中放置在透明底圖上
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(transparent_image.shape[1], x2)
        y2 = min(transparent_image.shape[0], y2)

        # 擷取圖片的部分可能超出範圍
        extracted_image_rgba = extracted_image_rgba[:y2-y1, :x2-x1]

        transparent_image[y1:y2, x1:x2] = extracted_image_rgba

        # 儲存圖片
        filename = os.path.join('img', f'{i}.png')
        cv2.imwrite(filename, transparent_image)
