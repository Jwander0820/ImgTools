from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

from .common import abs_path, default_output_stem, resolve_output_path


@dataclass(frozen=True)
class PairMatch:
    matched: bool
    dx: float | None = None
    dy: float | None = None
    inliers: int = 0
    candidates: int = 0
    inlier_ratio: float = 0.0
    method: str = "sift_ransac"
    low_confidence: bool = False


class InsufficientOverlapError(ValueError):
    error_code = "INSUFFICIENT_OVERLAP"


def images_to_pdf(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    folder_path = Path(str(params["folder_path"])).expanduser().resolve()
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Input folder does not exist: {folder_path}")
    overwrite = bool(params.get("overwrite", False))
    default_name = f"{default_output_stem(params, folder_path)}.pdf"
    output_path = resolve_output_path(
        params.get("output_path"),
        folder_path / default_name,
        overwrite=overwrite,
    )
    image_paths = sorted(
        path
        for path in folder_path.iterdir()
        if path.is_file() and path.suffix.lower() in {".tif", ".tiff", ".png", ".jpg", ".jpeg"}
    )
    if not image_paths:
        raise ValueError(f"No supported images found in: {folder_path}")

    images = []
    try:
        for image_path in image_paths:
            with Image.open(image_path) as source:
                images.append(source.convert("RGB"))
        images[0].save(output_path, "PDF", save_all=True, append_images=images[1:])
    finally:
        for image in images:
            image.close()
    return {
        "ok": True,
        "outputs": {"files": [abs_path(output_path)]},
        "warnings": [],
    }


def stack_vertical(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image, ImageOps

    raw_paths = params.get("input_paths")
    if not isinstance(raw_paths, (list, tuple)) or not 2 <= len(raw_paths) <= 9:
        raise ValueError("input_paths must contain 2 to 9 image paths")

    paths = [Path(str(path)).expanduser().resolve() for path in raw_paths]
    images = []
    try:
        for path in paths:
            if not path.is_file():
                raise FileNotFoundError(f"Input image does not exist: {path}")
            with Image.open(path) as source:
                images.append(ImageOps.exif_transpose(source).copy())

        widths = {image.width for image in images}
        if len(widths) != 1:
            raise ValueError("All input images must have the same width; images are not resized")

        has_alpha = any("A" in image.getbands() or "transparency" in image.info for image in images)
        mode = "RGBA" if has_alpha else "RGB"
        converted = [image.convert(mode) for image in images]
        try:
            width = converted[0].width
            height = sum(image.height for image in converted)
            canvas = Image.new(mode, (width, height), (0, 0, 0, 0) if has_alpha else "black")
            top = 0
            for image in converted:
                canvas.paste(image, (0, top))
                top += image.height

            default_name = f"{default_output_stem(params, paths[0])}.png"
            requested_output = params.get("output_path")
            if requested_output and Path(str(requested_output)).suffix.lower() != ".png":
                raise ValueError("output_path must end in .png")
            output_path = resolve_output_path(
                requested_output,
                paths[0].parent / default_name,
                overwrite=bool(params.get("overwrite", False)),
                protected_paths=tuple(paths),
            )
            try:
                canvas.save(output_path, "PNG")
            finally:
                canvas.close()
        finally:
            for image in converted:
                image.close()
    finally:
        for image in images:
            image.close()

    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(output_path)],
            "source_files": [abs_path(path) for path in paths],
            "image_count": len(paths),
            "width": width,
            "height": height,
        },
        "warnings": [],
    }


