let stackPreviewRender = 0;
import {$, previewImages, previewPendingPaths} from './state.mjs';
import {pathItems, previewErrorFor} from './fields.mjs';
import {isStackVerticalAction, loadDialoguePreviewImage} from './preview.mjs';

export function renderStackVerticalPreview() {
  const panel = document.createElement('section');
  panel.className = 'stack-preview';
  panel.innerHTML = `
    <div class="stack-preview-heading">
      <div><p class="eyebrow">Before export</p><h3>輸出前疊圖預覽</h3></div>
      <p>依目前由上到下的順序，用縮圖即時模擬正式輸出；不會提前寫入檔案。</p>
    </div>
    <div class="stack-preview-shell">
      <div class="stack-preview-bar">
        <span><i></i>即時合成</span>
        <code id="stack-preview-size">等待圖片</code>
      </div>
      <div class="stack-preview-stage" id="stack-preview-stage">
        <div class="stack-preview-empty" id="stack-preview-empty">
          <strong>選擇至少兩張同寬圖片</strong>
          <span>選圖後會在這裡顯示依目前順序合成的完整長圖。</span>
        </div>
        <canvas class="stack-preview-canvas" id="stack-preview-canvas" hidden></canvas>
      </div>
      <p class="stack-preview-status" id="stack-preview-status" role="status">預覽只使用縮圖，不會建立或修改輸出檔。</p>
    </div>`;
  return panel;
}

export function initStackVerticalPreview() {
  const pathInput = $('param_input_paths');
  pathInput?.addEventListener('input', drawStackVerticalPreview);
  pathInput?.addEventListener('change', drawStackVerticalPreview);
  drawStackVerticalPreview();
}

export async function drawStackVerticalPreview() {
  if (!isStackVerticalAction()) return;
  const renderId = ++stackPreviewRender;
  const paths = pathItems('param_input_paths');
  const missing = paths.filter((path) => !previewImages.has(path));
  const pending = missing.some((path) => previewPendingPaths.has(path));
  const previewError = previewErrorFor(missing);
  const canvas = $('stack-preview-canvas');
  const empty = $('stack-preview-empty');
  const status = $('stack-preview-status');
  const size = $('stack-preview-size');
  const invalidCount = paths.length > 9;
  if (paths.length < 2 || invalidCount || missing.length) {
    canvas.hidden = true;
    empty.hidden = false;
    empty.querySelector('strong').textContent = invalidCount
      ? '快速直向疊圖最多支援九張圖片'
      : paths.length < 2
        ? '選擇或貼上至少兩張同寬圖片'
        : pending
          ? '正在載入預覽'
          : previewError
            ? '無法載入部分圖片'
            : '需要重新載入預覽';
    empty.querySelector('span').textContent = invalidCount
      ? '請移除多餘圖片後再確認輸出前預覽。'
      : paths.length < 2
        ? '可使用「選擇圖片」，或在文字框中每行貼上一個完整路徑。'
        : pending
          ? '正在由本機 ImgTools 讀取縮圖。'
          : previewError
            ? `${previewError}。預覽失敗不會修改任何檔案。`
            : '可重新輸入路徑或使用「選擇圖片」載入。';
    status.classList.toggle('warning', invalidCount || Boolean(previewError));
    status.textContent = pending
      ? '正在讀取圖片並準備合成預覽…'
      : invalidCount
        ? '請將圖片數量調整為 2～9 張。'
        : previewError
          ? '部分縮圖無法讀取，尚未建立任何輸出。'
          : '預覽只使用縮圖，不會建立或修改輸出檔。';
    size.textContent = '等待圖片';
    return;
  }

  status.classList.remove('warning');
  status.textContent = '正在依目前順序合成預覽…';
  try {
    const records = paths.map((path) => previewImages.get(path));
    const widths = new Set(records.map((record) => record.width));
    if (widths.size !== 1) throw new Error('所有圖片必須同寬，正式輸出不會自動縮放原圖');
    const images = await Promise.all(records.map((record) => loadDialoguePreviewImage(record.data_url)));
    if (renderId !== stackPreviewRender) return;

    const originalWidth = records[0].width;
    const originalHeight = records.reduce((total, record) => total + record.height, 0);
    const scale = Math.min(1, 720 / originalWidth, 8192 / originalHeight);
    const renderedHeights = records.map((record) => Math.max(1, Math.round(record.height * scale)));
    canvas.width = Math.max(1, Math.round(originalWidth * scale));
    canvas.height = renderedHeights.reduce((total, height) => total + height, 0);
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    let top = 0;
    images.forEach((image, index) => {
      context.drawImage(image, 0, top, canvas.width, renderedHeights[index]);
      top += renderedHeights[index];
    });

    canvas.hidden = false;
    empty.hidden = true;
    size.textContent = `${originalWidth} × ${originalHeight} px`;
    status.textContent = `目前依 ${paths.length} 張圖片的順序預覽；正式輸出保持原始解析度。`;
  } catch (error) {
    if (renderId !== stackPreviewRender) return;
    canvas.hidden = true;
    empty.hidden = false;
    empty.querySelector('strong').textContent = '無法建立疊圖預覽';
    empty.querySelector('span').textContent = error.message;
    size.textContent = '預覽失敗';
    status.classList.add('warning');
    status.textContent = '請確認所有圖片寬度一致後再執行。';
  }
}
