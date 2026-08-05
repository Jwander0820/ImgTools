from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


PARAM_LABELS = {
    "input_path": "輸入檔案",
    "input_paths": "輸入圖片",
    "folder_path": "圖片資料夾",
    "target_folder": "目標資料夾",
    "output_path": "自訂輸出位置",
    "output_dir": "自訂輸出資料夾",
    "page": "頁碼",
    "pdf_path": "PDF 檔案",
    "dpi": "輸出解析度（DPI）",
    "password": "PDF 密碼",
    "method": "讀取方式",
    "target": "尋找文字",
    "replacement": "替換成",
    "confirm": "套用變更",
    "overwrite": "允許覆寫",
    "duration": "每幀時間（毫秒）",
    "loop": "循環次數",
    "color_mode": "色彩模式",
    "text": "浮水印文字",
    "font_path": "自訂字型",
    "font_size": "字型大小",
    "rotation": "旋轉角度",
    "opacity": "透明度",
    "color": "浮水印顏色",
    "repeat": "重複平鋪",
    "repeat_spacing": "平鋪間距",
    "position": "浮水印位置",
    "margin": "邊界距離",
    "position_x": "自訂 X 座標",
    "position_y": "自訂 Y 座標",
    "fps": "輸出影格率（FPS）",
    "compression": "TIF 壓縮方式",
    "dilate_iterations": "文字連接強度",
    "min_area": "最小區域面積",
    "padding_ratio": "透明邊界比例",
    "canvas_size": "固定畫布尺寸",
    "ignore_bottom_ratio": "忽略底部比例",
    "allow_low_confidence": "接受低信心配對",
    "crop_subtitles": "保留最底部字幕",
    "subtitle_crop_ratio": "字幕區高度比例",
    "subtitle_top_ratio": "字幕帶起點比例",
    "line_spacing": "每句間距（像素）",
}

DEFAULT_ADVANCED_PARAMS = {
    "output_path",
    "output_dir",
    "overwrite",
    "password",
    "font_path",
    "font_size",
    "color_mode",
    "ignore_bottom_ratio",
    "allow_low_confidence",
    "crop_subtitles",
    "subtitle_crop_ratio",
    "loop",
    "rotation",
    "opacity",
    "position",
    "margin",
    "position_x",
    "position_y",
    "fps",
    "compression",
    "dilate_iterations",
    "min_area",
    "padding_ratio",
    "canvas_size",
}


@dataclass(frozen=True)
class ToolParam:
    name: str
    type: str = "string"
    required: bool = False
    default: Any = None
    description: str = ""
    choices: tuple[str, ...] = ()
    label: str = ""
    advanced: bool = False
    default_hint: str = ""
    source_default_hint: str = ""
    min_items: int | None = None
    max_items: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "label": self.label or PARAM_LABELS.get(self.name, self.name),
            "advanced": self.advanced or self.name in DEFAULT_ADVANCED_PARAMS,
        }
        if self.default is not None:
            data["default"] = self.default
        if self.choices:
            data["choices"] = list(self.choices)
        if self.default_hint:
            data["default_hint"] = self.default_hint
        if self.source_default_hint:
            data["source_default_hint"] = self.source_default_hint
        if self.min_items is not None:
            data["min_items"] = self.min_items
        if self.max_items is not None:
            data["max_items"] = self.max_items
        return data


@dataclass(frozen=True)
class ToolSpec:
    action: str
    title: str
    category: str
    description: str
    params: tuple[ToolParam, ...]
    handler: ToolHandler
    danger_level: str = "low"
    featured: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "params": [param.to_dict() for param in self.params],
            "danger_level": self.danger_level,
            "featured": self.featured,
        }


