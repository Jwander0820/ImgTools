import os
import tifftools
from PIL import Image


def merge_img_to_one_tif(folder_path, save_file_path):
    """
    將資料夾下的所有圖片合成一張多幀TIF，合成多幀TIF是直接原圖合併成TIF檔，不受圖像尺寸限制
    :param folder_path: 資料夾路徑
    :param save_file_path: 儲存檔案的路徑
    :return: 儲存檔案的路徑
    """
    files = os.listdir(folder_path)  # 讀取資料夾內所有資料
    tif_files = []
    for file in files:
        if '.tif' in file or '.png' in file or '.jpg' in file:  # 檢測若file檔名包含.tif、.png、.jpg 加入要合併的清單
            img_path = os.path.join(folder_path, file)
            tif_files.append(img_path)
    tif_files.sort()
    # tifftools合成多幀tif檔案，效率佳又不吃記憶體；Image.save()也可以儲存多幀tif，但效率相對較差
    tifftools.tiff_concat(tif_files, save_file_path, overwrite=True)
    return save_file_path


def merge_img_to_one_pdf(folder_path, save_file_path):
    """
    將資料夾下的所有圖片合成PDF，不受圖像尺寸限制
    :param folder_path: 資料夾路徑
    :param save_file_path: 儲存檔案的路徑
    :return: 儲存檔案的路徑
    """
    files = os.listdir(folder_path)  # 讀取資料夾內所有資料
    pdf_files = []
    for file in files:
        if '.tif' in file or '.png' in file or '.jpg' in file:  # 檢測若file檔名包含.tif、.png、.jpg 加入要合併的清單
            img_path = os.path.join(folder_path, file)
            img = Image.open(img_path).convert("RGB")
            pdf_files.append(img)
    pdf_files[0].save(save_file_path, "pdf", append_images=pdf_files[1:], save_all=True)
    return save_file_path


def merge_img_to_one_gif(folder_path, save_file_path, duration=1000):
    """
    將資料夾下的所有圖片合成一張GIF，合成GIF建議圖像尺寸大小相近，否則會按照第一張圖的尺寸作貼圖
    :param folder_path: 資料夾路徑
    :param save_file_path: 儲存檔案的路徑
    :param duration: 圖片間隔時長，單位為毫秒
    :return: 儲存檔案的路徑
    """
    files = os.listdir(folder_path)  # 讀取資料夾內所有資料
    gif_list = []
    for file in files:
        if '.tif' in file or '.png' in file or '.jpg' in file:  # 檢測若file檔名包含.tif、.png、.jpg 加入要合併的清單
            img_path = os.path.join(folder_path, file)
            img = Image.open(img_path).convert("RGB")
            img = img.resize((1000, 1000))  # 若無resize成相同大小，GIF疊圖會以第一張為準，參數可以自行調整
            gif_list.append(img)
    gif_list[0].save(save_file_path, save_all=True, append_images=gif_list[1:], loop=0, duration=duration, disposal=0)
    return save_file_path


if __name__ == "__main__":
    folder_dir = "./data"  # 儲存的資料夾
    if not os.path.exists(folder_dir):
        os.makedirs(folder_dir)

    _folder_path = "./merge_img"
    _save_file_path = "./data/merge_img_to_one_TIF.tif"
    merge_img_to_one_tif(_folder_path, _save_file_path)

    _folder_path = "./merge_img"
    _save_file_path = "./data/merge_img_to_one_PDF.pdf"
    merge_img_to_one_pdf(_folder_path, _save_file_path)

    _folder_path = "./merge_img"
    _save_file_path = "./data/merge_img_to_one_GIF.gif"
    merge_img_to_one_gif(_folder_path, _save_file_path, duration=1000)
