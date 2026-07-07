const CATEGORY_LABELS = {
  all: '全部',
  metadata: '資訊',
  rename: '重新命名',
  pdf: 'PDF',
  merge: '合併',
  tif: 'TIF',
  gif: 'GIF',
  crop: '裁切',
  watermark: '浮水印',
};

const CATEGORY_MARKS = {
  metadata: 'EX', rename: 'RN', pdf: 'PD', merge: 'MG',
  tif: 'TF', gif: 'GF', crop: 'CR', watermark: 'WM',
};

let tools = [];
let selected = null;
let activeCategory = 'all';
let searchTerm = '';

const $ = (id) => document.getElementById(id);

async function boot() {
  $('tool-search').addEventListener('input', (event) => {
    searchTerm = event.target.value.trim().toLocaleLowerCase();
    renderTools();
  });

  try {
    const response = await fetch('/api/tools');
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法載入工具清單');
    tools = data.tools || [];
    selected = tools[0] || null;
    renderCategories();
    renderTools();
    renderForm();
  } catch (error) {
    $('tool-title').textContent = '工具清單載入失敗';
    $('tool-description').textContent = `${error.message}。請重新啟動 ImgTools 後再試一次。`;
    setStatus('載入失敗', false);
  }
}

function renderCategories() {
  const categories = ['all', ...new Set(tools.map((tool) => tool.category))];
  const container = $('category-filters');
  container.replaceChildren(...categories.map((category) => {
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
      <span class="tool-icon">${escapeHtml(CATEGORY_MARKS[tool.category] || 'TL')}</span>
      <span class="tool-copy"><strong>${escapeHtml(tool.title)}</strong><small>${escapeHtml(tool.action)}</small></span>
      <span class="tool-arrow" aria-hidden="true">›</span>`;
    button.addEventListener('click', () => {
      selected = tool;
      renderTools();
      renderForm();
      if (window.innerWidth < 761) $('tool-intro').scrollIntoView({ behavior: 'smooth' });
    });
    return button;
  }));
}

function renderForm() {
  const form = $('form');
  if (!selected) {
    form.replaceChildren();
    return;
  }

  $('tool-category').textContent = CATEGORY_LABELS[selected.category] || selected.category;
  $('tool-title').textContent = selected.title;
  $('tool-description').textContent = selected.description;
  $('tool-action').textContent = selected.action;
  const dangerBadge = $('danger-badge');
  dangerBadge.textContent = selected.danger_level === 'high' ? '會變更檔案' : '';
  dangerBadge.className = selected.danger_level || '';

  const grid = document.createElement('div');
  grid.className = 'field-grid';
  selected.params.forEach((param) => grid.appendChild(renderField(param)));

  const actions = document.createElement('div');
  actions.className = 'actions';
  actions.innerHTML = `
    <button class="primary" id="run-tool" type="submit">執行工具</button>
    <button class="secondary" id="copy-task" type="button">複製 JSON</button>
    <span class="action-note">所有處理都留在這台電腦</span>`;

  form.replaceChildren(grid, actions);
  form.onsubmit = runTool;
  $('copy-task').onclick = copyTask;
}

function renderField(param) {
  const block = document.createElement('div');
  const id = `param_${param.name}`;
  const value = param.default === undefined ? '' : param.default;
  const fullWidth = param.type === 'path_list' || selected.params.length < 2;
  block.className = `field${fullWidth ? ' full' : ''}`;

  if (param.type === 'bool') {
    block.innerHTML = `
      <label class="check-field" for="${id}">
        <input id="${id}" type="checkbox" ${value ? 'checked' : ''}>
        <span><strong>${escapeHtml(param.name)}</strong><span class="hint">${escapeHtml(param.description || booleanHint(param.name))}</span></span>
      </label>`;
    return block;
  }

  const required = param.required ? '<span class="required">＊</span>' : '';
  const label = `<label class="field-label" for="${id}"><code>${escapeHtml(param.name)}</code>${required}</label>`;
  let control;
  if (param.type === 'path_list') {
    const pathValue = Array.isArray(value) ? value.join('\n') : value;
    control = `<textarea id="${id}" placeholder="每行貼上一個圖片路徑">${escapeHtml(String(pathValue))}</textarea>`;
  } else if (param.choices && param.choices.length) {
    control = `<select id="${id}">${param.choices.map((choice) => `<option value="${escapeHtml(choice)}" ${choice === value ? 'selected' : ''}>${escapeHtml(choice)}</option>`).join('')}</select>`;
  } else {
    const inputType = ['int', 'float'].includes(param.type) ? 'number' : 'text';
    const step = param.type === 'float' ? ' step="any"' : '';
    control = `<input id="${id}" type="${inputType}"${step} value="${escapeHtml(String(value))}" placeholder="${escapeHtml(inputPlaceholder(param))}">`;
  }
  block.innerHTML = `${label}${control}<div class="hint">${escapeHtml(param.description || '')}</div>`;
  return block;
}

function inputPlaceholder(param) {
  if (param.type === 'path') return '例如：D:\\Images\\output.png';
  if (param.type === 'folder') return '例如：D:\\Images';
  return param.required ? '請輸入內容' : '選填';
}

function booleanHint(name) {
  if (name === 'overwrite') return '允許覆蓋已存在的輸出檔案';
  if (name === 'confirm') return '關閉時只會預覽變更，不會修改檔案';
  return '';
}

function collectParams() {
  const output = {};
  selected.params.forEach((param) => {
    const element = $(`param_${param.name}`);
    if (!element) return;
    if (param.type === 'bool') output[param.name] = element.checked;
    else if (param.type === 'path_list') output[param.name] = element.value.split(/\r?\n/).map(value => value.trim()).filter(Boolean);
    else if (element.value !== '') output[param.name] = element.value;
  });
  return output;
}

async function runTool(event) {
  event.preventDefault();
  const button = $('run-tool');
  button.disabled = true;
  button.textContent = '處理中…';
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
    setStatus(data.ok ? '執行完成' : '執行失敗', data.ok);
  } catch (error) {
    const data = { ok: false, message: error.message };
    $('result').textContent = JSON.stringify(data, null, 2);
    renderResult(data);
    setStatus('連線失敗', false);
  } finally {
    button.disabled = false;
    button.textContent = '執行工具';
  }
}

function renderResult(data) {
  const cards = [];
  if (data.message) cards.push(resultCard('訊息', data.message));
  Object.entries(data.outputs || {}).forEach(([key, value]) => cards.push(resultCard(key, value)));
  if (data.manifest_path) cards.push(resultCard('Manifest', data.manifest_path));
  (data.warnings || []).forEach((warning) => cards.push(resultCard('注意', warning, true)));
  if (!cards.length) cards.push(resultCard(data.ok ? '完成' : '錯誤', data.ok ? '工具已完成，沒有額外輸出。' : (data.error_code || '未提供錯誤資訊')));
  $('result-summary').innerHTML = cards.join('');
}

function resultCard(label, value, warning = false) {
  const displayValue = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return `<div class="result-card${warning ? ' warning' : ''}"><div class="result-card-label">${escapeHtml(label)}</div><div class="result-card-value">${escapeHtml(displayValue)}</div></div>`;
}

async function copyTask() {
  const task = { action: selected.action, params: collectParams() };
  const text = JSON.stringify(task, null, 2);
  try {
    await navigator.clipboard.writeText(text);
    $('result').textContent = text;
    $('result-summary').innerHTML = resultCard('JSON task', '已複製到剪貼簿');
    setStatus('已複製', true);
  } catch (_error) {
    $('result').textContent = text;
    document.querySelector('.raw-result').open = true;
    $('result-summary').innerHTML = resultCard('JSON task', '瀏覽器未允許剪貼簿存取，請從下方手動複製。', true);
    setStatus('請手動複製', null);
  }
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