def dialogue_stack(params: dict[str, Any]) -> dict[str, Any]:
    """Keep the first frame, then stack full-width subtitle bands from later frames."""
    from PIL import Image, ImageOps

    raw_paths = params.get("input_paths")
    if not isinstance(raw_paths, (list, tuple)) or not 2 <= len(raw_paths) <= 12:
        raise ValueError("input_paths must contain 2 to 12 image paths")

    subtitle_top_ratio = float(params.get("subtitle_top_ratio", 0.88))
    if not 0.0 < subtitle_top_ratio < 1.0:
        raise ValueError("subtitle_top_ratio must be greater than 0.0 and less than 1.0")
    line_spacing = int(params.get("line_spacing", 85))
    if line_spacing <= 0:
        raise ValueError("line_spacing must be greater than 0")

    paths = [Path(str(path)).expanduser().resolve() for path in raw_paths]
    images = []
    try:
        for path in paths:
            if not path.is_file():
                raise FileNotFoundError(f"Input image does not exist: {path}")
            with Image.open(path) as source:
                images.append(ImageOps.exif_transpose(source).copy())

        sizes = {image.size for image in images}
        if len(sizes) != 1:
            raise ValueError("All input images must have the same dimensions")

        width, source_height = images[0].size
        subtitle_top = round(source_height * subtitle_top_ratio)
        subtitle_top = min(max(subtitle_top, 1), source_height - 1)
        subtitle_band_height = source_height - subtitle_top
        if line_spacing > subtitle_band_height:
            raise ValueError(
                "line_spacing must not exceed the subtitle band height "
                f"({subtitle_band_height} pixels)"
            )

        has_alpha = any(
            "A" in image.getbands() or "transparency" in image.info
            for image in images
        )
        mode = "RGBA" if has_alpha else "RGB"
        converted = [image.convert(mode) for image in images]
        try:
            output_height = source_height + line_spacing * (len(converted) - 1)
            background = (0, 0, 0, 0) if has_alpha else "black"
            canvas = Image.new(mode, (width, output_height), background)
            try:
                canvas.paste(converted[0], (0, 0))
                for index, image in enumerate(converted[1:], start=1):
                    band = image.crop((0, subtitle_top, width, source_height))
                    try:
                        target_y = subtitle_top + line_spacing * index
                        canvas.paste(band, (0, target_y))
                    finally:
                        band.close()

                default_name = f"{default_output_stem(params, paths[0])}.png"
                requested_output = params.get("output_path")
                if requested_output and Path(str(requested_output)).suffix.lower() != ".png":
                    raise ValueError("output_path must end in .png")
                output_path = resolve_output_path(
                    requested_output,
                    paths[0].parent / default_name,
                    overwrite=bool(params.get("overwrite", False)),
                    protected_paths=tuple(paths),
                )
                canvas.save(output_path, "PNG")
            finally:
                canvas.close()
        finally:
            for image in converted:
                image.close()
    finally:
        for image in images:
            image.close()

    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(output_path)],
            "source_files": [abs_path(path) for path in paths],
            "image_count": len(paths),
            "width": width,
            "height": output_height,
            "subtitle_top": subtitle_top,
            "subtitle_band_height": subtitle_band_height,
            "line_spacing": line_spacing,
            "overlap": subtitle_band_height - line_spacing,
        },
        "warnings": [],
    }


