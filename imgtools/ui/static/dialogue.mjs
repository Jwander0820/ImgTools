let dialoguePreviewRender = 0;
import {$, selected, previewImages, previewPendingPaths} from './state.mjs';
import {valueFor} from './form.mjs';
import {pathItems, previewErrorFor} from './fields.mjs';
import {loadDialoguePreviewImage, drawDialogueCutGuide} from './preview.mjs';

export function renderDialoguePreview() {
  const ratioParam = selected.params.find((param) => param.name === 'subtitle_top_ratio');
  const spacingParam = selected.params.find((param) => param.name === 'line_spacing');
  const ratio = Number(valueFor(ratioParam)) || 0.88;
  const spacing = Number(valueFor(spacingParam)) || 85;
  const panel = document.createElement('section');
  panel.className = 'dialogue-editor';
  panel.innerHTML = `
    <div class="dialogue-editor-heading">
      <div><p class="eyebrow">Dialogue cutting desk</p><h3>字幕剪輯台</h3></div>
      <p>拖曳預覽中的橫線，決定每張圖片從哪裡開始保留字幕帶。</p>
    </div>
    <div class="dialogue-controls">
      <label class="dialogue-control" for="dialogue-band-range">
        <span><strong>字幕帶起點</strong><output id="dialogue-band-value">${(ratio * 100).toFixed(1)}%</output></span>
        <input id="dialogue-band-range" aria-label="字幕帶起點（%）" type="range" min="50" max="98" step="0.1" value="${ratio * 100}">
        <small>上方保留完整首張；後續圖片從導線以下全寬裁切。</small>
      </label>
      <label class="dialogue-control" for="dialogue-spacing-range">
        <span><strong>每句間距</strong><span class="dialogue-number"><input id="param_line_spacing" aria-label="每句間距（px）" type="number" min="1" step="1" value="${spacing}"><b>px</b></span></span>
        <input id="dialogue-spacing-range" aria-label="調整每句間距" type="range" min="1" max="220" step="1" value="${spacing}">
        <small>每加入一句台詞，成品向下增加的高度；必須落在字幕帶內。</small>
      </label>
      <input id="param_subtitle_top_ratio" type="hidden" value="${ratio}">
    </div>
    <div class="dialogue-preview-shell">
      <div class="dialogue-preview-bar">
        <span><i></i>即時預覽</span>
        <code id="dialogue-preview-size">等待圖片</code>
      </div>
      <div class="dialogue-preview-stage" id="dialogue-preview-stage">
        <div class="dialogue-preview-empty" id="dialogue-preview-empty">
          <strong>選擇至少兩張圖片</strong>
          <span>預覽只載入經由「選擇圖片」明確選取的檔案。</span>
        </div>
        <canvas class="dialogue-preview-canvas" id="dialogue-preview-canvas" hidden></canvas>
      </div>
      <p class="dialogue-preview-status" id="dialogue-preview-status" role="status">第一張會完整保留，後續只取導線以下的全寬字幕帶。</p>
    </div>`;
  return panel;
}

