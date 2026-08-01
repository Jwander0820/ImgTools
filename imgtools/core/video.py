from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .common import (
    abs_path,
    default_output_stem,
    resolve_output_directory,
    resolve_output_path,
)


class MediaConversionError(RuntimeError):
    error_code = "MEDIA_CONVERSION_ERROR"


def _ffmpeg_executable() -> str:
    configured = os.environ.get("IMGTOOLS_FFMPEG")
    if configured:
        path = Path(configured).expanduser().resolve()
        if path.is_file():
            return str(path)
        raise FileNotFoundError(f"IMGTOOLS_FFMPEG does not exist: {path}")

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        executable = shutil.which("ffmpeg")
        if executable:
            return executable
    raise RuntimeError(
        "ffmpeg is not available. Install imageio-ffmpeg or set IMGTOOLS_FFMPEG."
    )


def _run_ffmpeg(arguments: list[str]) -> None:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    completed = subprocess.run(
        [_ffmpeg_executable(), "-hide_banner", "-loglevel", "error", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or "ffmpeg conversion failed"
        raise MediaConversionError(message)


def extract_frames(params: dict[str, Any]) -> dict[str, Any]:
    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input MP4 does not exist: {input_path}")

    overwrite = bool(params.get("overwrite", False))
    output_stem = default_output_stem(params, input_path)
    output_dir = resolve_output_directory(
        params.get("output_dir"),
        input_path.with_name(f"{output_stem}_frames"),
        overwrite=overwrite,
    )
    frame_pattern = f"{output_stem}_frame_*.png"
    existing_frames = sorted(output_dir.glob(frame_pattern))
    if existing_frames and not overwrite:
        raise FileExistsError(f"Output frames already exist in: {output_dir}")

    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}-",
        dir=output_dir.parent,
    ) as temporary_dir:
        temporary_root = Path(temporary_dir)
        _run_ffmpeg([
            "-n",
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-fps_mode",
            "passthrough",
            "-start_number",
            "1",
            str(temporary_root / f"{output_stem}_frame_%06d.png"),
        ])

        temporary_frames = sorted(temporary_root.glob(frame_pattern))
        if not temporary_frames:
            raise MediaConversionError("No video frames were produced.")

        output_paths = []
        for temporary_frame in temporary_frames:
            output_path = output_dir / temporary_frame.name
            if output_path.exists() and not overwrite:
                raise FileExistsError(f"Output already exists: {output_path}")
            temporary_frame.replace(output_path)
            output_paths.append(output_path)
    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(path) for path in output_paths],
            "output_dir": abs_path(output_dir),
            "frame_count": len(output_paths),
        },
        "warnings": [],
    }


def mp4_to_gif(params: dict[str, Any]) -> dict[str, Any]:
    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input MP4 does not exist: {input_path}")

    fps = int(params.get("fps", 12))
    loop = int(params.get("loop", 0))
    if fps <= 0:
        raise ValueError("fps must be greater than 0")
    if loop < 0:
        raise ValueError("loop must be 0 or greater")
    overwrite = bool(params.get("overwrite", False))
    output_path = resolve_output_path(
        params.get("output_path"),
        input_path.with_name(f"{default_output_stem(params, input_path)}.gif"),
        overwrite=overwrite,
    )

    filter_graph = (
        f"[0:v:0]fps={fps},split[gif_a][gif_b];"
        "[gif_a]palettegen=stats_mode=diff[palette];"
        "[gif_b][palette]paletteuse=dither=sierra2_4a"
    )
    _run_ffmpeg([
        "-y" if overwrite else "-n",
        "-i",
        str(input_path),
        "-filter_complex",
        filter_graph,
        "-loop",
        str(loop),
        str(output_path),
    ])

    return {
        "ok": True,
        "outputs": {"files": [abs_path(output_path)]},
        "warnings": [],
    }


def gif_to_mp4(params: dict[str, Any]) -> dict[str, Any]:
    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input GIF does not exist: {input_path}")

    fps = int(params.get("fps", 30))
    if fps <= 0:
        raise ValueError("fps must be greater than 0")
    overwrite = bool(params.get("overwrite", False))
    output_path = resolve_output_path(
        params.get("output_path"),
        input_path.with_name(f"{default_output_stem(params, input_path)}.mp4"),
        overwrite=overwrite,
    )

    video_filter = (
        f"fps={fps},"
        "pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0:color=black,"
        "format=yuv420p"
    )
    _run_ffmpeg([
        "-y" if overwrite else "-n",
        "-ignore_loop",
        "1",
        "-i",
        str(input_path),
        "-vf",
        video_filter,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ])

    return {
        "ok": True,
        "outputs": {"files": [abs_path(output_path)]},
        "warnings": [],
    }