def panorama_translation(params: dict[str, Any]) -> dict[str, Any]:
    import cv2

    raw_paths = params.get("input_paths")
    if not isinstance(raw_paths, (list, tuple)) or len(raw_paths) < 2:
        raise ValueError("input_paths must contain at least two image paths")

    paths = [Path(str(path)).expanduser().resolve() for path in raw_paths]
    images = [_read_cv_image(path) for path in paths]
    shapes = {image.shape for image in images}
    if len(shapes) != 1:
        raise ValueError("All input images must have the same dimensions and channels")

    ignore_bottom_ratio = float(params.get("ignore_bottom_ratio", 0.15))
    if not 0.0 <= ignore_bottom_ratio < 1.0:
        raise ValueError("ignore_bottom_ratio must be between 0.0 and less than 1.0")
    subtitle_crop_ratio = float(params.get("subtitle_crop_ratio", 0.08))
    if not 0.0 <= subtitle_crop_ratio < 1.0:
        raise ValueError("subtitle_crop_ratio must be between 0.0 and less than 1.0")

    pair_matches = [
        estimate_translation(first, second, ignore_bottom_ratio=ignore_bottom_ratio)
        for first, second in zip(images, images[1:])
    ]
    recovered_count = 0
    if bool(params.get("allow_low_confidence", True)):
        pair_matches, recovered_count = _recover_timestamp_matches(images, paths, pair_matches)
    start, end = _largest_connected_segment(pair_matches)
    if end - start < 2:
        raise InsufficientOverlapError("No pair of input images has sufficient reliable overlap")

    selected_images = images[start:end]
    selected_paths = paths[start:end]
    positions: list[tuple[int, int]] = [(0, 0)]
    for match in pair_matches[start : end - 1]:
        previous_x, previous_y = positions[-1]
        positions.append(
            (
                previous_x - round(float(match.dx)),
                previous_y - round(float(match.dy)),
            )
        )

    subtitle_rows_removed = 0
    subtitle_seams_applied = 0
    if bool(params.get("crop_subtitles", True)):
        panorama, subtitle_seams_applied = _subtitle_seam_compose(
            selected_images,
            positions,
            crop_ratio=subtitle_crop_ratio,
        )
    else:
        panorama = _overwrite_compose(selected_images, positions)
    output_path = resolve_output_path(
        None,
        paths[0].parent / "stitched" / f"{default_output_stem(params, paths[0])}.png",
        overwrite=bool(params.get("overwrite", False)),
    )
    ok, encoded = cv2.imencode(".png", panorama)
    if not ok:
        raise OSError(f"Could not encode panorama output: {output_path}")
    output_path.write_bytes(encoded.tobytes())

    skipped_paths = paths[:start] + paths[end:]
    diagnostics = []
    for index, match in enumerate(pair_matches):
        item = asdict(match)
        item.update({"from": abs_path(paths[index]), "to": abs_path(paths[index + 1])})
        diagnostics.append(item)

    warnings = []
    if recovered_count:
        warnings.append(
            f"Included {recovered_count} low-confidence pair(s) using filename timestamp motion extrapolation."
        )
    if skipped_paths:
        warnings.append(
            f"Used the largest reliable segment and skipped {len(skipped_paths)} image(s) with insufficient overlap."
        )
    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(output_path)],
            "used_files": [abs_path(path) for path in selected_paths],
            "skipped_files": [abs_path(path) for path in skipped_paths],
            "pair_matches": diagnostics,
            "subtitle_rows_removed": subtitle_rows_removed,
            "subtitle_seams_applied": subtitle_seams_applied,
        },
        "warnings": warnings,
    }


def estimate_translation(
    first: Any,
    second: Any,
    *,
    ignore_bottom_ratio: float = 0.15,
    min_inliers: int = 8,
    min_inlier_ratio: float = 0.2,
    ransac_threshold: float = 3.0,
) -> PairMatch:
    import numpy as np

    displacements, candidates = _match_displacements(
        first,
        second,
        ignore_bottom_ratio=ignore_bottom_ratio,
    )
    if candidates == 0:
        return PairMatch(matched=False)
    center, inlier_mask = _translation_consensus(displacements, ransac_threshold)
    inliers = int(np.count_nonzero(inlier_mask))
    ratio = inliers / candidates
    matched = inliers >= min_inliers and ratio >= min_inlier_ratio
    return PairMatch(
        matched=matched,
        dx=float(center[0]) if matched else None,
        dy=float(center[1]) if matched else None,
        inliers=inliers,
        candidates=candidates,
        inlier_ratio=round(ratio, 4),
    )


def _recover_timestamp_matches(
    images: list[Any],
    paths: list[Path],
    matches: list[PairMatch],
) -> tuple[list[PairMatch], int]:
    times = [_timestamp_seconds(path) for path in paths]
    if any(value is None for value in times):
        return matches, 0
    deltas = []
    for first, second in zip(times, times[1:]):
        delta = float(second) - float(first)
        if delta <= 0:
            delta += 24 * 60 * 60
        deltas.append(delta)

    references = [
        index
        for index, match in enumerate(matches)
        if match.matched and match.dx is not None and match.dy is not None and deltas[index] > 0
    ]
    if not references:
        return matches, 0

    recovered = list(matches)
    recovered_count = 0
    for index, match in enumerate(matches):
        if match.matched or deltas[index] <= 0:
            continue
        reference = min(references, key=lambda item: abs(item - index))
        scale = deltas[index] / deltas[reference]
        predicted = (
            float(matches[reference].dx) * scale,
            float(matches[reference].dy) * scale,
        )
        candidate = _estimate_translation_near_prediction(images[index], images[index + 1], predicted)
        if candidate.matched:
            recovered[index] = candidate
            recovered_count += 1
    return recovered, recovered_count


