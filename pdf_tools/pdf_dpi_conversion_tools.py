import argparse

import fitz
import numpy as np
from PIL import Image


class PDFOperator:
    STANDARD_DPI = 72.0

    def __init__(self, file_path):
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        self.total_pages = len(self.doc)

    def dimensions(self, page_number=0):
        """
        獲取指定頁面的原始尺寸(寬和高)
        :param page_number: 頁碼(從0開始)
        :return:
        """
        page_rect = self.doc[page_number].rect
        return page_rect.width, page_rect.height

    def dimensions_in_inches(self, page_number=0):
        """
        獲取指定頁面的原始尺寸（寬和高），並將其轉換為英寸
        :param page_number: 頁碼(從0開始)
        :return:
        """
        width, height = self.dimensions(page_number)
        return width / self.STANDARD_DPI, height / self.STANDARD_DPI

    def dimensions_at_dpi(self, page_number=0, dpi=None):
        """
        獲取指定頁面在特定DPI下的尺寸（寬和高）
        :param page_number: 頁碼(從0開始)
        :param dpi: 目標DPI
        :return: 目標DPI下的尺寸（寬和高）
        """
        pix = self.capture_full_page(page_number=page_number, dpi=dpi)
        return pix.width, pix.height

    def capture_region(self, rect, page_number=0, dpi=None):
        """
        截取PDF指定頁面的指定區域
        :param rect: 需要截取的區域的座標
        :param page_number: 頁碼(從0開始)
        :param dpi: 設定的DPI值
        :return:
        """
        page = self.doc[page_number]
        # 若提供了 dpi 則調整縮放
        if dpi:
            zoom = dpi / self.STANDARD_DPI
            matrix = fitz.Matrix(zoom, zoom)
        else:
            matrix = fitz.Matrix(1, 1)

        rect = fitz.Rect(*rect)
        pix = page.get_pixmap(clip=rect, matrix=matrix)
        return pix

    def capture_full_page(self, page_number=0, dpi=None):
        """
        截取PDF指定頁面
        :param page_number: 頁碼(從0開始)
        :param dpi: 設定的DPI值
        :return:
        """
        page = self.doc[page_number]
        # 若提供了 dpi 則調整縮放
        if dpi:
            zoom = dpi / self.STANDARD_DPI
            matrix = fitz.Matrix(zoom, zoom)
        else:
            matrix = fitz.Matrix(1, 1)

        pix = page.get_pixmap(matrix=matrix)
        return pix

    def save_page_as_image(self, page_number, file_name, dpi=None):
        """
        將指定頁數的 PDF 內容儲存為 PNG 檔案。

        :param page_number: 要儲存的 PDF 頁碼，從 0 開始。
        :param file_name: 儲存 PNG 檔案的名稱。
        :param dpi: 指定圖像的解析度，若為 None 則使用標準 DPI。
        :return: None
        """
        pix = self.capture_full_page(page_number=page_number, dpi=dpi)
        self.save_image(pix, file_name)

    def save_image(self, img, file_name):
        """
        儲存截取的圖像
        :param img: 圖像資料
        :param file_name: 儲存圖像的文件名
        :return:
        """
        if isinstance(img, np.ndarray):
            img = Image.fromarray(np.uint8(img))
        img.save(file_name)


def main():
    """
    20240219；PDF指定DPI抽取圖片工具，使用PDFOperator做轉換，可簡易包裝成exe
    應該不需要時常更新，留存供參考
    壓成EXE直接使用 pyinstaller -F ./folder/XXX.py 即可
    :return:
    """
    parser = argparse.ArgumentParser(
        description='Convert a specific page of a PDF to an image with optional DPI setting.')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file.')
    parser.add_argument('--page', type=int, default=1, help='Page number to convert (default: 1).')
    parser.add_argument('--dpi', type=int, default=96, help='DPI for the image (default: 96).')
    args = parser.parse_args()

    # 注意：使用者界面中的頁碼從1開始，但內部實現從0開始，所以進行了-1操作
    page = args.page - 1
    dpi = args.dpi

    processor = PDFOperator(args.pdf_path)
    # 檔案名稱中加入指定的頁碼
    file_name = args.pdf_path.replace('.pdf', f'_page{args.page}.png')
    processor.save_page_as_image(page, file_name, dpi=dpi)


if __name__ == '__main__':
    main()
