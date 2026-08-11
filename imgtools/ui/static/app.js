const CATEGORY_LABELS = {
  all: '全部', metadata: '資訊', rename: '重新命名', pdf: 'PDF',
  merge: '合併', tif: 'TIF', gif: 'GIF', video: '影片', crop: '裁切', watermark: '浮水印',
};

const CATEGORY_ICONS = {
  metadata: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 10v6m0-9h.01"/></svg>',
  rename: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h10m-3-3 3 3-3 3M20 17H10m3-3-3 3 3 3"/></svg>',
  pdf: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6zM14 3v5h4M9 13h6M9 17h6"/></svg>',
  merge: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="11" height="11" rx="2"/><path d="M8 19h11a2 2 0 0 0 2-2V8M6 13l3-3 3 3"/></svg>',
  tif: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"/></svg>',
  gif: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 15 3-3 2 2 2-2 3 3M8 8h.01M16 8h.01"/></svg>',
  video: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3z"/></svg>',
  crop: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v14a2 2 0 0 0 2 2h12M3 7h14a2 2 0 0 1 2 2v12"/></svg>',
  watermark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18 12 4l8 14M7 13h10M6 21h12"/></svg>',
};

const OUTPUT_NAMING_STORAGE_KEY = 'imgtools.outputNaming';

let tools = [];
let selected = null;
let activeCategory = 'all';
let searchTerm = '';
let outputNaming = loadOutputNaming();
let preferences = {
  pinned_actions: [], usage: {}, quick_actions: [], max_pinned: 8, pdf_default_dpi: 192,
};
const formState = {};
const previewImages = new Map();
const previewErrors = new Map();
const previewPendingPaths = new Set();
const previewRequestTimers = new Map();
let dialoguePreviewRender = 0;
let watermarkPreviewRender = 0;
let stackPreviewRender = 0;
let resultPreviewRender = 0;

const $ = (id) => document.getElementById(id);

async function boot() {
  document.querySelectorAll('[data-output-naming]').forEach((button) => {
    button.addEventListener('click', () => setOutputNaming(button.dataset.outputNaming));
  });
  renderOutputNaming();
  $('pdf-default-dpi').addEventListener('change', savePdfDefaultDpi);
  $('quick-settings').addEventListener('click', toggleQuickEditor);
  $('tool-search').addEventListener('input', (event) => {
    searchTerm = event.target.value.trim().toLocaleLowerCase();
    renderTools();
  });

  try {
    const response = await fetch('/api/tools');
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法載入工具清單');
    tools = data.tools || [];
    await refreshPreferences();
    const firstQuickAction = preferences.quick_actions[0]?.action;
    selected = tools.find((tool) => tool.action === firstQuickAction)
      || tools.find((tool) => tool.featured)
      || tools[0]
      || null;
    renderCategories();
    renderQuickActions();
    renderQuickEditor();
    renderTools();
    renderForm();
  } catch (error) {
    $('tool-title').textContent = '工具清單載入失敗';
    $('tool-description').textContent = `${error.message}。請重新啟動 ImgTools 後再試一次。`;
    setStatus('載入失敗', false);
  }
}

async function refreshPreferences() {
  try {
    const response = await fetch('/api/preferences');
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法載入常用功能設定');
    preferences = data;
  } catch (_error) {
    if (!preferences.quick_actions.length) {
      preferences = {
        pinned_actions: [],
        usage: {},
        quick_actions: tools.filter((tool) => tool.featured).slice(0, 8).map((tool) => ({
          action: tool.action, source: 'default', successful_runs: 0,
        })),
        max_pinned: 8,
        pdf_default_dpi: 192,
      };
    }
  }
  syncPdfDefaultDpi();
}

function syncPdfDefaultDpi() {
  const dpi = Number(preferences.pdf_default_dpi) || 192;
  $('pdf-default-dpi').value = String(dpi);
  tools.filter((tool) => tool.category === 'pdf').forEach((tool) => {
    const dpiParam = tool.params.find((param) => param.name === 'dpi');
    if (dpiParam) dpiParam.default = dpi;
  });
}

async function savePdfDefaultDpi(event) {
  const input = event.currentTarget;
  const previous = Number(preferences.pdf_default_dpi) || 192;
  const next = Number(input.value);
  if (!Number.isInteger(next) || next < 36 || next > 1200) {
    input.value = String(previous);
    $('pdf-dpi-status').textContent = 'PDF 預設 DPI 必須是 36 到 1200 的整數。';
    return;
  }
  input.disabled = true;
  $('pdf-dpi-status').textContent = '正在保存 PDF 預設 DPI。';
  try {
    const response = await fetch('/api/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pdf_default_dpi: next }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法保存 PDF 預設 DPI');
    preferences = data;
    syncPdfDefaultDpi();
    const dpiField = selected?.category === 'pdf' ? $('param_dpi') : null;
    if (dpiField && Number(dpiField.value) === previous) dpiField.value = String(next);
    Object.keys(formState).forEach((action) => {
      if (action.startsWith('pdf.') && Number(formState[action].dpi) === previous) {
        formState[action].dpi = String(next);
      }
    });
    $('pdf-dpi-status').textContent = `PDF 預設 DPI 已保存為 ${next}。`;
  } catch (error) {
    input.value = String(previous);
    $('pdf-dpi-status').textContent = `保存 PDF 預設 DPI 失敗：${error.message}`;
  } finally {
    input.disabled = false;
  }
}

