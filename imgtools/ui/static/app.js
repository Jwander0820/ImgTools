import {$, CATEGORY_LABELS, CATEGORY_ICONS, tools, selected, activeCategory, searchTerm, outputNaming, preferences, formState, setTools, setSelected, setActiveCategory, setSearchTerm, setOutputNamingValue, setPreferences} from './state.mjs';
import {startJobs} from './jobs.mjs';
import {renderForm, saveFormState} from './form.mjs';
import {setStatus, escapeHtml} from './dom.mjs';

export async function boot() {
  $('library-toggle').onclick = () => {
    const expanded = document.querySelector('.tool-shelf').classList.toggle('expanded');
    $('library-toggle').setAttribute('aria-expanded', String(expanded));
  };
  document.querySelectorAll('[data-output-naming]').forEach((button) => {
    button.addEventListener('click', () => setOutputNaming(button.dataset.outputNaming));
  });
  renderOutputNaming();
  $('pdf-default-dpi').addEventListener('change', savePdfDefaultDpi);
  $('quick-settings').addEventListener('click', toggleQuickEditor);
  $('tool-search').addEventListener('input', (event) => {
    setSearchTerm(event.target.value.trim().toLocaleLowerCase());
    renderTools();
  });

  try {
    const response = await fetch('/api/tools');
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法載入工具清單');
    setTools(data.tools || []);
    await refreshPreferences();
    const firstQuickAction = preferences.quick_actions[0]?.action;
    setSelected(tools.find((tool) => tool.action === firstQuickAction)
      || tools.find((tool) => tool.featured)
      || tools[0]
      || null);
    renderCategories();
    renderQuickActions();
    renderQuickEditor();
    renderTools();
    renderForm();
    startJobs();
  } catch (error) {
    $('tool-title').textContent = '工具清單載入失敗';
    $('tool-description').textContent = `${error.message}。請重新啟動 ImgTools 後再試一次。`;
    setStatus('載入失敗', false);
  }
}

export async function refreshPreferences() {
  try {
    const response = await fetch('/api/preferences');
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法載入常用功能設定');
    setPreferences(data);
  } catch (_error) {
    if (!preferences.quick_actions.length) {
      setPreferences({
        pinned_actions: [],
        usage: {},
        quick_actions: tools.filter((tool) => tool.featured).slice(0, 8).map((tool) => ({
          action: tool.action, source: 'default', successful_runs: 0,
        })),
        max_pinned: 8,
        pdf_default_dpi: 192,
        output_naming: 'fixed',
      });
    }
  }
  syncPdfDefaultDpi();
  syncOutputNaming();
}

export function syncOutputNaming() {
  setOutputNamingValue(preferences.output_naming === 'source' ? 'source' : 'fixed');
  renderOutputNaming();
}

export function syncPdfDefaultDpi() {
  const dpi = Number(preferences.pdf_default_dpi) || 192;
  $('pdf-default-dpi').value = String(dpi);
  tools.filter((tool) => tool.category === 'pdf').forEach((tool) => {
    const dpiParam = tool.params.find((param) => param.name === 'dpi');
    if (dpiParam) dpiParam.default = dpi;
  });
}

export async function savePdfDefaultDpi(event) {
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
    setPreferences(data);
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

export async function setOutputNaming(mode) {
  if (!['fixed', 'source'].includes(mode) || mode === outputNaming) return;
  saveFormState();
  const previous = outputNaming;
  setOutputNamingValue(mode);
  renderOutputNaming();
  renderForm();
  try {
    const response = await fetch('/api/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ output_naming: mode }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || '無法保存預設檔名設定');
    setPreferences(data);
    syncOutputNaming();
  } catch (error) {
    setOutputNamingValue(previous);
    renderOutputNaming();
    renderForm();
    setStatus(`保存檔名設定失敗：${error.message}`, false);
  }
}

export function renderOutputNaming() {
  document.querySelectorAll('[data-output-naming]').forEach((button) => {
    const isActive = button.dataset.outputNaming === outputNaming;
    button.classList.toggle('active', isActive);
    button.setAttribute('aria-pressed', String(isActive));
  });
}

export function iconFor(category) {
  return CATEGORY_ICONS[category] || CATEGORY_ICONS.merge;
}

export function renderQuickActions() {
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

export function preferenceLabel(source) {
  if (source === 'pinned') return '已釘選';
  if (source === 'frequent') return '常用';
  return '預設';
}

export function toggleQuickEditor() {
  const editor = $('quick-action-editor');
  const isOpening = editor.hidden;
  editor.hidden = !isOpening;
  $('quick-settings').setAttribute('aria-expanded', String(isOpening));
  if (isOpening) renderQuickEditor();
}

export function renderQuickEditor() {
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

export async function togglePinnedAction(action, button) {
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
    setPreferences(data);
    renderQuickActions();
    renderQuickEditor();
    $('quick-editor-status').textContent = '已保存到這台電腦。';
  } catch (error) {
    $('quick-editor-status').textContent = `保存失敗：${error.message}`;
    button.disabled = false;
  }
}

export function renderCategories() {
  const categories = ['all', ...new Set(tools.map((tool) => tool.category))];
  $('category-filters').replaceChildren(...categories.map((category) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `filter-chip${activeCategory === category ? ' active' : ''}`;
    button.textContent = CATEGORY_LABELS[category] || category;
    button.setAttribute('aria-pressed', String(activeCategory === category));
    button.addEventListener('click', () => {
      setActiveCategory(category);
      renderCategories();
      renderTools();
    });
    return button;
  }));
}

export function visibleTools() {
  return tools.filter((tool) => {
    const categoryMatches = activeCategory === 'all' || tool.category === activeCategory;
    const haystack = `${tool.title} ${tool.action} ${tool.description}`.toLocaleLowerCase();
    return categoryMatches && (!searchTerm || haystack.includes(searchTerm));
  });
}

export function renderTools() {
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

export function selectTool(tool, shouldScroll) {
  saveFormState();
  setSelected(tool);
  renderQuickActions();
  renderTools();
  renderForm();
  document.querySelector('.tool-shelf').classList.remove('expanded');
  $('library-toggle').setAttribute('aria-expanded', 'false');
  if (shouldScroll) $('tool-intro').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

boot();
