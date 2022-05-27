from PIL import Image, TiffImagePlugin, TiffTags
import tifftools
import numpy as np
import exifread


class ReadExif:
    @staticmethod
    def pil_tag_v2(path):
        # 取得檔案的exif資訊，以代號形式呈現，圖像不得做轉換，否則讀不出來
        img = Image.open(path)
        img_tags = img.tag_v2
        return img_tags

    @staticmethod
    def tifftools_ifds(path):
        img = tifftools.read_tiff(path)
        img_tags = img["ifds"][0]["tags"]
        return img_tags

    @staticmethod
    def exifread_ifds(path):
        with open(path, 'rb') as f:
            img_tags = exifread.process_file(f)
        return img_tags


if __name__ == "__main__":
    _path = "./test.tif"

    # 1. 透過PIL的tag_v2讀取檔案的exif資訊，各代號的意義可以參見
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