function loadOutputNaming() {
  try {
    const saved = window.localStorage.getItem(OUTPUT_NAMING_STORAGE_KEY);
    return saved === 'source' ? 'source' : 'fixed';
  } catch (_error) {
    return 'fixed';
  }
}

function setOutputNaming(mode) {
  if (!['fixed', 'source'].includes(mode) || mode === outputNaming) return;
  saveFormState();
  outputNaming = mode;
  try {
    window.localStorage.setItem(OUTPUT_NAMING_STORAGE_KEY, mode);
  } catch (_error) {
    // The setting still applies for this session when storage is unavailable.
  }
  renderOutputNaming();
  renderForm();
}

function renderOutputNaming() {
  document.querySelectorAll('[data-output-naming]').forEach((button) => {
    const isActive = button.dataset.outputNaming === outputNaming;
    button.classList.toggle('active', isActive);
    button.setAttribute('aria-pressed', String(isActive));
  });
}

function iconFor(category) {
  return CATEGORY_ICONS[category] || CATEGORY_ICONS.merge;
}

function renderQuickActions() {
  const quickActions = preferences.quick_actions
    .map((preference) => ({ preference, tool: tools.find((tool) => tool.action === preference.action) }))
    .filter((item) => item.tool);
  $('quick-actions').replaceChildren(...quickActions.map(({ preference, tool }, index) => {
    const button = document.createElement('button');
    const isActive = selected && selected.action === tool.action;
    button.type = 'button';
    button.className = `quick-action${isActive ? ' active' : ''}`;
    button.setAttribute('aria-pressed', String(isActive));
    button.innerHTML = `
      <span class="frame-index">${String(index + 1).padStart(2, '0')}</span>
      <span class="quick-icon">${iconFor(tool.category)}</span>
      <span class="quick-copy"><strong>${escapeHtml(tool.title)}</strong><small><span class="quick-source ${preference.source}">${escapeHtml(preferenceLabel(preference.source))}</span>${preference.successful_runs ? `${preference.successful_runs} 次成功執行` : '快速開啟'}</small></span>
      <svg class="launch-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-5-5 5 5-5 5"/></svg>`;
    button.addEventListener('click', () => selectTool(tool, true));
    return button;
  }));
}

function preferenceLabel(source) {
  if (source === 'pinned') return '已釘選';
  if (source === 'frequent') return '常用';
  return '預設';
}

function toggleQuickEditor() {
  const editor = $('quick-action-editor');
  const isOpening = editor.hidden;
  editor.hidden = !isOpening;
  $('quick-settings').setAttribute('aria-expanded', String(isOpening));
  if (isOpening) renderQuickEditor();
}

function renderQuickEditor() {
  const pinned = new Set(preferences.pinned_actions || []);
  const maxPinned = preferences.max_pinned || 8;
  $('pin-count').textContent = `${pinned.size} / ${maxPinned} 已釘選`;
  $('quick-pin-list').replaceChildren(...tools.map((tool) => {
    const button = document.createElement('button');
    const isPinned = pinned.has(tool.action);
    const usage = preferences.usage?.[tool.action]?.successful_runs || 0;
    button.type = 'button';
    button.className = `pin-choice${isPinned ? ' pinned' : ''}`;
    button.dataset.pinAction = tool.action;
    button.setAttribute('aria-pressed', String(isPinned));
    button.disabled = !isPinned && pinned.size >= maxPinned;
    button.innerHTML = `
      <span class="pin-choice-icon">${iconFor(tool.category)}</span>
      <span><strong>${escapeHtml(tool.title)}</strong><small>${escapeHtml(CATEGORY_LABELS[tool.category] || tool.category)} · ${usage} 次成功執行</small></span>
      <svg class="pin-mark" viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.4 5.1 5.6.7-4.1 3.9 1.1 5.5-5-2.7-5 2.7 1.1-5.5L4 8.8l5.6-.7z"/></svg>`;
    button.addEventListener('click', () => togglePinnedAction(tool.action, button));
    return button;
  }));
}

async function togglePinnedAction(action, button) {
  const current = preferences.pinned_actions || [];
  const isPinned = current.includes(action);
  const next = isPinned ? current.filter((item) => item !== action) : [...current, action];
  button.disabled = true;
  $('quick-editor-status').textContent = '正在保存本機設定…';
  try {
    const response = await fetch('/api/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pinned_actions: next }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法保存常用功能設定');
    preferences = data;
    renderQuickActions();
    renderQuickEditor();
    $('quick-editor-status').textContent = '已保存到這台電腦。';
  } catch (error) {
    $('quick-editor-status').textContent = `保存失敗：${error.message}`;
    button.disabled = false;
  }
}

