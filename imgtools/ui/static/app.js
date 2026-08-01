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

  const basicGrid = document.createElement('div');
  basicGrid.className = 'field-grid';
  const advancedGrid = document.createElement('div');
  advancedGrid.className = 'field-grid advanced-grid';

  selected.params.forEach((param) => {
    const field = renderField(param);
    (param.advanced ? advancedGrid : basicGrid).appendChild(field);
  });

  const nodes = [basicGrid];
  if (advancedGrid.childElementCount) {
    const details = document.createElement('details');
    details.className = 'advanced-options';
    details.innerHTML = `<summary><span>進階設定</span><small>${advancedGrid.childElementCount} 個選項</small></summary>`;
    details.appendChild(advancedGrid);
    nodes.push(details);
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
  const controlMarkup = canPick
    ? `<div class="path-control">${control}<button class="pick-button" type="button" data-pick-for="${id}">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h7l2 2h9v10H3zM3 7V5h7l2 2"/></svg><span>選擇</span></button></div>`
    : control;
  block.innerHTML = `${label}${controlMarkup}<div class="hint-row"><span class="hint">${escapeHtml(param.description || '')}</span>${defaultHint}</div>`;
  if (canPick) {
    block.querySelector('.pick-button').addEventListener('click', (event) => openPicker(param, event.currentTarget));
  }
  return block;
}

function pickerMode(param) {
  if (param.type === 'folder') return 'folder';
  if (param.type === 'path_list') return 'files';
  if (param.name.startsWith('output_')) return 'save';
  return 'file';
}

async function openPicker(param, button) {
  const original = button.innerHTML;
  button.disabled = true;
  button.textContent = '選擇中…';
  try {
    const response = await fetch('/api/pick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: pickerMode(param), title: `選擇${param.label}` }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '選擇器無法使用');
    if (!data.paths || !data.paths.length) return;
    const element = $(`param_${param.name}`);
    element.value = param.type === 'path_list' ? data.paths.join('\n') : data.paths[0];
    element.dispatchEvent(new Event('change', { bubbles: true }));
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
  const button = $('run-tool');
  const label = button.querySelector('span');
  button.disabled = true;
  label.textContent = '處理中…';
  setStatus('執行中', null);
  try {
    const response = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: selected.action, params: collectParams() }),
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
  (data.warnings || []).forEach((warning) => cards.push(`<div class="result-warning">${alertIcon()}<span>${escapeHtml(warning)}</span></div>`));
  $('result-summary').innerHTML = cards.join('');
  document.querySelectorAll('[data-copy-path]').forEach((button) => {
    button.addEventListener('click', () => copyPath(files[Number(button.dataset.copyPath)], button));
  });
  const manifest = $('manifest-note');
  manifest.hidden = !data.manifest_path;
  manifest.textContent = data.manifest_path ? '本次執行紀錄已集中保存於 Server。' : '';
}

function renderTransientMessage(title, message, warning = false) {
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
