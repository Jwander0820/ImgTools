from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolParam:
    name: str
    type: str = "string"
    required: bool = False
    default: Any = None
    description: str = ""
    choices: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }
        if self.default is not None:
            data["default"] = self.default
        if self.choices:
            data["choices"] = list(self.choices)
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "params": [param.to_dict() for param in self.params],
            "danger_level": self.danger_level,
        }


def _specs() -> list[ToolSpec]:
    from imgtools.core import merge, metadata, pdf, rename

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
                ToolParam("output_path", "path", False, description="輸出 PNG 路徑"),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=pdf.render_page,
        ),
        ToolSpec(
            action="merge.images_to_pdf",
            title="圖片合併為 PDF",
            category="merge",
            description="將資料夾內圖片依檔名排序後合併為 PDF。",
            params=(
                ToolParam("folder_path", "folder", True, description="輸入圖片資料夾"),
                ToolParam("output_path", "path", True, description="輸出 PDF 路徑"),
                ToolParam("overwrite", "bool", False, False, "是否覆寫既有輸出檔"),
            ),
            handler=merge.images_to_pdf,
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
