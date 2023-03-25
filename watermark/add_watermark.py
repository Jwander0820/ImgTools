from PIL import Image, ImageDraw, ImageFont


class AddWatermark:
    @staticmethod
    def basic_auto_adaptation(input_image_path, output_image_path, watermark_text,
                              position=None, font_size=None, rotation=None, auto_adapt=True, save_format=None):
        # 打開原始圖像
        base_image = Image.open(input_image_path).convert("RGBA")
        base_width, base_height = base_image.size

        # 如果未指定字體大小，則自動適應
        if not font_size and auto_adapt:
            font_size = int(min(base_width, base_height) * 0.2)

        # 選擇字體和大小
        font = ImageFont.truetype("msjhbd.ttc", font_size)

        # 獲取浮水印尺寸
        temp_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        txt_bbox = temp_draw.textbbox((0, 0), watermark_text, font=font)
        txt_width, txt_height = txt_bbox[2] - txt_bbox[0], txt_bbox[3] - txt_bbox[1]

        # 如果未指定位置，則將浮水印放置在左下角到右上角
        if not position and auto_adapt:
            position = (int((base_width - txt_width) / 2), int((base_height - txt_height) / 2))

        # 如果未指定旋轉角度，則設置為45度
        if not rotation:
            rotation = 45

        # 創建一個新的透明圖層，大小與原始圖像相同
        txt_layer = Image.new("RGBA", base_image.size, (255, 255, 255, 0))

        # 在新圖層上繪製水印文字
        draw = ImageDraw.Draw(txt_layer)
        draw.text(position, watermark_text, font=font, fill=(0, 0, 0, 100))

        # 旋轉浮水印圖層
        txt_layer = txt_layer.rotate(rotation, resample=Image.BICUBIC, expand=1)

        # 計算旋轉後的圖層與基本圖像的偏移量
        offset_x = (txt_layer.width - base_image.width) // 2
        offset_y = (txt_layer.height - base_image.height) // 2

        # 將旋轉後的浮水印圖層粘貼到原始圖像上
        base_image.paste(txt_layer, (-offset_x, -offset_y), txt_layer)

        # 保存帶有浮水印的圖像
        if save_format:
            base_image = base_image.convert(save_format)
            base_image.save(output_image_path, dpi=(300, 300), compression='group4')
            return
        else:
            base_image.save(output_image_path, dpi=(300, 300), compression='tiff_lzw')

if __name__ == '__main__':
    # 使用範例
    input_image_path = "../read_img_exif/test.tif"
    output_image_path = "./image_with_watermark.tif"
    watermark_text = "版權所有"

    AddWatermark.basic_auto_adaptation(input_image_path, output_image_path, watermark_text, save_format="1")
