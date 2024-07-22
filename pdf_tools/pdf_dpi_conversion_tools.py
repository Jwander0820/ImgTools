import argparse
import json
import os

import fitz
import numpy as np
from PIL import Image


class PDFOperator:
    STANDARD_DPI = 72.0

    def __init__(self, file_path, password=None):
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        if self.doc.is_encrypted:
            if password:
                self.doc.authenticate(password)
            else:
                raise ValueError("PDF 文件被加密，請使用 --password 提供密碼。")
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


def load_default_dpi():
    """
    讀取設定檔，取得預設dpi，若無設定檔或設定檔參數異常，則欲設dpi為192
    :return:
    """
    config_path = 'config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config = json.load(file)
        default_dpi = config.get('default_dpi', 192)
    else:
        default_dpi = 192  # 如果找不到配置文件，使用默認的 DPI
    print(f'The default DPI setting is {default_dpi}')
    return default_dpi


def save_all_pages_as_images(processor, output_dir, dpi):
    """
    將所有頁面的 PDF 內容儲存為 PNG 檔案
    :param processor: PDFOperator 實例
    :param output_dir: 儲存圖片的目錄
    :param dpi: 指定圖像的解析度
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_name_base = os.path.splitext(os.path.basename(processor.file_path))[0]
    total_pages = processor.total_pages
    for page in range(total_pages):
        file_name = os.path.join(output_dir, f'{file_name_base}_page{str(page + 1).zfill(len(str(total_pages)))}.png')
        processor.save_page_as_image(page, file_name, dpi=dpi)
        print(f'Page {page + 1} has been saved as {file_name}')


def main():
    """
    20240219；PDF指定DPI抽取圖片工具，使用PDFOperator做轉換，可簡易包裝成exe
    應該不需要時常更新，留存供參考
    壓成EXE直接使用 pyinstaller -F ./folder/XXX.py 即可
    :return:
    """
    default_dpi = load_default_dpi()

    parser = argparse.ArgumentParser(
        description='Convert a specific page of a PDF to an image with optional DPI setting.')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file.')
    parser.add_argument('--page', type=int, default=1, help='Page number to convert (default: 1).')
    parser.add_argument('--dpi', type=int, default=default_dpi, help='DPI for the image (default: 192).')
    parser.add_argument('--password', type=str, default=None, help='Password for the encrypted PDF file.')
    parser.add_argument('--all', action='store_true', help='Convert all pages of the PDF.')
    args = parser.parse_args()

    try:
        processor = PDFOperator(args.pdf_path, args.password)
        dpi = args.dpi

        if args.all:
            file_name_base = os.path.splitext(os.path.basename(processor.file_path))[0]
            output_dir = os.path.join(os.path.dirname(args.pdf_path), file_name_base)
            save_all_pages_as_images(processor, output_dir, dpi)
            print(f'All pages have been saved in {output_dir}')

        else:
            # 注意：使用者界面中的頁碼從1開始，但內部實現從0開始，所以進行了-1操作
            page_number = args.page
            real_page_number = page_number - 1
            file_name_base = args.pdf_path.replace('.pdf', f'')
            file_name = f"{file_name_base}_page{str(page_number).zfill(len(str(processor.total_pages)))}.png"
            processor.save_page_as_image(real_page_number, file_name, dpi=dpi)
            print(f'Page {page_number} has been saved as {file_name}')

    except Exception as e:
        print(e)


def main_test():
    # 測試參數
    pdf_path = r"file_path.pdf"
    password = "password"  # 如果沒有密碼，可以設置為 None

    processor = PDFOperator(pdf_path, password)
    dpi = load_default_dpi()

    # 測試單頁轉換
    page_number = 1
    real_page_number = page_number - 1
    file_name_base = pdf_path.replace('.pdf', f'')
    file_name = f"{file_name_base}_page{str(page_number).zfill(len(str(processor.total_pages)))}.png"
    processor.save_page_as_image(real_page_number, file_name, dpi=dpi)
    print(f'Page {page_number} has been saved as {file_name}')

    # 測試所有頁面轉換
    file_name_base = os.path.splitext(os.path.basename(processor.file_path))[0]
    output_dir = os.path.join(os.path.dirname(pdf_path), file_name_base)
    save_all_pages_as_images(processor, output_dir, dpi)
    print(f'All pages have been saved in {output_dir}')


if __name__ == '__main__':
    main()
