import glob
import os

import cv2
import moviepy.editor as mp
from PIL import Image


def convert_mp4_to_frame(input_file, output_folder="output", filename_template="frame_{:03d}.png"):
    """
    將 mp4 影片檔案轉換為逐幀的圖片檔，並儲存到指定的資料夾。
    :param input_file: 輸入 mp4 影片檔案路徑
    :param output_folder: 儲存輸出圖片的資料夾。如果資料夾不存在，將會自動建立
    :param filename_template: 輸出圖片的檔名模板。應包含一個用於插入幀編號的格式化字段
    :return:
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # 先將mp4文件的所有幀讀取出儲存成圖片
    video_capture = cv2.VideoCapture(input_file)
    still_reading, image = video_capture.read()
    frame_count = 0
    while still_reading:
        output_path = os.path.join(output_folder, filename_template.format(frame_count))
        cv2.imwrite(output_path, image)
        # read next image
        still_reading, image = video_capture.read()
        frame_count += 1
    video_capture.release()
    print(f"轉換完成 共 {frame_count} 幀")


def convert_images_to_gif(folder_path, output_path, convert_color="RGB", duration=40, loop=0):
    """
    將指定資料夾中的圖片轉換為一個 gif 檔案
    :param folder_path:要讀取圖片的資料夾路徑
    :param output_path:儲存生成的 gif 檔案完整路徑
    :param convert_color:圖片轉換的顏色模式，預設為"RGB"推薦使用"L"或"RGBA"
    :param duration:每一幀在 gif 中顯示的持續時間，單位為毫秒。預設為 40
    :param loop:gif 的循環次數，0 表示無限循環。預設為 0
    :return:
    """
    # 取得圖片清單並排列
    extensions = ["tif", "png", "jpg"]  # 指定副檔名
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(folder_path, f"*.{ext}")))
    images.sort()
    if not images:
        print("No images found.")
        return
    # 讀取並轉換檔案，建議convert_color為 "L"、"RGBA"
    frames = [Image.open(image).convert(convert_color) for image in images]
    # 儲存gif 若無resize成相同大小，gif疊圖會以第一張為準，參數可以自行調整
    frames[0].save(output_path, format="gif", append_images=frames[1:], save_all=True, duration=duration,
                   loop=loop, dpi=(600, 600))


def convert_mp4_to_gif(input_file, output_path):
    """
    調用上面兩個函數完成從 mp4 拆成單幀圖片在合成 gif
    :param input_file: 輸入 mp4 影片檔案路徑
    :param output_path: 儲存生成的 gif 檔案完整路徑
    :return:
    """
    convert_mp4_to_frame(input_file)
    convert_images_to_gif("./output", output_path)


def mp4_to_gif(input_file, output_path="output.gif"):
    """
    moviepy將 mp4 轉 gif
    :param input_file: 輸入 mp4 影片檔案路徑
    :param output_path: 儲存生成的 gif 檔案完整路徑
    :return:
    """
    clip_frame = mp.VideoFileClip(input_file)
    clip_frame.write_gif(output_path)


def gif_to_mp4(input_file, output_path="output.mp4"):
    """
    moviepy將 gif 轉 mp4
    :param input_file: 輸入 gif 檔案路徑
    :param output_path: 儲存生成的 mp4 檔案完整路徑
    :return:
    """
    clip_frame = mp.VideoFileClip(input_file)
    clip_frame.write_videofile(output_path)


if __name__ == "__main__":
    # _input_gif = "dvd_bounce.gif"  # 原始gif
    # gif_to_mp4(_input_gif)  # moviepy將gif轉mp4
    # _input_mp4 = "output.mp4"  # 提取計算完的mp4
    # mp4_to_gif(_input_mp4)  # moviepy將mp4轉gif

    # PIL將mp4轉gif，會先提取每幀到output資料夾下，再進行合併
    # convert_mp4_to_gif("output.mp4", "output_gif_by_pil.gif")

    # 拆分mp4
    # convert_mp4_to_frame("./output.mp4")

    # 拆分gif
    convert_images_to_gif(r"./output",
                          "./output_gif_by_pil.gif",
                          duration=40)
