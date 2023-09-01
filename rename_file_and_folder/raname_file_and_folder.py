import os


def rename_files_by_string(target_folder, target, convert2):
    """
    依據目標字串(target)對指定資料夾(target_folder)內 所有檔案 進行重新命名。
    :param target_folder:待操作的目標資料夾的路徑
    :param target:目標字串，該字串在檔名中將被替換
    :param convert2:用於替換目標子串的新字串
    :return:
    """
    for root, _, files in os.walk(target_folder, topdown=False):
        for file_name in files:
            if target in file_name:
                new_file_name = file_name.replace(target, convert2)
                org_file_path = os.path.join(root, file_name)
                new_file_path = os.path.join(root, new_file_name)

                # 檢查新檔名是否已存在
                if os.path.exists(new_file_path):
                    print(f"Error: {new_file_name} already exists.")
                    continue

                os.rename(org_file_path, new_file_path)
                print(f"{org_file_path} renamed to {new_file_path}")


def rename_folder_by_string(target_folder, target, convert2):
    """
    依據目標字串(target)對指定資料夾(target_folder)內的 所有子資料夾 進行重新命名
    :param target_folder:待操作的目標資料夾的路徑
    :param target:目標字串，該字串在資料夾名中將被替換
    :param convert2:用於替換目標字串的新字串
    :return:
    """
    for root, dirs, _ in os.walk(target_folder, topdown=False):  # 取得路徑下所有檔案的根目錄與檔名
        for dir_name in dirs:  # 循序讀取檔名清單
            if target in dir_name:
                new_img_name = dir_name.replace(target, convert2)

                # 檢查新名稱是否存在
                org_img_path = os.path.join(root, dir_name)  # 組合成完整路徑
                new_img_path = os.path.join(root, new_img_name)

                if os.path.exists(new_img_path):
                    print(f"Error: {new_img_name} already exists.")
                    continue

                print(f"{dir_name} renamed to {new_img_name}")
                os.rename(org_img_path, new_img_path)


def create_test_files(target_folder, prefix, suffix, file_count=5):
    """
    在指定的目標資料夾(target_folder)中，生成指定數量(file_count)的測試檔案
    :param target_folder:檔案將生成在此資料夾內
    :param prefix:檔名前綴
    :param suffix:檔名後綴(通常是副檔名)
    :param file_count:要生成的虛擬檔案數量，預設為 5
    :return:
    """
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    for i in range(file_count):
        dummy_file_name = f"{prefix}{chr(65 + i)}{suffix}"
        dummy_file_path = os.path.join(target_folder, dummy_file_name)

        with open(dummy_file_path, "w") as f:
            f.write("This is a dummy file.")

    print(f"{file_count} dummy files have been created.")


if __name__ == "__main__":
    target_folder = "./test_folder"
    target = "測試文字"
    convert = "替換文字"

    # 生成測試文件
    create_test_files(target_folder, target, ".txt")

    # 替換檔案名中的指定字元
    rename_files_by_string(target_folder, target, convert)
    rename_files_by_string(target_folder, ".txt", ".log")

    # 替換文件夾名稱
    rename_folder_by_string("./", "test", "測試")