function renderCategories() {
  const categories = ['all', ...new Set(tools.map((tool) => tool.category))];
  $('category-filters').replaceChildren(...categories.map((category) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `filter-chip${activeCategory === category ? ' active' : ''}`;
    button.textContent = CATEGORY_LABELS[category] || category;
    button.addEventListener('click', () => {
      activeCategory = category;
      renderCategories();
      renderTools();
    });
    return button;
  }));
}

function visibleTools() {
  return tools.filter((tool) => {
    const categoryMatches = activeCategory === 'all' || tool.category === activeCategory;
    const haystack = `${tool.title} ${tool.action} ${tool.description}`.toLocaleLowerCase();
    return categoryMatches && (!searchTerm || haystack.includes(searchTerm));
  });
}

function renderTools() {
  const filtered = visibleTools();
  $('tool-count').textContent = filtered.length;
  $('tools-empty').hidden = filtered.length > 0;
  $('tools').replaceChildren(...filtered.map((tool) => {
    const button = document.createElement('button');
    const isActive = selected && selected.action === tool.action;
    button.type = 'button';
    button.className = `tool${isActive ? ' active' : ''}`;
    button.setAttribute('aria-current', isActive ? 'true' : 'false');
    button.innerHTML = `
      <span class="tool-icon">${iconFor(tool.category)}</span>
      <span class="tool-copy"><strong>${escapeHtml(tool.title)}</strong><small>${escapeHtml(CATEGORY_LABELS[tool.category] || tool.category)}</small></span>
      <svg class="tool-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>`;
    button.addEventListener('click', () => selectTool(tool, window.innerWidth < 761));
    return button;
  }));
}