def _estimate_translation_near_prediction(
    first: Any,
    second: Any,
    predicted: tuple[float, float],
    *,
    min_inliers: int = 3,
    ransac_threshold: float = 4.0,
) -> PairMatch:
    import numpy as np

    displacements, candidates = _match_displacements(first, second, ignore_bottom_ratio=0.0)
    if candidates == 0:
        return PairMatch(matched=False, method="timestamp_fallback", low_confidence=True)
    prediction = np.asarray(predicted, dtype=np.float32)
    tolerance = max(40.0, min(140.0, float(np.linalg.norm(prediction)) * 0.15))
    nearby = displacements[np.linalg.norm(displacements - prediction, axis=1) <= tolerance]
    if len(nearby) == 0:
        return PairMatch(
            matched=False,
            candidates=candidates,
            method="timestamp_fallback",
            low_confidence=True,
        )
    center, inlier_mask = _translation_consensus(nearby, ransac_threshold)
    inliers = int(np.count_nonzero(inlier_mask))
    height, width = first.shape[:2]
    leaves_overlap = abs(float(center[0])) < width and abs(float(center[1])) < height
    matched = inliers >= min_inliers and leaves_overlap
    return PairMatch(
        matched=matched,
        dx=float(center[0]) if matched else None,
        dy=float(center[1]) if matched else None,
        inliers=inliers,
        candidates=candidates,
        inlier_ratio=round(inliers / candidates, 4),
        method="timestamp_fallback",
        low_confidence=True,
    )


def _match_displacements(
    first: Any,
    second: Any,
    *,
    ignore_bottom_ratio: float,
) -> tuple[Any, int]:
    import cv2
    import numpy as np

    height = first.shape[0]
    usable_height = max(1, round(height * (1.0 - ignore_bottom_ratio)))
    mask = np.zeros(first.shape[:2], dtype=np.uint8)
    mask[:usable_height, :] = 255
    first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    second_gray = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)
    detector = cv2.SIFT_create(nfeatures=10000, contrastThreshold=0.02, edgeThreshold=15)
    first_points, first_descriptors = detector.detectAndCompute(first_gray, mask)
    second_points, second_descriptors = detector.detectAndCompute(second_gray, mask)
    if first_descriptors is None or second_descriptors is None:
        return np.empty((0, 2), dtype=np.float32), 0
    if len(first_descriptors) < 2 or len(second_descriptors) < 2:
        return np.empty((0, 2), dtype=np.float32), 0

    matcher = cv2.BFMatcher(cv2.NORM_L2)
    forward = _ratio_matches(matcher.knnMatch(first_descriptors, second_descriptors, k=2))
    reverse = _ratio_matches(matcher.knnMatch(second_descriptors, first_descriptors, k=2))
    reverse_pairs = {(match.queryIdx, match.trainIdx) for match in reverse}
    mutual = [match for match in forward if (match.trainIdx, match.queryIdx) in reverse_pairs]
    displacements = np.asarray(
        [
            np.subtract(second_points[match.trainIdx].pt, first_points[match.queryIdx].pt)
            for match in mutual
        ],
        dtype=np.float32,
    )
    return displacements.reshape((-1, 2)), len(mutual)


def _timestamp_seconds(path: Path) -> float | None:
    match = re.search(r"_(\d{2})(\d{2})(\d{2})\.(\d+)$", path.stem)
    if match is None:
        return None
    hours, minutes, seconds, fraction = match.groups()
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(fraction) / (10 ** len(fraction))
    )


def _ratio_matches(pairs: list[list[Any]], ratio: float = 0.78) -> list[Any]:
    matches = []
    for pair in pairs:
        if len(pair) == 2 and pair[0].distance < ratio * pair[1].distance:
            matches.append(pair[0])
    return matches


