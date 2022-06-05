import glob
import cv2
from PIL import Image
import moviepy.editor as mp


def convert_mp4_to_jpgs(input_file):
    # 先將mp4文件的所有幀讀取出保存成圖片
    video_capture = cv2.VideoCapture(input_file)
    still_reading, image = video_capture.read()
    frame_count = 0
    while still_reading:
        cv2.imwrite(f"output/frame_{frame_count:03d}.png", image)
        # read next image
        still_reading, image = video_capture.read()
        frame_count += 1


def convert_images_to_gif(output_file):
    # 讀取目錄下圖片，用Pillow模組的Image將所有圖片合併成一張gif
    images = glob.glob(f"output/*.png")
    images.sort()
    frames = [Image.open(image) for image in images]
    frame_one = frames[0]
    frame_one.save(output_file, format="GIF", append_images=frames[1:],
                   save_all=True, duration=40, loop=0)


def convert_mp4_to_gif(input_file, output_file):
    # 調用上面兩個函數完成從 mp4拆成單幀圖片在合成gif
    convert_mp4_to_jpgs(input_file)
    convert_images_to_gif(output_file)


def mp4_to_gif2(input_file):
    # moviepy將mp4轉gif
    clip_frame = mp.VideoFileClip(input_file)
    clip_frame.write_gif("output.gif")


def gif_to_mp4(input_file):
    # moviepy將gif轉mp4
    clip_frame = mp.VideoFileClip(input_file)
    clip_frame.write_videofile("output.mp4")


if __name__ == "__main__":
    _input_gif = "dvd_bounce.gif"  # 原始gif
    gif_to_mp4(_input_gif)  # moviepy將gif轉mp4
    _input_mp4 = "output.mp4"  # 提取計算完的mp4
    mp4_to_gif2(_input_mp4)  # moviepy將mp4轉gif
    # PIL將mp4轉gif，會先提取每幀到output資料夾下，再進行合併
    convert_mp4_to_gif("output.mp4", "output_gif_by_pil.gif")
