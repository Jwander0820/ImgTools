import os

import tifftools
from PIL import Image


class TifTools:
    def save_multipage_tiff(self, image_paths, output_path, compression='tiff_lzw', color_mode=None):
        """
        壓縮多個圖片成一個多頁的 tif 檔
        :param image_paths: 圖片檔案路徑列表
        :param output_path: 壓縮後的 tif 檔輸出路徑
        :param compression: 壓縮方法，預設為 'tiff_lzw'
        :param color_mode: 位元深度轉換，根據PIL設定，例如 '1'、'L'、'RGB'、'RGBA'
        """
        if convert:
            images = [Image.open(image_path).convert(color_mode) for image_path in image_paths]
        else:
            images = [Image.open(image_path) for image_path in image_paths]

        # 轉換所有圖片到第一張圖片的模式和大小
        images = [image.convert(images[0].mode).resize(images[0].size) for image in images]

        # 儲存多頁tif
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            compression=compression
        )

        print(f"Multipage tif has been saved to {output_path}")

    def _get_file_name(self, path):
        file_name_with_ext = os.path.basename(path)  # 取出文件名(包含副檔名)
        file_name, _ = os.path.splitext(file_name_with_ext)  # 去除副檔名
        return file_name

    def split_all_page(self, path, folder_name="output"):
        """
        將多頁 tif 檔拆分並儲存為單頁 tif 檔
        :param path: tif檔案路徑
        :param folder_name: 存儲資料夾名稱，如果不設定則自動命名並儲存至同一層 output 資料夾下
        """
        img = Image.open(path)
        file_name = self._get_file_name(path)

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        for page in range(img.n_frames):
            img.seek(page)
            tmp_img = img.convert("1")
            tmp_file_name = f"{file_name}_page{str(page + 1).zfill(3)}.tif"
            save_path = os.path.join(folder_name, tmp_file_name)
            tmp_img.save(save_path, dpi=(600, 600), compression="tiff_lzw")
            print(save_path)

    def process_single_page(self, path, page, show=False, save=False, output_path=""):
        """
        查看或儲存單一頁面的 tif 圖片
        :param path: tif 檔案的路徑
        :param page: 指定想要處理的頁數
        :param show: 是否要顯示該頁，預設為False
        :param save: 是否要儲存該頁，預設為False
        :param output_path: 若儲存，儲存的資料夾路徑(不包含檔名)
        :return: 處理後的圖片物件
        """
        file_name = self._get_file_name(path)
        img = Image.open(path)
        img.seek(page)
        if show:
            img.show()
        if save or output_path:
            tmp_file_name = f"{file_name}_page{str(page + 1).zfill(3)}.tif"
            save_path = os.path.join(output_path, tmp_file_name)  # 若未指定output_path，預設儲存在同層資料夾下
            img.save(save_path, dpi=(600, 600), compression="tiff_lzw")
            print(save_path)
        return img

    def merge_img_to_one_tif(self, folder_path, save_file_path):
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


if __name__ == '__main__':
    # 將_path替換成想要拆頁的tif檔路徑執行即可
    _path = r"./test_file.tif"
    _page = 0

    tif_tools = TifTools()

    # 讀取或是儲存單一頁圖片
    tif_tools.process_single_page(_path, _page, save=True)

    # 分割多頁tif檔案成單一tif檔案
    # tif_tools.split_all_page(_path)

    # 合併成多頁tif檔
    # _folder_path = "../merge_img"
    # _save_file_path = "./merge_img_to_one_TIF.tif"
    # tif_tools.merge_img_to_one_tif(_folder_path, _save_file_path)
