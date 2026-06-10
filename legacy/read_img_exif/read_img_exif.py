import numpy as np
import tifftools
import exifread
from PIL import Image, TiffTags


class ReadExif:
    @staticmethod
    def pil_tag_v2(path):
        # 使用Image開啟圖片，取得檔案的exif資訊，以代號形式呈現，圖像不得做轉換，否則讀不出來
        img = Image.open(path)
        img_tags = img.tag_v2
        return img_tags

    @staticmethod
    def tifftools_ifds(path):
        # 使用tifftools.read_tiff開啟圖片，取得檔案的exif資訊，以代號形式呈現，內有各資料詳細項目
        img = tifftools.read_tiff(path)
        img_tags = img["ifds"][0]["tags"]
        return img_tags

    @staticmethod
    def exifread_ifds(path):
        # 直接開啟檔案讀取整個檔案的exif資訊，讀取多幀tif時非常好用，會呈現多頁tif的每頁資訊，exif資訊以名稱方式呈現較直觀
        with open(path, 'rb') as f:
            img_tags = exifread.process_file(f)
        return img_tags


if __name__ == "__main__":
    _path = "./test.tif"

    # 1. 透過PIL的tag_v2讀取檔案的exif資訊，各代號的意義可以參見網路上的說明
    _tag = ReadExif.pil_tag_v2(_path)
    for key in _tag:
        print(key, _tag[key])

    # 2. 透過tifftools讀取檔案，並提取出exif資訊
    _tag = ReadExif.tifftools_ifds(_path)
    for key in _tag:
        print(key, _tag[key])

    # 3. 透過直接開啟檔案，使用exifread提取出exif資訊
    _tag = ReadExif.exifread_ifds(_path)
    for key in _tag:
        print(key, _tag[key])

    # !image.save使用tiffinfo改寫tif tag的方法
    tiffinfo = {262: (1,)}  # 撰寫tiffinfo的字典，各編號對應的tag可以查詢，編號262為PhotometricInterpretation(光度解釋)
    _img = Image.open("./test.tif")
    _img.save("./new.tif", dpi=(600, 600), compression="group4", tiffinfo=tiffinfo)

    # !使用tifftools改寫tif tag的方法 (謹慎使用)
    info = tifftools.read_tiff('test.tif')  # 打開tif
    print(info['ifds'][0]['tags'][262])
    # 編寫要改寫的tif tag的參數，此處也是以修改262光度解釋為例
    info['ifds'][0]['tags'][262] = {
        'datatype': 3,
        'count': 1,
        'datapos': 78,
        'data': [0]
    }
    print(info['ifds'][0]['tags'][262])
    # tifftools.write_tiff(info, 'new.tif')  # 儲存圖片
