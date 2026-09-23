import {$, CATEGORY_LABELS, selected, outputNaming, formState} from './state.mjs';
import {runTool, syncRunButton} from './jobs.mjs';
import {renderTransientMessage} from './results.mjs';
import {renderField, renderPathOrder, queueLocalPreviews, normalizeLocalPath} from './fields.mjs';
import {isWatermarkAction, interactivePreviewParam} from './preview.mjs';
import {renderWatermarkEditor, initWatermarkEditor} from './watermark.mjs';
import {renderStackVerticalPreview, initStackVerticalPreview} from './stack.mjs';
import {renderDialoguePreview, initDialoguePreview} from './dialogue.mjs';
import {setStatus, escapeHtml} from './dom.mjs';

export function renderForm() {
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
    <button class="primary" id="run-tool" type="submit" form="form">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 5 11 7-11 7z"/></svg>
      <span>開始處理</span>
    </button>
    <button class="secondary" id="show-result" type="button" ${$('output-panel').hidden ? 'disabled' : ''}>查看結果</button>
    <details class="task-options"><summary>進階操作</summary><button id="copy-task" type="button">複製工作 JSON</button></details>
    <span class="action-note">${escapeHtml(outputNamingNote())}</span>`;
  $('actionbar').replaceChildren(...actions.childNodes);

  form.replaceChildren(...nodes);
  form.onsubmit = runTool;
  $('copy-task').onclick = copyTask;
  $('show-result').onclick = () => $('output-panel').scrollIntoView({block:'start'});
  form.addEventListener('change', syncRunButton);
  syncRunButton();
  selected.params
    .filter((param) => param.type === 'path_list')
    .forEach((param) => renderPathOrder(`param_${param.name}`, param));
  if (selected.action === 'merge.stack_vertical') initStackVerticalPreview();
  if (selected.action === 'merge.dialogue_stack') initDialoguePreview();
  if (isWatermarkAction()) initWatermarkEditor();
  const previewParam = interactivePreviewParam();
  if (previewParam) queueLocalPreviews(previewParam, { immediate: true });
}

export function outputNamingNote() {
  if (selected?.action.startsWith('rename.')) return '先預覽改名前後的名稱；勾選套用變更才會修改檔案';
  if (selected?.category === 'metadata') return '讀取圖片資訊，不會修改來源檔案';
  return outputNaming === 'source'
    ? '留白時跟隨來源命名；重名會先自動加編號'
    : '留白時使用 output；重名會先自動加編號';
}

export function valueFor(param) {
  const saved = formState[selected.action];
  if (saved && Object.hasOwn(saved, param.name)) return saved[param.name];
  return param.default === undefined ? '' : param.default;
}

export function inputPlaceholder(param) {
  const hint = defaultHintFor(param);
  if (hint) return `留白即可使用${hint}`;
  if (param.type === 'path') return '貼上完整檔案路徑，或按「選擇」';
  if (param.type === 'folder') return '貼上資料夾路徑，或按「選擇」';
  return param.required ? '請輸入內容' : '選填';
}

export function defaultHintFor(param) {
  if (outputNaming === 'source' && param.source_default_hint) return param.source_default_hint;
  return param.default_hint || '';
}

export function booleanHint(name) {
  if (name === 'overwrite') return '允許覆蓋已存在的明確輸出路徑';
  if (name === 'confirm') return '關閉時只預覽變更，不會修改檔案';
  return '';
}

export function readFormValues(includeEmpty = false) {
  const output = { output_naming: outputNaming };
  if (!selected) return output;
  selected.params.forEach((param) => {
    const element = $(`param_${param.name}`);
    if (!element) return;
    if (element.disabled && !includeEmpty) return;
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

export function collectParams() {
  return readFormValues(false);
}

export function saveFormState() {
  if (selected && $('form').childElementCount) formState[selected.action] = readFormValues(true);
}

export async function copyTask() {
  const task = { action: selected.action, params: collectParams() };
  const text = JSON.stringify(task, null, 2);
  try {
    await navigator.clipboard.writeText(text);
    renderTransientMessage('工作 JSON 已複製', '可以貼到 CLI、文件或下一次工作中。');
  } catch (_error) {
    renderTransientMessage('無法複製', '瀏覽器未允許剪貼簿存取，請確認瀏覽器權限後重試。', true);
  }
}
