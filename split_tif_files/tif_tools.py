import os

from PIL import Image


class TifTools:
    def save_multipage_tiff(self, image_paths, output_path, compression='tiff_lzw', convert=None):
        """
        壓縮多個圖片成一個多頁的TIFF檔
        :param image_paths: 圖片檔案路徑列表
        :param output_path: 壓縮後的TIFF檔輸出路徑
        :param compression: 壓縮方法，預設為 'tiff_lzw'
        :param compression: 位元深度轉換，根據PIL設定，例如 '1'、'L'、'RGB'、'RGBA'。
        """
        if convert:
            images = [Image.open(image_path).convert(convert) for image_path in image_paths]
        else:
            images = [Image.open(image_path) for image_path in image_paths]

        # 轉換所有圖片到第一張圖片的模式和大小
        images = [image.convert(images[0].mode).resize(images[0].size) for image in images]

        # 儲存多頁TIFF
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            compression=compression
        )

        print(f"Multipage TIFF has been saved to {output_path}")

    def save_all_page(self, path, folder_name=None):
        """
        儲存所有頁面為單頁TIFF檔。

        :param str path: TIFF檔案路徑。
        :param str folder_name: 存儲資料夾名稱，如果為None則自動命名。
        """
        img = Image.open(path)
        file_name_with_ext = os.path.basename(path)  # 取出文件名(包含副檔名)
        file_name, _ = os.path.splitext(file_name_with_ext)  # 去除副檔名

        if folder_name is None:
            # 根據檔名的後綴來判斷屬於哪種類型並命名資料夾
            if '_py_pure_noise' in file_name:
                folder_name = 'pure_noise'
            elif '_py_deskew' in file_name:
                folder_name = 'deskew'
            elif '_py' in file_name:
                folder_name = 'process'
            else:
                folder_name = 'org'

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        for page in range(img.n_frames):
            img.seek(page)
            tmp_img = img.convert("1")
            save_path = f"./{folder_name}/{file_name}_page{str(page + 1).zfill(3)}.tif"
            print(save_path)
            tmp_img.save(save_path, dpi=(600, 600), compression="tiff_lzw")

    def manage_single_page(self, path, page, save=False, show=False, output_path=None):
        """
        查看或儲存單一頁面的TIFF圖片。

        :param path: TIFF檔案的路徑。
        :param page: 指定想要管理的頁數。
        :param save: 是否要儲存該頁，預設為False。
        :param show: 是否要顯示該頁，預設為False。
        :param output_path: 若儲存，儲存的路徑。
        :return: 處理後的圖片物件。
        """
        img = Image.open(path)
        img.seek(page)
        if show:
            img.show()
        if save or output_path:
            save_path = output_path or f"{path[:-4]}_page{str(page).zfill(3)}.tif"
            print(save_path)
            img.save(save_path, dpi=(600, 600), compression="tiff_lzw")
        return img


if __name__ == '__main__':
    # 將_path替換成想要拆頁的tif檔路徑執行即可
    _path = r"./test_file.tif"
    tif_tools = TifTools()
    # 分割出多頁tif檔案成單一tif檔案
    # tif_tools.save_all_page(_path)

    # 讀取或是儲存單一頁圖片
    tif_tools.manage_single_page(_path, 1, show=True)
