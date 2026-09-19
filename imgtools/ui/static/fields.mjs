import {$, selected, previewImages, previewErrors, previewPendingPaths, previewRequestTimers} from './state.mjs';
import {renderTransientMessage} from './results.mjs';
import {valueFor, inputPlaceholder, defaultHintFor, booleanHint} from './form.mjs';
import {isWatermarkAction, isStackVerticalAction, shouldAutoPreview} from './preview.mjs';
import {drawWatermarkPreview} from './watermark.mjs';
import {drawStackVerticalPreview} from './stack.mjs';
import {drawDialoguePreview} from './dialogue.mjs';
import {setStatus, escapeHtml} from './dom.mjs';

export function renderField(param) {
  const block = document.createElement('div');
  const id = `param_${param.name}`;
  const value = valueFor(param);
  const fullWidth = param.type === 'path_list' || ['folder', 'path'].includes(param.type);
  block.className = `field${fullWidth ? ' full' : ''}`;

  if (param.type === 'bool') {
    block.innerHTML = `
      <label class="check-field" for="${id}">
        <input id="${id}" type="checkbox" ${value ? 'checked' : ''}>
        <span><strong>${escapeHtml(param.label)}</strong><span class="hint">${escapeHtml(booleanHint(param.name) || param.description || '')}</span></span>
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
    const inputType = param.name === 'password' ? 'password' : ['int', 'float'].includes(param.type) ? 'number' : 'text';
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
  const input = block.querySelector(`#${id}`);
  if (param.required) { input.required = true; input.setAttribute('aria-required', 'true'); }
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

export function pathItems(id) {
  const element = $(id);
  if (!element) return [];
  return element.value.split(/\r?\n/).map(normalizeLocalPath).filter(Boolean);
}

export function setPathItems(id, items, param) {
  const element = $(id);
  element.value = items.join('\n');
  element.dispatchEvent(new Event('change', { bubbles: true }));
  renderPathOrder(id, param);
}

export function movePathItem(id, index, direction, param) {
  const items = pathItems(id);
  const target = index + direction;
  if (target < 0 || target >= items.length) return;
  [items[index], items[target]] = [items[target], items[index]];
  setPathItems(id, items, param);
}

export function removePathItem(id, index, param) {
  const items = pathItems(id);
  items.splice(index, 1);
  setPathItems(id, items, param);
}

export function renderPathOrder(id, param) {
  const container = $(`${id}_order`);
  if (!container) return;
  const items = pathItems(id);
  const min = param.min_items ?? 1;
  const max = param.max_items ?? null;
  const valid = items.length >= min && (max === null || items.length <= max);
  const limit = max === null ? `${items.length} 張` : `${items.length} / ${max} 張`;

  const heading = document.createElement('div');
  heading.className = `path-order-heading${valid ? '' : ' invalid'}`;
  const orderLabel = isWatermarkAction() ? '待處理圖片' : selected?.action === 'merge.panorama_translation' ? '動畫畫面順序' : '由上到下的疊圖順序';
  heading.innerHTML = `<strong>${orderLabel}</strong><span>${escapeHtml(limit)}</span>`;
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
    const showThumbnail = shouldAutoPreview(param) && param.name === 'input_paths';
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

export function pickerMode(param) {
  if (param.type === 'folder') return 'folder';
  if (param.type === 'path_list') return 'files';
  if (param.name.startsWith('output_')) return 'save';
  return 'file';
}

export function previewPathsFor(param) {
  const id = `param_${param.name}`;
  if (param.type === 'path_list') return pathItems(id);
  const path = normalizeLocalPath($(id)?.value || '');
  return path ? [path] : [];
}

export function previewErrorFor(paths) {
  return paths.map((path) => previewErrors.get(path)).find(Boolean) || '';
}

export function refreshInteractivePreview() {
  if (isStackVerticalAction()) {
    const param = selected.params.find((item) => item.name === 'input_paths');
    if (param) renderPathOrder('param_input_paths', param);
    drawStackVerticalPreview();
  }
  if (selected?.action === 'merge.dialogue_stack') drawDialoguePreview();
  if (isWatermarkAction()) drawWatermarkPreview();
}

export function queueLocalPreviews(param, { immediate = false } = {}) {
  if (!shouldAutoPreview(param)) return;
  const key = `param_${param.name}`;
  const previous = previewRequestTimers.get(key);
  if (previous) window.clearTimeout(previous);
  const delay = immediate ? 0 : 350;
  const action = selected.action;
  const timer = window.setTimeout(() => {
    previewRequestTimers.delete(key);
    if (selected?.action !== action) return;
    requestLocalPreviews(param);
  }, delay);
  previewRequestTimers.set(key, timer);
}

export async function requestLocalPreviews(param) {
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

export async function openPicker(param, button) {
  const action = selected.action;
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
    if (selected?.action !== action) return;
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

export function normalizeLocalPath(value) {
  const path = String(value).trim();
  if (path.length >= 2 && path.startsWith('"') && path.endsWith('"')) {
    return path.slice(1, -1);
  }
  return path;
}