function selectTool(tool, shouldScroll) {
  saveFormState();
  selected = tool;
  renderQuickActions();
  renderTools();
  renderForm();
  if (shouldScroll) $('tool-intro').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderForm() {
  const form = $('form');
  if (!selected) {
    $('pdf-default-setting').hidden = true;
    form.replaceChildren();
    return;
  }

  $('tool-category').textContent = CATEGORY_LABELS[selected.category] || selected.category;
  $('tool-title').textContent = selected.title;
  $('tool-description').textContent = selected.description;
  $('tool-action').textContent = selected.action;
  $('pdf-default-setting').hidden = selected.category !== 'pdf';
  const dangerBadge = $('danger-badge');
  dangerBadge.textContent = selected.danger_level === 'high' ? '會變更檔案' : '';
  dangerBadge.className = selected.danger_level || '';

  const nodes = [];
  if (isWatermarkAction()) {
    nodes.push(renderWatermarkEditor());
  } else {
    const basicGrid = document.createElement('div');
    basicGrid.className = 'field-grid';
    const advancedGrid = document.createElement('div');
    advancedGrid.className = 'field-grid advanced-grid';

    const customDialogueParams = new Set(['subtitle_top_ratio', 'line_spacing']);
    selected.params.forEach((param) => {
      if (selected.action === 'merge.dialogue_stack' && customDialogueParams.has(param.name)) return;
      const field = renderField(param);
      (param.advanced ? advancedGrid : basicGrid).appendChild(field);
    });

    nodes.push(basicGrid);
    if (selected.action === 'merge.stack_vertical') nodes.push(renderStackVerticalPreview());
    if (selected.action === 'merge.dialogue_stack') nodes.push(renderDialoguePreview());
    if (advancedGrid.childElementCount) {
      const details = document.createElement('details');
      details.className = 'advanced-options';
      details.innerHTML = `<summary><span>進階設定</span><small>${advancedGrid.childElementCount} 個選項</small></summary>`;
      details.appendChild(advancedGrid);
      nodes.push(details);
    }
  }

  const actions = document.createElement('div');
  actions.className = 'actions';
  actions.innerHTML = `
    <button class="primary" id="run-tool" type="submit">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 5 11 7-11 7z"/></svg>
      <span>開始處理</span>
    </button>
    <button class="secondary" id="copy-task" type="button">複製工作 JSON</button>
    <span class="action-note">${escapeHtml(outputNamingNote())}</span>`;
  nodes.push(actions);

  form.replaceChildren(...nodes);
  form.onsubmit = runTool;
  $('copy-task').onclick = copyTask;
  selected.params
    .filter((param) => param.type === 'path_list')
    .forEach((param) => renderPathOrder(`param_${param.name}`, param));
  if (selected.action === 'merge.stack_vertical') initStackVerticalPreview();
  if (selected.action === 'merge.dialogue_stack') initDialoguePreview();
  if (isWatermarkAction()) initWatermarkEditor();
  const previewParam = interactivePreviewParam();
  if (previewParam) queueLocalPreviews(previewParam, { immediate: true });
}

function isWatermarkAction() {
  return selected?.action === 'watermark.text' || selected?.action === 'watermark.batch_text';
}

function isStackVerticalAction() {
  return selected?.action === 'merge.stack_vertical';
}

function interactivePreviewParam() {
  if (selected?.action === 'merge.dialogue_stack' || isStackVerticalAction()) {
    return selected.params.find((param) => param.name === 'input_paths') || null;
  }
  return isWatermarkAction() ? watermarkInputParam() : null;
}

function shouldAutoPreview(param) {
  return Boolean(
    (selected?.action === 'merge.dialogue_stack' && param.name === 'input_paths')
      || (isStackVerticalAction() && param.name === 'input_paths')
      || (isWatermarkAction() && ['input_path', 'input_paths'].includes(param.name)),
  );
}

function watermarkParam(name) {
  return selected.params.find((param) => param.name === name) || { name, default: '' };
}

function watermarkInputParam() {
  return selected.params.find((param) => param.name === 'input_paths')
    || watermarkParam('input_path');
}

function renderWatermarkEditor() {
  const isBatch = selected?.action === 'watermark.batch_text';
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
          <label class="watermark-range-field" for="watermark-rotation-range"><span><strong>旋轉角度</strong><output id="watermark-rotation-value">${escapeHtml(String(rotation))}°</output></span><input id="watermark-rotation-range" type="range" min="-180" max="180" step="1" value="${escapeHtml(String(rotation))}"><input id="param_rotation" class="sr-status" type="number" value="${escapeHtml(String(rotation))}"></label>
          <label class="watermark-range-field" for="watermark-opacity-range"><span><strong>不透明度</strong><output id="watermark-opacity-value">${opacityPercent}%</output></span><input id="watermark-opacity-range" type="range" min="0" max="100" step="1" value="${opacityPercent}"><input id="param_opacity" class="sr-status" type="number" value="${escapeHtml(String(opacity))}"></label>
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
  ['font_path', 'margin', isBatch ? 'output_dir' : 'output_path', 'overwrite']
    .map(watermarkParam)
    .forEach((param) => advanced.appendChild(renderField(param)));
  return panel;
}

function watermarkPositionButton(value, label, activeValue) {
  return `<button type="button" class="watermark-position-button${value === activeValue ? ' active' : ''}" data-watermark-position="${value}" aria-pressed="${value === activeValue}"><span class="position-dot position-${value}"></span>${label}</button>`;
}

function initWatermarkEditor() {
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

function watermarkCanvasPoint(event, canvas) {
  const bounds = canvas.getBoundingClientRect();
  return {
    x: (event.clientX - bounds.left) * canvas.width / bounds.width,
    y: (event.clientY - bounds.top) * canvas.height / bounds.height,
  };
}

function getWatermarkPreviewBox() {
  const canvas = $('watermark-preview-canvas');
  if (!canvas?.dataset.watermarkBox) return null;
  try { return JSON.parse(canvas.dataset.watermarkBox); } catch (_error) { return null; }
}

async function drawWatermarkPreview() {
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
    if (renderId !== watermarkPreviewRender) return;
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

function watermarkPositionLabel(mode) {
  return { center: '中央', top_left: '左上', top_right: '右上', bottom_left: '左下', bottom_right: '右下', custom: '自訂' }[mode] || mode;
}

function renderStackVerticalPreview() {
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

function initStackVerticalPreview() {
  const pathInput = $('param_input_paths');
  pathInput?.addEventListener('input', drawStackVerticalPreview);
  pathInput?.addEventListener('change', drawStackVerticalPreview);
  drawStackVerticalPreview();
}

async function drawStackVerticalPreview() {
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

function renderDialoguePreview() {
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
        <input id="dialogue-band-range" type="range" min="50" max="98" step="0.1" value="${ratio * 100}">
        <small>上方保留完整首張；後續圖片從導線以下全寬裁切。</small>
      </label>
      <label class="dialogue-control" for="dialogue-spacing-range">
        <span><strong>每句間距</strong><span class="dialogue-number"><input id="param_line_spacing" type="number" min="1" step="1" value="${spacing}"><b>px</b></span></span>
        <input id="dialogue-spacing-range" type="range" min="1" max="220" step="1" value="${spacing}">
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

function initDialoguePreview() {
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

function updateDialogueRatioFromPointer(event, updateRatio) {
  const canvas = $('dialogue-preview-canvas');
  const firstHeight = Number(canvas.dataset.firstHeight || 0);
  if (!firstHeight) return;
  const bounds = canvas.getBoundingClientRect();
  const y = (event.clientY - bounds.top) * canvas.height / bounds.height;
  updateRatio(y / firstHeight * 100);
}

async function drawDialoguePreview() {
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

function loadDialoguePreviewImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('預覽圖片載入失敗'));
    image.src = dataUrl;
  });
}

function drawDialogueCutGuide(context, y, width, ratio) {
  context.save();
  context.strokeStyle = '#ffb454';
  context.lineWidth = 3;
  context.setLineDash([12, 8]);
  context.beginPath();
  context.moveTo(0, y + 0.5);
  context.lineTo(width, y + 0.5);
  context.stroke();
  const label = ` 字幕帶起點 ${(ratio * 100).toFixed(1)}% `;
  context.font = '700 14px ui-monospace, monospace';
  const labelWidth = context.measureText(label).width;
  context.fillStyle = '#ffb454';
  context.fillRect(width - labelWidth - 14, y - 26, labelWidth + 8, 22);
  context.fillStyle = '#17232a';
  context.fillText(label, width - labelWidth - 10, y - 10);
  context.restore();
}

function outputNamingNote() {
  return outputNaming === 'source'
    ? '留白時跟隨來源命名；重名會先自動加編號'
    : '留白時使用 output；重名會先自動加編號';
}

function valueFor(param) {
  const saved = formState[selected.action];
  if (saved && Object.hasOwn(saved, param.name)) return saved[param.name];
  return param.default === undefined ? '' : param.default;
}

function renderField(param) {
  const block = document.createElement('div');
  const id = `param_${param.name}`;
  const value = valueFor(param);
  const fullWidth = param.type === 'path_list' || ['folder', 'path'].includes(param.type);
  block.className = `field${fullWidth ? ' full' : ''}`;

  if (param.type === 'bool') {
    block.innerHTML = `
      <label class="check-field" for="${id}">
        <input id="${id}" type="checkbox" ${value ? 'checked' : ''}>
        <span><strong>${escapeHtml(param.label)}</strong><span class="hint">${escapeHtml(param.description || booleanHint(param.name))}</span></span>
      </label>`;
    return block;
  }

  const required = param.required ? '<span class="required">必填</span>' : '<span class="optional">選填</span>';
  const hint = defaultHintFor(param);
  const defaultHint = hint ? `<span class="default-hint">預設：${escapeHtml(hint)}</span>` : '';
  const label = `<label class="field-label" for="${id}"><span>${escapeHtml(param.label)}</span>${required}</label>`;
  let control;
  if (param.type === 'path_list') {
    const pathValue = Array.isArray(value) ? value.join('\n') : value;
    control = `<textarea id="${id}" placeholder="每行一個圖片路徑">${escapeHtml(String(pathValue))}</textarea>`;
  } else if (param.choices && param.choices.length) {
    control = `<select id="${id}">${param.choices.map((choice) => `<option value="${escapeHtml(choice)}" ${choice === value ? 'selected' : ''}>${escapeHtml(choice)}</option>`).join('')}</select>`;
  } else {
    const inputType = ['int', 'float'].includes(param.type) ? 'number' : 'text';
    const step = param.type === 'float' ? ' step="any"' : '';
    control = `<input id="${id}" type="${inputType}"${step} value="${escapeHtml(String(value))}" placeholder="${escapeHtml(inputPlaceholder(param))}">`;
  }

  const canPick = ['path', 'folder', 'path_list'].includes(param.type);
  let controlMarkup = control;
  if (param.type === 'path_list') {
    controlMarkup = `<div class="ordered-path-list"><div class="path-control">${control}<button class="pick-button" type="button" data-pick-for="${id}">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h7l2 2h9v10H3zM3 7V5h7l2 2"/></svg><span>選擇圖片</span></button></div>
        <div class="path-order" id="${id}_order" aria-live="polite"></div></div>`;
  } else if (canPick) {
    controlMarkup = `<div class="path-control">${control}<button class="pick-button" type="button" data-pick-for="${id}">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h7l2 2h9v10H3zM3 7V5h7l2 2"/></svg><span>選擇</span></button></div>`
  }
  block.innerHTML = `${label}${controlMarkup}<div class="hint-row"><span class="hint">${escapeHtml(param.description || '')}</span>${defaultHint}</div>`;
  if (canPick) {
    block.querySelector('.pick-button').addEventListener('click', (event) => openPicker(param, event.currentTarget));
  }
  if (param.type === 'path_list') {
    const textarea = block.querySelector('textarea');
    textarea.addEventListener('input', () => renderPathOrder(id, param));
    renderPathOrder(id, param);
  }
  if (shouldAutoPreview(param)) {
    const previewInput = block.querySelector(`#${id}`);
    previewInput?.addEventListener('input', () => queueLocalPreviews(param));
    previewInput?.addEventListener('change', () => queueLocalPreviews(param, { immediate: true }));
  }
  return block;
}

function pathItems(id) {
  const element = $(id);
  if (!element) return [];
  return element.value.split(/\r?\n/).map(normalizeLocalPath).filter(Boolean);
}

function setPathItems(id, items, param) {
  const element = $(id);
  element.value = items.join('\n');
  element.dispatchEvent(new Event('change', { bubbles: true }));
  renderPathOrder(id, param);
}

function movePathItem(id, index, direction, param) {
  const items = pathItems(id);
  const target = index + direction;
  if (target < 0 || target >= items.length) return;
  [items[index], items[target]] = [items[target], items[index]];
  setPathItems(id, items, param);
}

function removePathItem(id, index, param) {
  const items = pathItems(id);
  items.splice(index, 1);
  setPathItems(id, items, param);
}

function renderPathOrder(id, param) {
  const container = $(`${id}_order`);
  if (!container) return;
  const items = pathItems(id);
  const min = param.min_items ?? 1;
  const max = param.max_items ?? null;
  const valid = items.length >= min && (max === null || items.length <= max);
  const limit = max === null ? `${items.length} 張` : `${items.length} / ${max} 張`;

  const heading = document.createElement('div');
  heading.className = `path-order-heading${valid ? '' : ' invalid'}`;
  heading.innerHTML = `<strong>由上到下的疊圖順序</strong><span>${escapeHtml(limit)}</span>`;
  if (!items.length) {
    const empty = document.createElement('p');
    empty.className = 'path-order-empty';
    empty.textContent = max
      ? `選擇 ${min}～${max} 張圖片後，可在這裡調整順序。`
      : `選擇至少 ${min} 張圖片後，可在這裡調整順序。`;
    container.replaceChildren(heading, empty);
    return;
  }

  const list = document.createElement('ol');
  list.className = 'path-order-list';
  items.forEach((path, index) => {
    const item = document.createElement('li');
    const filename = path.split(/[\\/]/).pop() || path;
    const record = previewImages.get(path);
    const showThumbnail = isStackVerticalAction() && param.name === 'input_paths';
    const thumbnailState = previewPendingPaths.has(path)
      ? '載入中'
      : previewErrors.has(path)
        ? '無法預覽'
        : '等待縮圖';
    const thumbnail = showThumbnail
      ? `<span class="path-order-thumbnail${record ? ' ready' : ''}" title="${escapeHtml(record ? `${record.width} × ${record.height} px` : thumbnailState)}">${record ? `<img src="${escapeHtml(record.data_url)}" alt="第 ${index + 1} 張縮圖">` : `<span>${escapeHtml(thumbnailState)}</span>`}</span>`
      : '';
    const pathDetail = record ? `${record.width} × ${record.height} px · ${path}` : path;
    item.className = `path-order-item${showThumbnail ? ' has-thumbnail' : ''}`;
    item.innerHTML = `
      <span class="path-order-index">${index + 1}</span>
      ${thumbnail}
      <span class="path-order-copy"><strong>${escapeHtml(filename)}</strong><small>${escapeHtml(pathDetail)}</small></span>
      <span class="path-order-actions">
        <button type="button" data-move="-1" aria-label="將第 ${index + 1} 張上移" ${index === 0 ? 'disabled' : ''}>↑</button>
        <button type="button" data-move="1" aria-label="將第 ${index + 1} 張下移" ${index === items.length - 1 ? 'disabled' : ''}>↓</button>
        <button type="button" data-remove aria-label="移除第 ${index + 1} 張">×</button>
      </span>`;
    item.querySelectorAll('[data-move]').forEach((button) => {
      button.addEventListener('click', () => movePathItem(id, index, Number(button.dataset.move), param));
    });
    item.querySelector('[data-remove]').addEventListener('click', () => removePathItem(id, index, param));
    list.appendChild(item);
  });
  container.replaceChildren(heading, list);
}

function pickerMode(param) {
  if (param.type === 'folder') return 'folder';
  if (param.type === 'path_list') return 'files';
  if (param.name.startsWith('output_')) return 'save';
  return 'file';
}

function previewPathsFor(param) {
  const id = `param_${param.name}`;
  if (param.type === 'path_list') return pathItems(id);
  const path = normalizeLocalPath($(id)?.value || '');
  return path ? [path] : [];
}

function previewErrorFor(paths) {
  return paths.map((path) => previewErrors.get(path)).find(Boolean) || '';
}

function refreshInteractivePreview() {
  if (isStackVerticalAction()) {
    const param = selected.params.find((item) => item.name === 'input_paths');
    if (param) renderPathOrder('param_input_paths', param);
    drawStackVerticalPreview();
  }
  if (selected?.action === 'merge.dialogue_stack') drawDialoguePreview();
  if (isWatermarkAction()) drawWatermarkPreview();
}

function queueLocalPreviews(param, { immediate = false } = {}) {
  if (!shouldAutoPreview(param)) return;
  const key = `param_${param.name}`;
  const previous = previewRequestTimers.get(key);
  if (previous) window.clearTimeout(previous);
  const delay = immediate ? 0 : 350;
  const timer = window.setTimeout(() => {
    previewRequestTimers.delete(key);
    requestLocalPreviews(param);
  }, delay);
  previewRequestTimers.set(key, timer);
}

async function requestLocalPreviews(param) {
  const paths = previewPathsFor(param);
  paths.forEach((path) => previewErrors.delete(path));
  const missing = paths.filter((path) => !previewImages.has(path));
  const requestPaths = missing.filter((path) => !previewPendingPaths.has(path));
  if (!requestPaths.length) {
    refreshInteractivePreview();
    return;
  }

  requestPaths.forEach((path) => previewPendingPaths.add(path));
  refreshInteractivePreview();
  try {
    const response = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paths: requestPaths }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '圖片預覽無法載入');
    (data.previews || []).forEach((preview) => {
      const path = normalizeLocalPath(preview.path);
      if (preview.data_url) {
        previewImages.set(path, { ...preview, path });
        previewErrors.delete(path);
      } else if (preview.error) {
        previewErrors.set(path, preview.error);
      }
    });
    requestPaths.forEach((path) => {
      if (!previewImages.has(path) && !previewErrors.has(path)) {
        previewErrors.set(path, '無法產生圖片預覽');
      }
    });
  } catch (error) {
    requestPaths.forEach((path) => previewErrors.set(path, error.message));
  } finally {
    requestPaths.forEach((path) => previewPendingPaths.delete(path));
    refreshInteractivePreview();
  }
}

async function openPicker(param, button) {
  const original = button.innerHTML;
  button.disabled = true;
  button.textContent = '選擇中…';
  try {
    const pickerPayload = { mode: pickerMode(param), title: `選擇${param.label}` };
    if (((selected?.action === 'merge.dialogue_stack' || isStackVerticalAction()) && param.type === 'path_list')
      || (isWatermarkAction() && param.type === 'path_list')
      || (selected?.action === 'watermark.text' && param.name === 'input_path')) {
      pickerPayload.include_previews = true;
    }
    const response = await fetch('/api/pick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pickerPayload),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '選擇器無法使用');
    if (!data.paths || !data.paths.length) return;
    (data.previews || []).forEach((preview) => {
      const path = normalizeLocalPath(preview.path);
      if (preview.data_url) {
        previewImages.set(path, { ...preview, path });
        previewErrors.delete(path);
      }
    });
    const element = $(`param_${param.name}`);
    element.value = param.type === 'path_list' ? data.paths.join('\n') : data.paths[0];
    element.dispatchEvent(new Event(param.type === 'path_list' ? 'input' : 'change', { bubbles: true }));
  } catch (error) {
    renderTransientMessage('無法選擇路徑', `${error.message}。仍可直接貼上完整路徑。`, true);
    setStatus('選擇器失敗', false);
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
}

function inputPlaceholder(param) {
  const hint = defaultHintFor(param);
  if (hint) return `留白即可使用${hint}`;
  if (param.type === 'path') return '貼上完整檔案路徑，或按「選擇」';
  if (param.type === 'folder') return '貼上資料夾路徑，或按「選擇」';
  return param.required ? '請輸入內容' : '選填';
}

function defaultHintFor(param) {
  if (outputNaming === 'source' && param.source_default_hint) return param.source_default_hint;
  return param.default_hint || '';
}

function booleanHint(name) {
  if (name === 'overwrite') return '允許覆蓋已存在的明確輸出路徑';
  if (name === 'confirm') return '關閉時只預覽變更，不會修改檔案';
  return '';
}

function normalizeLocalPath(value) {
  const path = String(value).trim();
  if (path.length >= 2 && path.startsWith('"') && path.endsWith('"')) {
    return path.slice(1, -1);
  }
  return path;
}

function readFormValues(includeEmpty = false) {
  const output = { output_naming: outputNaming };
  if (!selected) return output;
  selected.params.forEach((param) => {
    const element = $(`param_${param.name}`);
    if (!element) return;
    if (param.type === 'bool') output[param.name] = element.checked;
    else if (param.type === 'path_list') {
      const values = element.value.split(/\r?\n/).map(normalizeLocalPath).filter(Boolean);
      if (includeEmpty || values.length) output[param.name] = values;
    } else if (['path', 'folder'].includes(param.type)) {
      const value = normalizeLocalPath(element.value);
      if (includeEmpty || value !== '') output[param.name] = value;
    } else if (includeEmpty || element.value !== '') output[param.name] = element.value;
  });
  return output;
}

function collectParams() {
  return readFormValues(false);
}

function saveFormState() {
  if (selected && $('form').childElementCount) formState[selected.action] = readFormValues(true);
}

async function runTool(event) {
  event.preventDefault();
  saveFormState();
  const params = collectParams();
  if (isWatermarkAction() && !String(params.text || '').trim()) {
    const textInput = $('param_text');
    textInput?.setCustomValidity('請輸入浮水印文字。');
    textInput?.reportValidity();
    textInput?.focus();
    setStatus('請輸入浮水印文字', false);
    return;
  }
  const button = $('run-tool');
  const label = button.querySelector('span');
  button.disabled = true;
  label.textContent = '處理中…';
  setStatus('執行中', null);
  try {
    const response = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: selected.action, params }),
    });
    const data = await response.json();
    $('result').textContent = JSON.stringify(data, null, 2);
    renderResult(data);
    setStatus(data.ok ? '處理完成' : '處理失敗', data.ok);
    if (data.ok) {
      await refreshPreferences();
      renderQuickActions();
      renderQuickEditor();
    }
  } catch (error) {
    const data = { ok: false, message: error.message };
    $('result').textContent = JSON.stringify(data, null, 2);
    renderResult(data);
    setStatus('連線失敗', false);
  } finally {
    button.disabled = false;
    label.textContent = '開始處理';
  }
}

