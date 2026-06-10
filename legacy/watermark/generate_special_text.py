import random
from PIL import Image, ImageDraw, ImageFont
from crop_text import crop_text

def generate_line_pattern_image(width, height, min_line_length, max_line_length, line_spacing, angle):
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)

    for y in range(0, height, line_spacing):
        for x in range(0, width, line_spacing):
            line_length = random.randint(min_line_length, max_line_length)
            x2 = x + int(line_length * 1.0 * random.uniform(0.9, 1.1))
            y2 = y + int(line_length * 1.0 * random.uniform(0.9, 1.1))
            draw.line([(x, y), (x2, y2)], fill=0, width=1)

    image = image.rotate(angle, fillcolor=1)
    return image


def apply_text_mask(background_image, text, font_path, font_size):
    # 創建一個與背景圖像相同大小的透明圖像
    mask_image = Image.new('1', background_image.size, 0)

    # 選擇字體和大小
    font = ImageFont.truetype(font_path, font_size)

    # 在遮罩圖像上繪製自定義的文字
    draw = ImageDraw.Draw(mask_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    x = (background_image.size[0] - text_width) // 2
    y = (background_image.size[1] - text_height) // 2
    draw.text((x, y), text, font=font, fill=1)

    # 將遮罩應用到背景圖像
    masked_image = Image.new('1', background_image.size)
    for x in range(background_image.size[0]):
        for y in range(background_image.size[1]):
            if mask_image.getpixel((x, y)):
                masked_image.putpixel((x, y), background_image.getpixel((x, y)))
            else:
                masked_image.putpixel((x, y), 1)

    return masked_image


if __name__ == '__main__':
    width = 600
    height = 600
    min_line_length = 4
    max_line_length = 8
    line_spacing = 4
    angle = 0

    # 生成底圖
    image = generate_line_pattern_image(width, height, min_line_length, max_line_length, line_spacing, angle)
    image.show()
    # image.save("output_image.png")

    # 根據底圖製作特殊自定義文字蒙版，生成特殊文字浮水印
    background_image = generate_line_pattern_image(width, height, min_line_length, max_line_length, line_spacing, angle)
    text = "自定義文字"
    font_path = "msyh.ttc"  # 字體文件的路徑
    font_size = 120

    masked_image = apply_text_mask(background_image, text, font_path, font_size)
    masked_image.show()
    # masked_image.save("masked_image.png")
    # 生成白底黑字圖後，可以串接crop_text，去背圖片