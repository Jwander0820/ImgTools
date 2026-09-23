let watermarkPreviewRender = 0;
import {$, selected, previewImages, previewErrors, previewPendingPaths} from './state.mjs';
import {valueFor, outputNamingNote} from './form.mjs';
import {renderField, pathItems, normalizeLocalPath} from './fields.mjs';
import {isWatermarkAction, loadDialoguePreviewImage} from './preview.mjs';
import {escapeHtml} from './dom.mjs';

export function watermarkParam(name) {
  return selected.params.find((param) => param.name === name) || { name, default: '' };
}

export function watermarkInputParam() {
  return selected.params.find((param) => param.name === 'input_paths')
    || watermarkParam('input_path');
}

export function renderWatermarkEditor() {
  const inputParam = watermarkInputParam();
  const text = valueFor(watermarkParam('text'));
  const fontSize = valueFor(watermarkParam('font_size'));
  const rotation = valueFor(watermarkParam('rotation'));
  const opacity = valueFor(watermarkParam('opacity'));
  const position = valueFor(watermarkParam('position')) || 'center';
  const positionX = valueFor(watermarkParam('position_x')) || 0;
  const positionY = valueFor(watermarkParam('position_y')) || 0;
  const margin = valueFor(watermarkParam('margin')) || 16;
  const color = valueFor(watermarkParam('color')) || '#000000';
  const repeat = Boolean(valueFor(watermarkParam('repeat')));
  const repeatSpacing = valueFor(watermarkParam('repeat_spacing')) || 100;
  const opacityPercent = Math.round((Number(opacity || 0) / 255) * 100);
  const panel = document.createElement('section');
  panel.className = 'watermark-editor';
  panel.innerHTML = `
    <div class="watermark-editor-heading">
      <div>
        <p class="eyebrow">Watermark positioning desk</p>
        <h3>拖曳浮水印到你要的位置</h3>
        <p>先選圖片，再直接拖曳預覽中的浮水印；角度、大小與不透明度會同步更新。</p>
      </div>
      <div class="watermark-tip"><span>操作提示</span><strong>拖曳 · 滾輪微調</strong></div>
    </div>
    <div class="watermark-input-row"></div>
    <div class="watermark-layout">
      <div class="watermark-preview-shell">
        <div class="watermark-preview-bar">
          <span><i></i>即時預覽</span>
          <code id="watermark-preview-size">等待圖片</code>
        </div>
        <div class="watermark-preview-stage" id="watermark-preview-stage">
          <div class="watermark-preview-empty" id="watermark-preview-empty">
            <span class="watermark-crosshair">＋</span>
            <strong>選擇一張或多張圖片開始</strong>
            <span>可使用「選擇」或直接貼上完整檔案路徑。</span>
          </div>
          <canvas class="watermark-preview-canvas" id="watermark-preview-canvas" hidden></canvas>
        </div>
        <p class="watermark-preview-status" id="watermark-preview-status" role="status">浮水印會以目前設定疊加在預覽上。</p>
      </div>
      <div class="watermark-controls">
        <div class="watermark-control-card">
          <div class="watermark-card-heading"><strong>內容與尺寸</strong><span>01</span></div>
          <label class="watermark-field" for="param_text"><span>浮水印文字 <span class="required">必填</span></span><input id="param_text" type="text" required aria-required="true" value="${escapeHtml(String(text))}" placeholder="例如：Jwander Studio"></label>
          <label class="watermark-field" for="param_font_size"><span>字型大小（px） <small>0 = 依圖片自動</small></span><input id="param_font_size" class="watermark-direct-input" type="text" inputmode="numeric" value="${escapeHtml(String(fontSize))}"></label>
        </div>
        <div class="watermark-control-card">
          <div class="watermark-card-heading"><strong>外觀</strong><span>02</span></div>
          <label class="watermark-range-field" for="watermark-rotation-range"><span><strong>旋轉角度</strong><output id="watermark-rotation-value">${escapeHtml(String(rotation))}°</output></span><input id="watermark-rotation-range" aria-label="旋轉角度（度）" type="range" min="-180" max="180" step="1" value="${escapeHtml(String(rotation))}"><input id="param_rotation" type="hidden" value="${escapeHtml(String(rotation))}"></label>
          <label class="watermark-range-field" for="watermark-opacity-range"><span><strong>不透明度</strong><output id="watermark-opacity-value">${opacityPercent}%</output></span><input id="watermark-opacity-range" aria-label="不透明度（%）" type="range" min="0" max="100" step="1" value="${opacityPercent}"><input id="param_opacity" type="hidden" value="${escapeHtml(String(opacity))}"></label>
          <label class="watermark-color-field" for="param_color"><span>浮水印顏色</span><span class="watermark-color-control"><input id="param_color" type="color" value="${escapeHtml(String(color))}"><code id="watermark-color-value">${escapeHtml(String(color))}</code></span></label>
          <div class="watermark-swatches" role="group" aria-label="浮水印色票">
            ${['#111827', '#6d45ff', '#4f46e5', '#ee6c4d', '#ffffff', '#64748b'].map((swatch) => `<button type="button" class="watermark-swatch${swatch.toLowerCase() === String(color).toLowerCase() ? ' active' : ''}" data-watermark-color="${swatch}" style="--swatch-color:${swatch}" aria-label="選擇 ${swatch}"></button>`).join('')}
          </div>
          <label class="watermark-toggle-field" for="param_repeat"><input id="param_repeat" type="checkbox" ${repeat ? 'checked' : ''}><span><strong>重複平鋪</strong><small>用同一組設定覆蓋整張圖片</small></span></label>
          <label class="watermark-field watermark-repeat-spacing-field" id="watermark-repeat-spacing-field" for="param_repeat_spacing" ${repeat ? '' : 'hidden'}><span>平鋪間距（px）</span><input id="param_repeat_spacing" class="watermark-direct-input" type="text" inputmode="numeric" value="${escapeHtml(String(repeatSpacing))}"></label>
        </div>
        <div class="watermark-control-card">
          <div class="watermark-card-heading"><strong>位置</strong><span>03</span></div>
          <label class="sr-status" for="param_position">位置模式</label>
          <select id="param_position" class="sr-status">
            ${['center', 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'custom'].map((choice) => `<option value="${choice}" ${choice === position ? 'selected' : ''}>${choice}</option>`).join('')}
          </select>
          <div class="watermark-position-grid" role="group" aria-label="浮水印預設位置">
            ${watermarkPositionButton('top_left', '左上', position)}
            ${watermarkPositionButton('center', '中央', position)}
            ${watermarkPositionButton('top_right', '右上', position)}
            ${watermarkPositionButton('bottom_left', '左下', position)}
            ${watermarkPositionButton('custom', '自訂', position)}
            ${watermarkPositionButton('bottom_right', '右下', position)}
          </div>
          <div class="watermark-coordinate-fields" id="watermark-coordinate-fields" ${position === 'custom' ? '' : 'hidden'}>
            <label for="param_position_x">X <input id="param_position_x" type="number" step="1" value="${escapeHtml(String(positionX))}"></label>
            <label for="param_position_y">Y <input id="param_position_y" type="number" step="1" value="${escapeHtml(String(positionY))}"></label>
          </div>
          <p class="watermark-control-note">選「自訂」後可輸入座標，也可以直接拖曳預覽中的文字。</p>
        </div>
        <details class="watermark-advanced">
          <summary><span>輸出與進階</span><small>字型、邊距、檔案</small></summary>
          <div class="watermark-advanced-grid"></div>
        </details>
      </div>
    </div>`;
  panel.querySelector('.watermark-input-row').appendChild(
    renderField(selected?.action === 'watermark.text' ? { ...inputParam, required: true } : inputParam),
  );
  const advanced = panel.querySelector('.watermark-advanced-grid');
  ['font_path', 'margin', 'output_path', 'output_dir', 'overwrite']
    .map(name => selected.params.find(param => param.name === name))
    .filter(Boolean)
    .forEach((param) => advanced.appendChild(renderField(param)));
  return panel;
}