function renderResult(data) {
  const previewRenderId = ++resultPreviewRender;
  const cards = [];
  const files = Array.isArray(data.outputs?.files) ? data.outputs.files : [];
  if (data.ok) {
    cards.push(`<div class="result-hero success"><span class="result-symbol">${checkIcon()}</span><div><strong>處理完成</strong><span>${files.length ? `已建立 ${files.length} 個輸出檔案` : '工具已順利完成'}</span></div></div>`);
  } else {
    cards.push(`<div class="result-hero failure"><span class="result-symbol">${alertIcon()}</span><div><strong>無法完成處理</strong><span>${escapeHtml(data.message || data.error_code || '請檢查輸入後再試一次')}</span></div></div>`);
  }
  files.forEach((path, index) => {
    cards.push(`<div class="result-file"><span class="file-icon">${iconFor(selected?.category || 'merge')}</span><div><small>輸出 ${index + 1}</small><code>${escapeHtml(path)}</code></div><button type="button" data-copy-path="${index}">複製路徑</button></div>`);
  });
  if (data.ok && data.action === 'merge.stack_vertical' && files.length) {
    cards.push(`
      <section class="result-preview" data-result-preview-path="${escapeHtml(files[0])}">
        <div class="result-preview-heading"><strong>疊圖成品預覽</strong><span id="result-preview-size">載入中…</span></div>
        <div class="result-preview-stage">
          <div class="result-preview-empty" id="result-preview-empty">正在由本機讀取成品縮圖…</div>
          <img class="result-preview-image" id="result-preview-image" alt="快速直向疊圖成品預覽" hidden>
        </div>
        <p class="result-preview-status" id="result-preview-status">預覽已縮小顯示，輸出檔仍保留原始解析度。</p>
      </section>`);
  }
  (data.warnings || []).forEach((warning) => cards.push(`<div class="result-warning">${alertIcon()}<span>${escapeHtml(warning)}</span></div>`));
  $('result-summary').innerHTML = cards.join('');
  document.querySelectorAll('[data-copy-path]').forEach((button) => {
    button.addEventListener('click', () => copyPath(files[Number(button.dataset.copyPath)], button));
  });
  const manifest = $('manifest-note');
  manifest.hidden = !data.manifest_path;
  manifest.textContent = data.manifest_path ? '本次執行紀錄已集中保存於 Server。' : '';
  if (data.ok && data.action === 'merge.stack_vertical' && files.length) {
    loadResultPreview(files[0], previewRenderId);
  }
}