export function initDialoguePreview() {
  const pathInput = $('param_input_paths');
  const ratioRange = $('dialogue-band-range');
  const ratioInput = $('param_subtitle_top_ratio');
  const spacingRange = $('dialogue-spacing-range');
  const spacingInput = $('param_line_spacing');
  const canvas = $('dialogue-preview-canvas');
  let dragging = false;

  const updateRatio = (percent) => {
    const value = Math.min(98, Math.max(50, Number(percent) || 88));
    ratioRange.value = String(value);
    ratioInput.value = String(value / 100);
    $('dialogue-band-value').textContent = `${value.toFixed(1)}%`;
    drawDialoguePreview();
  };
  const updateSpacing = (value) => {
    const max = Number(spacingRange.max) || 220;
    const next = Math.min(max, Math.max(1, Math.round(Number(value) || 1)));
    spacingRange.value = String(next);
    spacingInput.value = String(next);
    drawDialoguePreview();
  };

  pathInput.addEventListener('input', drawDialoguePreview);
  pathInput.addEventListener('change', drawDialoguePreview);
  ratioRange.addEventListener('input', () => updateRatio(ratioRange.value));
  spacingRange.addEventListener('input', () => updateSpacing(spacingRange.value));
  spacingInput.addEventListener('input', () => updateSpacing(spacingInput.value));
  canvas.addEventListener('pointerdown', (event) => {
    dragging = true;
    canvas.setPointerCapture(event.pointerId);
    updateDialogueRatioFromPointer(event, updateRatio);
  });
  canvas.addEventListener('pointermove', (event) => {
    if (dragging) updateDialogueRatioFromPointer(event, updateRatio);
  });
  canvas.addEventListener('pointerup', (event) => {
    dragging = false;
    canvas.releasePointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointercancel', () => { dragging = false; });
  drawDialoguePreview();
}

export function updateDialogueRatioFromPointer(event, updateRatio) {
  const canvas = $('dialogue-preview-canvas');
  const firstHeight = Number(canvas.dataset.firstHeight || 0);
  if (!firstHeight) return;
  const bounds = canvas.getBoundingClientRect();
  const y = (event.clientY - bounds.top) * canvas.height / bounds.height;
  updateRatio(y / firstHeight * 100);
}

export async function drawDialoguePreview() {
  if (selected?.action !== 'merge.dialogue_stack') return;
  const renderId = ++dialoguePreviewRender;
  const paths = pathItems('param_input_paths');
  const missing = paths.filter((path) => !previewImages.has(path));
  const pending = missing.some((path) => previewPendingPaths.has(path));
  const previewError = previewErrorFor(missing);
  const canvas = $('dialogue-preview-canvas');
  const empty = $('dialogue-preview-empty');
  const status = $('dialogue-preview-status');
  if (paths.length < 2 || missing.length) {
    canvas.hidden = true;
    empty.hidden = false;
    empty.querySelector('strong').textContent = paths.length < 2
      ? '選擇或貼上至少兩張圖片'
      : pending
        ? '正在載入預覽'
        : previewError
          ? '無法載入預覽'
          : '需要重新載入預覽';
    empty.querySelector('span').textContent = paths.length < 2
      ? '可使用「選擇圖片」，或在文字框中每行貼上一個完整路徑。'
      : pending
        ? '正在由本機 ImgTools 讀取縮圖。'
        : previewError
          ? `${previewError}。仍可嘗試正式處理。`
          : '可重新輸入路徑或使用「選擇圖片」載入。';
    status.classList.toggle('warning', Boolean(previewError));
    status.textContent = pending
      ? '正在讀取圖片預覽…'
      : previewError
        ? '預覽失敗，但不會阻止正式處理。'
        : '第一張會完整保留，後續只取底部全寬字幕帶。';
    $('dialogue-preview-size').textContent = '等待圖片';
    return;
  }

  status.classList.remove('warning');
  status.textContent = '正在準備預覽…';
  try {
    const records = paths.map((path) => previewImages.get(path));
    const images = await Promise.all(records.map((record) => loadDialoguePreviewImage(record.data_url)));
    if (renderId !== dialoguePreviewRender) return;
    const dimensions = new Set(records.map((record) => `${record.width}x${record.height}`));
    if (dimensions.size !== 1) throw new Error('所有圖片必須具有相同尺寸');

    const originalWidth = records[0].width;
    const originalHeight = records[0].height;
    const previewWidth = images[0].naturalWidth;
    const previewHeight = images[0].naturalHeight;
    const scale = previewWidth / originalWidth;
    const ratio = Number($('param_subtitle_top_ratio').value);
    const bandTop = Math.round(previewHeight * ratio);
    const originalBandHeight = originalHeight - Math.round(originalHeight * ratio);
    const spacingRange = $('dialogue-spacing-range');
    const spacingInput = $('param_line_spacing');
    spacingRange.max = String(Math.max(1, originalBandHeight));
    spacingInput.max = String(Math.max(1, originalBandHeight));
    if (Number(spacingInput.value) > originalBandHeight) {
      spacingInput.value = String(originalBandHeight);
      spacingRange.value = String(originalBandHeight);
    }
    const lineSpacing = Number(spacingInput.value);
    const previewSpacing = Math.max(1, Math.round(lineSpacing * scale));
    const outputHeight = previewHeight + previewSpacing * (images.length - 1);

    canvas.width = previewWidth;
    canvas.height = outputHeight;
    canvas.dataset.firstHeight = String(previewHeight);
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(images[0], 0, 0);
    images.slice(1).forEach((image, index) => {
      const targetY = bandTop + previewSpacing * (index + 1);
      context.drawImage(image, 0, bandTop, previewWidth, previewHeight - bandTop, 0, targetY, previewWidth, previewHeight - bandTop);
    });
    drawDialogueCutGuide(context, bandTop, previewWidth, ratio);

    empty.hidden = true;
    canvas.hidden = false;
    $('dialogue-preview-size').textContent = `${originalWidth} × ${originalHeight + lineSpacing * (images.length - 1)} px`;
    status.textContent = `字幕帶高 ${originalBandHeight}px；相鄰字幕帶重疊 ${originalBandHeight - lineSpacing}px。拖曳橫線可繼續調整。`;
  } catch (error) {
    canvas.hidden = true;
    empty.hidden = false;
    empty.querySelector('strong').textContent = '無法建立預覽';
    empty.querySelector('span').textContent = error.message;
    status.textContent = '請確認圖片格式與尺寸後重新選取。';
  }
}