export function watermarkPositionButton(value, label, activeValue) {
  return `<button type="button" class="watermark-position-button${value === activeValue ? ' active' : ''}" data-watermark-position="${value}" aria-pressed="${value === activeValue}"><span class="position-dot position-${value}"></span>${label}</button>`;
}

export function initWatermarkEditor() {
  const canvas = $('watermark-preview-canvas');
  const rotationRange = $('watermark-rotation-range');
  const rotationInput = $('param_rotation');
  const opacityRange = $('watermark-opacity-range');
  const opacityInput = $('param_opacity');
  const positionSelect = $('param_position');
  const inputPath = $('param_input_paths') || $('param_input_path');
  const textInput = $('param_text');
  const fontSizeInput = $('param_font_size');
  const marginInput = $('param_margin');
  const colorInput = $('param_color');
  const colorValue = $('watermark-color-value');
  const repeatInput = $('param_repeat');
  const repeatSpacingInput = $('param_repeat_spacing');
  const repeatSpacingField = $('watermark-repeat-spacing-field');
  const coordinateFields = $('watermark-coordinate-fields');
  if (!canvas || !rotationRange || !rotationInput || !opacityRange || !opacityInput || !positionSelect) return;

  const updateOutputs = () => {
    const batch = selected.action === 'watermark.batch_text' || pathItems('param_input_paths').length > 1;
    const note = document.querySelector('#actionbar .action-note');
    if (note) note.textContent = batch ? '多張圖片集中輸出到資料夾；重名會自動加編號' : outputNamingNote();
    for (const name of ['output_path', 'output_dir']) {
      const input = $(`param_${name}`);
      if (!input) continue;
      const active = batch === (name === 'output_dir');
      input.disabled = !active;
      input.closest('.field').hidden = !active;
    }
  };
  inputPath?.addEventListener('input', updateOutputs);
  inputPath?.addEventListener('change', updateOutputs);
  updateOutputs();

  const updateRotation = (value) => {
    const next = Math.min(180, Math.max(-180, Number(value) || 0));
    rotationRange.value = String(next);
    rotationInput.value = String(next);
    $('watermark-rotation-value').textContent = `${next}°`;
    drawWatermarkPreview();
  };
  const updateOpacity = (value) => {
    const percent = Math.min(100, Math.max(0, Number(value) || 0));
    opacityRange.value = String(percent);
    opacityInput.value = String(Math.round(percent * 255 / 100));
    $('watermark-opacity-value').textContent = `${Math.round(percent)}%`;
    drawWatermarkPreview();
  };
  const updatePositionUi = () => {
    const mode = positionSelect.value;
    document.querySelectorAll('[data-watermark-position]').forEach((button) => {
      const active = button.dataset.watermarkPosition === mode;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    coordinateFields.hidden = mode !== 'custom';
  };
  const setPosition = (mode, preserveCoordinates = false) => {
    if (mode === 'custom' && !preserveCoordinates) {
      const box = getWatermarkPreviewBox();
      const scale = Number(canvas.dataset.originalScale || 1);
      if (box) {
        $('param_position_x').value = String(Math.round(box.x / scale));
        $('param_position_y').value = String(Math.round(box.y / scale));
      }
    }
    positionSelect.value = mode;
    updatePositionUi();
    drawWatermarkPreview();
  };

  rotationRange.addEventListener('input', () => updateRotation(rotationRange.value));
  rotationInput.addEventListener('input', () => updateRotation(rotationInput.value));
  opacityRange.addEventListener('input', () => updateOpacity(opacityRange.value));
  opacityInput.addEventListener('input', () => updateOpacity(Number(opacityInput.value) / 255 * 100));
  [inputPath, textInput, fontSizeInput, marginInput, repeatSpacingInput, $('param_position_x'), $('param_position_y')].forEach((input) => {
    if (input) input.addEventListener('input', drawWatermarkPreview);
    if (input === inputPath) input?.addEventListener('change', drawWatermarkPreview);
  });
  textInput?.addEventListener('input', () => textInput.setCustomValidity(''));
  if (colorInput) {
    colorInput.addEventListener('input', () => {
      colorValue.textContent = colorInput.value;
      document.querySelectorAll('[data-watermark-color]').forEach((button) => button.classList.toggle('active', button.dataset.watermarkColor.toLowerCase() === colorInput.value.toLowerCase()));
      drawWatermarkPreview();
    });
  }
  document.querySelectorAll('[data-watermark-color]').forEach((button) => {
    button.addEventListener('click', () => {
      if (!colorInput) return;
      colorInput.value = button.dataset.watermarkColor;
      colorInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
  });
  repeatInput?.addEventListener('change', () => {
    repeatSpacingField.hidden = !repeatInput.checked;
    drawWatermarkPreview();
  });
  document.querySelectorAll('[data-watermark-position]').forEach((button) => {
    button.addEventListener('click', () => setPosition(button.dataset.watermarkPosition));
  });

  let dragging = false;
  let dragOffset = { x: 0, y: 0 };
  canvas.addEventListener('pointerdown', (event) => {
    const box = getWatermarkPreviewBox();
    if (!box) return;
    const point = watermarkCanvasPoint(event, canvas);
    if (point.x < box.x || point.x > box.x + box.width || point.y < box.y || point.y > box.y + box.height) return;
    const scale = Number(canvas.dataset.originalScale || 1);
    setPosition('custom', true);
    $('param_position_x').value = String(Math.round(box.x / scale));
    $('param_position_y').value = String(Math.round(box.y / scale));
    dragOffset = { x: point.x - box.x, y: point.y - box.y };
    dragging = true;
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', (event) => {
    if (!dragging) return;
    const box = getWatermarkPreviewBox();
    if (!box) return;
    const point = watermarkCanvasPoint(event, canvas);
    const scale = Number(canvas.dataset.originalScale || 1);
    const x = Math.max(0, Math.min(canvas.width - box.width, point.x - dragOffset.x));
    const y = Math.max(0, Math.min(canvas.height - box.height, point.y - dragOffset.y));
    $('param_position_x').value = String(Math.round(x / scale));
    $('param_position_y').value = String(Math.round(y / scale));
    drawWatermarkPreview();
  });
  const stopDragging = (event) => {
    dragging = false;
    if (event?.pointerId !== undefined && canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
  };
  canvas.addEventListener('pointerup', stopDragging);
  canvas.addEventListener('pointercancel', stopDragging);
  canvas.addEventListener('wheel', (event) => {
    event.preventDefault();
    const current = Number(rotationInput.value) || 0;
    updateRotation(current + (event.deltaY > 0 ? 1 : -1));
  }, { passive: false });
  updatePositionUi();
  drawWatermarkPreview();
}

export function watermarkCanvasPoint(event, canvas) {
  const bounds = canvas.getBoundingClientRect();
  return {
    x: (event.clientX - bounds.left) * canvas.width / bounds.width,
    y: (event.clientY - bounds.top) * canvas.height / bounds.height,
  };
}

export function getWatermarkPreviewBox() {
  const canvas = $('watermark-preview-canvas');
  if (!canvas?.dataset.watermarkBox) return null;
  try { return JSON.parse(canvas.dataset.watermarkBox); } catch (_error) { return null; }
}

export async function drawWatermarkPreview() {
  if (!isWatermarkAction()) return;
  const renderId = ++watermarkPreviewRender;
  const path = $('param_input_paths')
    ? pathItems('param_input_paths')[0]
    : normalizeLocalPath($('param_input_path')?.value || '');
  const record = previewImages.get(path);
  const pending = Boolean(path && previewPendingPaths.has(path));
  const error = previewErrors.get(path) || '';
  const canvas = $('watermark-preview-canvas');
  const empty = $('watermark-preview-empty');
  const status = $('watermark-preview-status');
  if (!record) {
    canvas.hidden = true;
    empty.hidden = false;
    status.classList.toggle('warning', Boolean(error));
    empty.querySelector('strong').textContent = pending
      ? '正在載入預覽'
      : error
        ? '無法載入預覽'
        : '選擇或貼上一張圖片開始';
    empty.querySelector('span:not(.watermark-crosshair)').textContent = pending
      ? '正在由本機 ImgTools 讀取縮圖。'
      : error
        ? `${error}。仍可嘗試正式處理。`
        : '可使用「選擇」或直接貼上完整檔案路徑。';
    status.textContent = pending
      ? '正在讀取圖片預覽…'
      : error
        ? '預覽失敗，但不會阻止正式處理。'
        : '浮水印會以目前設定疊加在預覽上。';
    $('watermark-preview-size').textContent = '等待圖片';
    return;
  }

  status.classList.remove('warning');
  status.textContent = '正在更新預覽…';
  try {
    const image = await loadDialoguePreviewImage(record.data_url);
    if (renderId !== watermarkPreviewRender || !canvas.isConnected) return;
    const context = canvas.getContext('2d');
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const scale = image.naturalWidth / record.width;
    canvas.dataset.originalScale = String(scale);
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0);

    const text = $('param_text').value || '浮水印';
    const originalFontSize = Number($('param_font_size').value) || Math.max(12, Math.round(Math.min(record.width, record.height) * 0.2));
    const fontSize = originalFontSize * scale;
    const padding = Math.max(8, originalFontSize / 3) * scale;
    context.font = `700 ${fontSize}px "Microsoft JhengHei", "Segoe UI", sans-serif`;
    const textWidth = context.measureText(text).width;
    const boxWidth = Math.max(1, textWidth + padding * 2);
    const boxHeight = Math.max(1, fontSize + padding * 2);
    const rotation = Number($('param_rotation').value) || 0;
    const radians = rotation * Math.PI / 180;
    const rotatedWidth = Math.abs(Math.cos(radians)) * boxWidth + Math.abs(Math.sin(radians)) * boxHeight;
    const rotatedHeight = Math.abs(Math.sin(radians)) * boxWidth + Math.abs(Math.cos(radians)) * boxHeight;
    const margin = Number($('param_margin')?.value) || 16;
    const mode = $('param_position').value;
    const color = $('param_color')?.value || '#17232a';
    const repeat = Boolean($('param_repeat')?.checked);
    const repeatSpacing = Math.max(0, Number($('param_repeat_spacing')?.value) || 100) * scale;
    const positions = {
      center: [Math.max(0, (canvas.width - rotatedWidth) / 2), Math.max(0, (canvas.height - rotatedHeight) / 2)],
      top_left: [rotatedWidth > canvas.width ? 0 : margin * scale, rotatedHeight > canvas.height ? 0 : margin * scale],
      top_right: [Math.max(0, canvas.width - rotatedWidth - margin * scale), rotatedHeight > canvas.height ? 0 : margin * scale],
      bottom_left: [rotatedWidth > canvas.width ? 0 : margin * scale, Math.max(0, canvas.height - rotatedHeight - margin * scale)],
      bottom_right: [Math.max(0, canvas.width - rotatedWidth - margin * scale), Math.max(0, canvas.height - rotatedHeight - margin * scale)],
      custom: [Math.min(Math.max(0, Number($('param_position_x').value || 0) * scale), Math.max(0, canvas.width - rotatedWidth)), Math.min(Math.max(0, Number($('param_position_y').value || 0) * scale), Math.max(0, canvas.height - rotatedHeight))],
    };
    const [x, y] = positions[mode] || positions.center;
    const oversized = rotatedWidth > canvas.width || rotatedHeight > canvas.height;
    if (mode === 'custom') {
      $('param_position_x').value = String(Math.round(x / scale));
      $('param_position_y').value = String(Math.round(y / scale));
    }
    canvas.dataset.watermarkBox = JSON.stringify({ x, y, width: rotatedWidth, height: rotatedHeight });
    const drawWatermarkTile = (tileX, tileY) => {
      context.save();
      context.globalAlpha = Number($('param_opacity').value || 0) / 255;
      context.translate(tileX + rotatedWidth / 2, tileY + rotatedHeight / 2);
      context.rotate(radians);
      context.fillStyle = color;
      context.textAlign = 'center';
      context.textBaseline = 'middle';
      context.fillText(text, 0, 0);
      context.restore();
    };
    if (repeat) {
      const stepX = Math.max(1, rotatedWidth + repeatSpacing);
      const stepY = Math.max(1, rotatedHeight + repeatSpacing);
      const startX = (x % stepX) - stepX;
      const startY = (y % stepY) - stepY;
      for (let tileY = startY; tileY < canvas.height; tileY += stepY) {
        for (let tileX = startX; tileX < canvas.width; tileX += stepX) drawWatermarkTile(tileX, tileY);
      }
    } else {
      drawWatermarkTile(x, y);
    }
    context.save();
    context.strokeStyle = '#ffb454';
    context.lineWidth = Math.max(2, scale * 2);
    context.setLineDash([10 * scale, 7 * scale]);
    context.strokeRect(x, y, rotatedWidth, rotatedHeight);
    context.restore();
    canvas.hidden = false;
    empty.hidden = true;
    $('watermark-preview-size').textContent = `${record.width} × ${record.height} px`;
    const locationMessage = mode === 'custom'
      ? `自訂座標 X ${Math.round(x / scale)} · Y ${Math.round(y / scale)}；拖曳文字可微調。`
      : `目前位置：${watermarkPositionLabel(mode)}；拖曳文字即可切換成自訂位置。`;
    status.classList.toggle('warning', oversized);
    status.textContent = oversized
      ? `${locationMessage}浮水印超出圖片，請降低字型大小。`
      : locationMessage;
  } catch (error) {
    canvas.hidden = true;
    empty.hidden = false;
    status.classList.remove('warning');
    empty.querySelector('strong').textContent = '無法建立預覽';
    empty.querySelector('span').textContent = error.message;
    status.textContent = '請確認圖片格式後重新選取。';
  }
}

export function watermarkPositionLabel(mode) {
  return { center: '中央', top_left: '左上', top_right: '右上', bottom_left: '左下', bottom_right: '右下', custom: '自訂' }[mode] || mode;
}