async function loadResultPreview(path, renderId) {
  try {
    const response = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '成品預覽無法載入');
    const preview = data.previews?.[0];
    if (!preview?.data_url) throw new Error(preview?.error || '成品預覽無法載入');
    if (renderId !== resultPreviewRender) return;
    const image = $('result-preview-image');
    const empty = $('result-preview-empty');
    if (!image || !empty) return;
    image.src = preview.data_url;
    image.hidden = false;
    empty.hidden = true;
    $('result-preview-size').textContent = `${preview.width} × ${preview.height} px`;
    $('result-preview-status').textContent = '可在預覽區捲動查看完整長圖；輸出檔仍保留原始解析度。';
  } catch (error) {
    if (renderId !== resultPreviewRender) return;
    const empty = $('result-preview-empty');
    if (!empty) return;
    empty.textContent = `無法載入成品預覽：${error.message}`;
    empty.classList.add('warning');
    const status = $('result-preview-status');
    if (status) status.textContent = '成品已輸出，可使用上方路徑開啟原始檔。';
  }
}

function renderTransientMessage(title, message, warning = false) {
  resultPreviewRender += 1;
  $('result-summary').innerHTML = `<div class="result-hero ${warning ? 'failure' : 'success'}"><span class="result-symbol">${warning ? alertIcon() : checkIcon()}</span><div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div></div>`;
}