def _translation_consensus(displacements: Any, threshold: float) -> tuple[Any, Any]:
    import numpy as np

    sample_count = min(len(displacements), 500)
    sample_indexes = np.linspace(0, len(displacements) - 1, sample_count, dtype=int)
    best_mask = np.zeros(len(displacements), dtype=bool)
    for center in displacements[sample_indexes]:
        distances = np.linalg.norm(displacements - center, axis=1)
        mask = distances <= threshold
        if np.count_nonzero(mask) > np.count_nonzero(best_mask):
            best_mask = mask
    center = np.median(displacements[best_mask], axis=0)
    best_mask = np.linalg.norm(displacements - center, axis=1) <= threshold
    if np.any(best_mask):
        center = np.median(displacements[best_mask], axis=0)
    return center, best_mask


def _largest_connected_segment(matches: list[PairMatch]) -> tuple[int, int]:
    best = (0, 1)
    start = 0
    for edge_index, match in enumerate(matches):
        if not match.matched:
            end = edge_index + 1
            if end - start > best[1] - best[0]:
                best = (start, end)
            start = edge_index + 1
    end = len(matches) + 1
    if end - start > best[1] - best[0]:
        best = (start, end)
    return best


def _overwrite_compose(images: list[Any], positions: list[tuple[int, int]]) -> Any:
    import numpy as np

    height, width = images[0].shape[:2]
    min_x = min(x for x, _ in positions)
    min_y = min(y for _, y in positions)
    max_x = max(x + width for x, _ in positions)
    max_y = max(y + height for _, y in positions)
    canvas_width = max_x - min_x
    canvas_height = max_y - min_y
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    for image, (x, y) in zip(images, positions):
        left = x - min_x
        top = y - min_y
        canvas[top : top + height, left : left + width] = image
    return canvas


def _subtitle_seam_compose(
    images: list[Any],
    positions: list[tuple[int, int]],
    *,
    crop_ratio: float,
    bottom_margin_ratio: float = 0.04,
    seam_guard_ratio: float = 0.02,
) -> tuple[Any, int]:
    import numpy as np

    height, width = images[0].shape[:2]
    min_x = min(x for x, _ in positions)
    min_y = min(y for _, y in positions)
    normalized = [(x - min_x, y - min_y) for x, y in positions]
    max_x = max(x + width for x, _ in normalized)
    max_y = max(y + height for _, y in normalized)
    canvas = np.zeros((max_y, max_x, 3), dtype=np.uint8)

    band_height = round(height * crop_ratio)
    bottom_margin = round(height * bottom_margin_ratio)
    seam_guard = round(height * seam_guard_ratio)
    subtitle_start = height - bottom_margin - band_height - seam_guard
    if band_height <= 0 or len(images) < 2:
        return _overwrite_compose(images, positions), 0

    order = sorted(range(len(images)), key=lambda index: (normalized[index][1], -index))
    seams: list[int] = []
    applied = 0
    for upper_index, lower_index in zip(order, order[1:]):
        upper_top = normalized[upper_index][1]
        lower_top = normalized[lower_index][1]
        overlap_start = max(upper_top, lower_top)
        overlap_end = min(upper_top + height, lower_top + height)
        if overlap_end <= overlap_start:
            return _overwrite_compose(images, positions), 0
        desired = upper_top + subtitle_start
        if desired >= overlap_start:
            seam = min(desired, overlap_end)
            applied += 1
        else:
            seam = overlap_start
        seams.append(seam)

    for order_index, image_index in enumerate(order):
        left, top = normalized[image_index]
        visible_top = top if order_index == 0 else seams[order_index - 1]
        visible_bottom = top + height if order_index == len(order) - 1 else seams[order_index]
        source_top = max(0, visible_top - top)
        source_bottom = min(height, visible_bottom - top)
        if source_bottom <= source_top:
            continue
        target_top = top + source_top
        target_bottom = top + source_bottom
        canvas[target_top:target_bottom, left : left + width] = images[image_index][source_top:source_bottom]
    return canvas, applied


def _read_cv_image(path: Path) -> Any:
    import cv2
    import numpy as np

    if not path.is_file():
        raise FileNotFoundError(f"Input image does not exist: {path}")
    encoded = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unsupported or unreadable image: {path}")
    return image
