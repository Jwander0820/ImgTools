from __future__ import annotations

from typing import Any


def pick_paths(mode: str, *, title: str = "選擇檔案", default_name: str = "") -> list[str]:
    """Open an OS-native picker for the local-only web UI."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
        root.update()
        options: dict[str, Any] = {"parent": root, "title": title}
        if mode == "folder":
            selected = filedialog.askdirectory(**options)
        elif mode == "files":
            selected = filedialog.askopenfilenames(**options)
        elif mode == "save":
            if default_name:
                options["initialfile"] = default_name
            selected = filedialog.asksaveasfilename(**options)
        else:
            selected = filedialog.askopenfilename(**options)
    finally:
        root.destroy()

    if not selected:
        return []
    if isinstance(selected, (tuple, list)):
        return [str(path) for path in selected]
    return [str(selected)]