async function copyPath(path, button) {
  try {
    await navigator.clipboard.writeText(path);
    const previous = button.textContent;
    button.textContent = '已複製';
    window.setTimeout(() => { button.textContent = previous; }, 1600);
  } catch (_error) {
    document.querySelector('.raw-result').open = true;
  }
}

async function copyTask() {
  const task = { action: selected.action, params: collectParams() };
  const text = JSON.stringify(task, null, 2);
  try {
    await navigator.clipboard.writeText(text);
    $('result').textContent = text;
    renderTransientMessage('工作 JSON 已複製', '可以貼到 CLI、文件或下一次工作中。');
    setStatus('已複製', true);
  } catch (_error) {
    $('result').textContent = text;
    document.querySelector('.raw-result').open = true;
    renderTransientMessage('請手動複製', '瀏覽器未允許剪貼簿存取，JSON 已顯示在下方。', true);
    setStatus('請手動複製', null);
  }
}

function checkIcon() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>';
}

function alertIcon() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4 3 20h18zM12 9v5m0 3h.01"/></svg>';
}

function setStatus(text, ok) {
  const status = $('status');
  status.innerHTML = `<i></i>${escapeHtml(text)}`;
  status.className = `status ${ok === true ? 'ok' : ok === false ? 'fail' : text === '執行中' ? 'running' : 'idle'}`;
}

function escapeHtml(value) {
  return String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

boot();