def _specs() -> list[ToolSpec]:
    from imgtools.core import crop, gif, merge, metadata, pdf, rename, tif, video, watermark

    return [
        ToolSpec(
            action="metadata.read_tif_tags",
            title="讀取 TIF metadata",
            category="metadata",
            description="用 PIL、tifftools 或 exifread 讀取 TIF / EXIF metadata。",
            params=(
                ToolParam("input_path", "path", True, description="輸入圖片路徑"),
                ToolParam(
                    "method",
                    "string",
                    False,
                    "pil",
                    "讀取方式",
                    choices=("pil", "tifftools", "exifread"),
                ),
            ),
            handler=metadata.read_tif_tags,
        ),
        ToolSpec(
            action="rename.files_replace",
            title="批次替換檔名字串",
            category="rename",
            description="批次替換檔名中的指定字串。預設 dry-run。",
            params=(
                ToolParam("target_folder", "folder", True, description="目標資料夾"),
                ToolParam("target", "string", True, description="要被替換的字串"),
                ToolParam("replacement", "string", True, description="替換後字串"),
                ToolParam("confirm", "bool", False, False, "true 才會實際改名"),
            ),
            handler=rename.files_replace,
            danger_level="high",
        ),
        ToolSpec(
            action="rename.folders_replace",
            title="批次替換資料夾名稱",
            category="rename",
            description="批次替換資料夾名稱中的指定字串。預設 dry-run。",
            params=(
                ToolParam("target_folder", "folder", True, description="目標資料夾"),
                ToolParam("target", "string", True, description="要被替換的字串"),
                ToolParam("replacement", "string", True, description="替換後字串"),
                ToolParam("confirm", "bool", False, False, "true 才會實際改名"),
            ),
            handler=rename.folders_replace,
            danger_level="high",
        ),
        ToolSpec(
            action="pdf.render_page",
            title="PDF 單頁轉 PNG",
            category="pdf",
            description="將 PDF 指定頁面依 DPI 輸出為 PNG。",
            params=(
                ToolParam("pdf_path", "path", True, description="輸入 PDF 路徑"),
                ToolParam("page", "int", False, 1, "頁碼，從 1 開始"),
                ToolParam("dpi", "int", False, 192, "輸出 DPI"),
                ToolParam("password", "string", False, description="PDF 密碼，沒有可留空"),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到 PDF 旁。",
                    default_hint="PDF 旁的 output_pageNNN.png",
                    source_default_hint="PDF 旁的 <原始檔名>_pageNNN.png",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=pdf.render_page,
        ),
        ToolSpec(
            action="pdf.render_all_pages",
            title="PDF 全頁轉 PNG",
            category="pdf",
            description="將 PDF 所有頁面依 DPI 輸出為 PNG。",
            params=(
                ToolParam("pdf_path", "path", True, description="輸入 PDF 路徑"),
                ToolParam("dpi", "int", False, 192, "輸出 DPI"),
                ToolParam("password", "string", False, description="PDF 密碼，沒有可留空"),
                ToolParam(
                    "output_dir",
                    "folder",
                    False,
                    description="留白時在 PDF 旁建立專用資料夾。",
                    default_hint="PDF 旁的 output_pages 資料夾",
                    source_default_hint="PDF 旁的 <原始檔名>_pages 資料夾",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=pdf.render_all_pages,
            featured=True,
        ),
        ToolSpec(
            action="merge.images_to_pdf",
            title="圖片合併為 PDF",
            category="merge",
            description="將資料夾內圖片依檔名排序後合併為 PDF。",
            params=(
                ToolParam("folder_path", "folder", True, description="輸入圖片資料夾"),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到圖片資料夾；既有檔案不會被覆寫。",
                    default_hint="同資料夾的 output.pdf",
                    source_default_hint="同資料夾的 <資料夾名稱>.pdf",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=merge.images_to_pdf,
            featured=True,
        ),
        ToolSpec(
            action="merge.images_to_tif",
            title="圖片合併為多頁 TIF",
            category="merge",
            description="將資料夾內圖片依檔名排序後合併為多頁 TIF。",
            params=(
                ToolParam("folder_path", "folder", True, description="輸入圖片資料夾"),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到圖片資料夾；既有檔案會自動加上編號。",
                    default_hint="同資料夾的 output.tif",
                    source_default_hint="同資料夾的 <資料夾名稱>.tif",
                ),
                ToolParam(
                    "compression",
                    "string",
                    False,
                    "tiff_lzw",
                    "輸出 TIF 的壓縮方式",
                    choices=("tiff_lzw", "tiff_adobe_deflate", "raw"),
                ),
                ToolParam(
                    "color_mode",
                    "string",
                    False,
                    "RGB",
                    "統一每頁的色彩模式",
                    choices=("RGB", "RGBA", "L"),
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=tif.images_to_tif,
            featured=True,
        ),
        ToolSpec(
            action="merge.stack_vertical",
            title="快速直向疊圖",
            category="merge",
            description="將 2～4 張同寬圖片依指定順序由上到下疊成一張 PNG，不縮放原圖。",
            params=(
                ToolParam(
                    "input_paths",
                    "path_list",
                    True,
                    description="依由上到下的順序選擇 2～4 張同寬圖片",
                    min_items=2,
                    max_items=4,
                ),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到第一張圖片旁；既有檔案會自動加上編號。",
                    default_hint="第一張圖片旁的 output.png",
                    source_default_hint="第一張圖片旁的 <第一張檔名>.png",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=merge.stack_vertical,
            featured=True,
        ),
        ToolSpec(
            action="merge.dialogue_stack",
            title="台詞疊圖",
            category="merge",
            description="保留第一張完整畫面，將後續圖片的全寬字幕帶依敘事順序向下排列並即時預覽。",
            params=(
                ToolParam(
                    "input_paths",
                    "path_list",
                    True,
                    description="依台詞發生順序選擇 2～12 張同尺寸圖片",
                    min_items=2,
                    max_items=12,
                ),
                ToolParam(
                    "subtitle_top_ratio",
                    "float",
                    False,
                    0.88,
                    "從畫面高度的此比例開始擷取全寬字幕帶",
                ),
                ToolParam(
                    "line_spacing",
                    "int",
                    False,
                    85,
                    "每增加一句台詞，成品向下增加的像素高度",
                ),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到第一張圖片旁；既有檔案會自動加上編號。",
                    default_hint="第一張圖片旁的 output.png",
                    source_default_hint="第一張圖片旁的 <第一張檔名>.png",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=merge.dialogue_stack,
            featured=True,
        ),
        ToolSpec(
            action="merge.panorama_translation",
            title="動畫平移長截圖",
            category="merge",
            description="依指定順序偵測圖片間的純平移，合併為一張長截圖。",
            params=(
                ToolParam(
                    "input_paths",
                    "path_list",
                    True,
                    description="依合併順序輸入圖片路徑，每行一個",
                ),
                ToolParam(
                    "ignore_bottom_ratio",
                    "float",
                    False,
                    0.15,
                    "比對時忽略底部字幕區的比例",
                ),
                ToolParam(
                    "allow_low_confidence",
                    "bool",
                    False,
                    True,
                    "依檔名時間碼推算大位移並接受少量一致特徵",
                ),
                ToolParam(
                    "crop_subtitles",
                    "bool",
                    False,
                    True,
                    "在重疊區於字幕前切換來源影格，只保留最底部字幕",
                ),
                ToolParam(
                    "subtitle_crop_ratio",
                    "float",
                    False,
                    0.08,
                    "字幕帶高度比例，用於選擇重疊區接縫",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=merge.panorama_translation,
        ),
        ToolSpec(
            action="tif.split_pages",
            title="拆分多頁 TIF",
            category="tif",
            description="將多頁 TIF 拆成依頁碼命名的單頁 TIF。",
            params=(
                ToolParam("input_path", "path", True, description="輸入多頁 TIF 路徑"),
                ToolParam(
                    "output_dir",
                    "folder",
                    False,
                    description="留白時在 TIF 旁建立專用資料夾。",
                    default_hint="TIF 旁的 output_pages 資料夾",
                    source_default_hint="TIF 旁的 <原始檔名>_pages 資料夾",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=tif.split_pages,
        ),
        ToolSpec(
            action="tif.extract_page",
            title="抽出單頁 TIF",
            category="tif",
            description="從多頁 TIF 抽出指定頁面，頁碼從 1 開始。",
            params=(
                ToolParam("input_path", "path", True, description="輸入多頁 TIF 路徑"),
                ToolParam("page", "int", False, 1, "頁碼，從 1 開始"),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到原 TIF 旁。",
                    default_hint="TIF 旁的 output_pageNNN.tif",
                    source_default_hint="TIF 旁的 <原始檔名>_pageNNN.tif",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=tif.extract_page,
        ),
        ToolSpec(
            action="gif.images_to_gif",
            title="圖片序列轉 GIF",
            category="gif",
            description="將資料夾內圖片依檔名排序後輸出為 GIF。",
            params=(
                ToolParam("folder_path", "folder", True, description="輸入圖片資料夾"),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到圖片資料夾；既有檔案會自動加上編號。",
                    default_hint="同資料夾的 output.gif",
                    source_default_hint="同資料夾的 <資料夾名稱>.gif",
                ),
                ToolParam("duration", "int", False, 40, "每幀顯示毫秒數"),
                ToolParam("loop", "int", False, 0, "循環次數，0 表示無限循環"),
                ToolParam(
                    "color_mode", "string", False, "RGBA", "圖片色彩模式",
                    choices=("RGBA", "RGB", "L"),
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=gif.images_to_gif,
            featured=True,
        ),
        ToolSpec(
            action="video.extract_frames",
            title="MP4 拆幀",
            category="video",
            description="將 MP4 的所有影格依序輸出為 PNG。",
            params=(
                ToolParam("input_path", "path", True, description="輸入 MP4 路徑"),
                ToolParam(
                    "output_dir",
                    "folder",
                    False,
                    description="留白時在 MP4 旁建立專用資料夾；既有資料夾會自動加上編號。",
                    default_hint="MP4 旁的 output_frames 資料夾",
                    source_default_hint="MP4 旁的 <原始檔名>_frames 資料夾",
                ),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出影格"),
            ),
            handler=video.extract_frames,
            featured=True,
        ),
        ToolSpec(
            action="gif.mp4_to_gif",
            title="MP4 轉 GIF",
            category="video",
            description="將 MP4 轉成適合快速分享的 GIF 動畫。",
            params=(
                ToolParam("input_path", "path", True, description="輸入 MP4 路徑"),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到 MP4 同一資料夾；既有檔案會自動加上編號。",
                    default_hint="同資料夾的 output.gif",
                    source_default_hint="同資料夾的 <原始檔名>.gif",
                ),
                ToolParam("fps", "int", False, 12, "GIF 每秒影格數"),
                ToolParam("loop", "int", False, 0, "循環次數，0 表示無限循環"),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=video.mp4_to_gif,
            featured=True,
        ),
        ToolSpec(
            action="gif.gif_to_mp4",
            title="GIF 轉 MP4",
            category="video",
            description="將 GIF 轉成相容性高的 H.264 MP4。",
            params=(
                ToolParam("input_path", "path", True, description="輸入 GIF 路徑"),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時輸出到 GIF 同一資料夾；既有檔案會自動加上編號。",
                    default_hint="同資料夾的 output.mp4",
                    source_default_hint="同資料夾的 <原始檔名>.mp4",
                ),
                ToolParam("fps", "int", False, 30, "MP4 每秒影格數"),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=video.gif_to_mp4,
            featured=True,
        ),
        ToolSpec(
            action="crop.text_regions",
            title="擷取文字／圖章區域",
            category="crop",
            description="從淺色背景偵測文字或圖章區塊，輸出透明 PNG。",
            params=(
                ToolParam("input_path", "path", True, description="白底或淺色背景圖片"),
                ToolParam(
                    "output_dir",
                    "folder",
                    False,
                    description="留白時在來源旁建立專用資料夾。",
                    default_hint="圖片旁的 output_regions 資料夾",
                    source_default_hint="圖片旁的 <原始檔名>_regions 資料夾",
                ),
                ToolParam("dilate_iterations", "int", False, 10, "連接鄰近筆畫的膨脹次數"),
                ToolParam("min_area", "int", False, 64, "忽略面積小於此值的雜點"),
                ToolParam("padding_ratio", "float", False, 0.1, "區域四周增加的透明邊界比例"),
                ToolParam("canvas_size", "int", False, 0, "固定正方形畫布邊長；0 表示自動"),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=crop.text_regions,
        ),
        ToolSpec(
            action="watermark.text",
            title="加入文字浮水印",
            category="watermark",
            description="在圖片指定位置加入可旋轉的半透明文字浮水印。",
            params=(
                ToolParam("input_path", "path", False, description="單張圖片相容輸入；多張時請使用圖片清單。"),
                ToolParam("input_paths", "path_list", False, description="可一次選擇一張或多張圖片。", min_items=1),
                ToolParam(
                    "output_path",
                    "path",
                    False,
                    description="留白時使用原圖片副檔名，輸出到同一資料夾。",
                    default_hint="同資料夾的 output.<原副檔名>",
                    source_default_hint="同資料夾的 <原始檔名>-2.<原副檔名>",
                ),
                ToolParam("text", "string", True, description="浮水印文字"),
                ToolParam("font_path", "path", False, description="自訂字型檔路徑"),
                ToolParam("font_size", "int", False, 0, "字型大小，0 表示自動"),
                ToolParam("rotation", "float", False, 30, "旋轉角度"),
                ToolParam("opacity", "int", False, 64, "透明度，0 到 255"),
                ToolParam("color", "string", False, "#000000", "浮水印顏色"),
                ToolParam("repeat", "bool", False, False, "重複平鋪文字以覆蓋整張圖片"),
                ToolParam("repeat_spacing", "int", False, 100, "重複文字之間的間距（像素）"),
                ToolParam(
                    "position",
                    "string",
                    False,
                    "center",
                    "使用預設位置，或選擇 custom 後填入座標",
                    choices=(
                        "center",
                        "top_left",
                        "top_right",
                        "bottom_left",
                        "bottom_right",
                        "custom",
                    ),
                ),
                ToolParam("margin", "int", False, 16, "四角位置與圖片邊界的距離"),
                ToolParam("position_x", "int", False, 0, "custom 模式的左上角 X 座標"),
                ToolParam("position_y", "int", False, 0, "custom 模式的左上角 Y 座標"),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=watermark.add_text,
            featured=True,
        ),
        ToolSpec(
            action="watermark.batch_text",
            title="批次加入文字浮水印",
            category="watermark",
            description="將同一組文字浮水印設定套用到多張圖片，並集中輸出處理結果。",
            params=(
                ToolParam("input_paths", "path_list", True, description="要處理的圖片，可一次選取多張。", min_items=1),
                ToolParam(
                    "output_dir",
                    "folder",
                    False,
                    description="批次結果輸出資料夾。",
                    default_hint="輸入圖片旁的 watermarked 資料夾",
                ),
                ToolParam("text", "string", True, description="浮水印文字"),
                ToolParam("font_path", "path", False, description="選填的字型檔案"),
                ToolParam("font_size", "int", False, 0, "字型大小，0 表示依圖片自動"),
                ToolParam("rotation", "float", False, 30, "旋轉角度"),
                ToolParam("opacity", "int", False, 64, "透明度，0 到 255"),
                ToolParam("color", "string", False, "#000000", "浮水印顏色"),
                ToolParam("repeat", "bool", False, False, "重複平鋪文字以覆蓋整張圖片"),
                ToolParam("repeat_spacing", "int", False, 100, "重複文字之間的間距（像素）"),
                ToolParam(
                    "position",
                    "string",
                    False,
                    "center",
                    "浮水印位置",
                    choices=(
                        "center",
                        "top_left",
                        "top_right",
                        "bottom_left",
                        "bottom_right",
                        "custom",
                    ),
                ),
                ToolParam("margin", "int", False, 16, "邊界距離"),
                ToolParam("position_x", "int", False, 0, "自訂 X 座標"),
                ToolParam("position_y", "int", False, 0, "自訂 Y 座標"),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔案"),
            ),
            handler=watermark.add_text_batch,
            featured=True,
        ),
    ]


def get_registry() -> dict[str, ToolSpec]:
    return {spec.action: spec for spec in _specs()}


def list_tools() -> list[dict[str, Any]]:
    return [spec.to_dict() for spec in _specs()]


def get_tool(action: str) -> ToolSpec:
    registry = get_registry()
    if action not in registry:
        raise KeyError(action)
    return registry[action]
