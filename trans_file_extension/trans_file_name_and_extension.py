import glob
import os


def trans_file_extension(target_folder, target, convert2):
    back = len(target)
    for root, dirs, files in os.walk(target_folder, topdown=False):  # 取得路徑下所有檔案的根目錄與檔名
        for index, file_name in enumerate(files):  # 循序讀取檔名清單
            _, extension = os.path.splitext(file_name)
            if extension == target:
                org_img_name = os.path.join(root, file_name)  # 組合成完整路徑
                new_img_name = org_img_name[:-back] + convert2
                os.rename(org_img_name, new_img_name)
                print(new_img_name)


def trans_folder_name(target_folder, target, convert2):
    back = len(target)
    for root, dirs, files in os.walk(target_folder, topdown=False):  # 取得路徑下所有檔案的根目錄與檔名
        for index, dir_name in enumerate(dirs):  # 循序讀取檔名清單
            if target in dir_name:
                org_img_name = dir_name
                new_img_name = dir_name[:-back] + convert2
                org_img_path = os.path.join(root, dir_name)  # 組合成完整路徑
                new_img_path = os.path.join(root, new_img_name)
                print(f"{org_img_name} trans2 {new_img_name}")
                os.rename(org_img_path, new_img_path)


if __name__ == "__main__":
    _target_folder = r"C:\Users\Jwander\Downloads\輝夜姬想讓人告白～天才們的戀愛頭腦戰～"
    _target = "话"
    _convert = ""
    trans_folder_name(_target_folder, _target, _convert)
