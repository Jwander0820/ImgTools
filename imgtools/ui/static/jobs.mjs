import {$, selected} from './state.mjs';
import {collectParams, saveFormState} from './form.mjs';
import {isWatermarkAction} from './preview.mjs';
import {escapeHtml} from './dom.mjs';
import {renderResult, renderTransientMessage} from './results.mjs';
import {refreshPreferences, renderQuickActions, renderQuickEditor} from './app.js';
import {createTaskStore} from './task-store.mjs';

const labels = {queued:'排隊中',running:'處理中',cancelling:'取消中',completed:'完成',failed:'失敗',cancelled:'已取消'};
const active = job => ['queued','running','cancelling'].includes(job.status);
let started = false;
let lastMarkup = '';
async function request(url, payload) {
  const response = await fetch(url, {signal:AbortSignal.timeout(10000), ...(payload ? {method:'POST', headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)} : {})});
  const data = await response.json();
  if (!response.ok || !data.ok) {
    const error = Error(data.message || '本機服務未回應'); error.rejected = true; throw error;
  }
  return data;
}
const store = createTaskStore({request, onChange: renderJobs, onResult: job => {
  renderResult(job.result, job);
  if (job.result.ok) refreshPreferences().then(() => {renderQuickActions();renderQuickEditor();});
}});

export function startJobs() {
  if (started) return; started = true;
  $('retry-jobs').onclick = async () => {
    try { if (store.snapshot().uncertain) await store.retrySubmission(); else await store.refresh(); }
    catch(error) { renderTransientMessage('連線尚未恢復', error.message, true); }
  };
  const poll = async () => {
    try { await store.refresh(); } catch { /* The retained queue and retry UI explain disconnection. */ }
    setTimeout(poll, document.hidden ? 3000 : 1000);
  };
  poll();
}

export function syncRunButton() {
  const button = $('run-tool'); if (!button || !selected) return;
  const state = store.snapshot();
  const job = state.jobs.find(job => job.action === selected.action && active(job));
  if (selected.action.startsWith('rename.')) {
    const apply = Boolean($('param_confirm')?.checked);
    $('danger-badge').textContent = apply ? '將實際修改檔名' : '預覽模式';
    $('danger-badge').className = apply ? 'high' : 'preview';
  }
  button.disabled = !state.ready || state.submitting || state.uncertain || store.busy(selected.action);
  button.querySelector('span').textContent = !state.ready ? '連接任務服務中…' : state.submitting ? '送出中…' : state.uncertain ? '請先確認送出狀態' : job ? `${labels[job.status]}，請查看任務列` : state.jobs.some(active) ? '加入佇列' : selected.action.startsWith('rename.') ? ($('param_confirm')?.checked ? '套用改名' : '預覽改名') : '開始處理';
}

export async function runTool(event) {
  event.preventDefault();
  saveFormState();
  const action = selected.action;
  const params = collectParams();
  if (isWatermarkAction() && !String(params.text || '').trim()) {
    $('param_text')?.setCustomValidity('請輸入浮水印文字。'); $('param_text')?.reportValidity(); return;
  }
  try { await store.submit(action, params); }
  catch(error) { renderTransientMessage('任務送出未完成', error.message, true); }
}

function renderJobs(state) {
  const current = state.jobs.filter(active);
  $('job-tray').hidden = !state.jobs.length && !state.error && !state.submitting;
  $('job-summary').textContent = state.submitting ? '正在送出任務…' : current.length ? `${current.length} 個任務進行中／等待中` : '目前沒有執行中的任務';
  $('job-error').textContent = state.uncertain ? '送出狀態未確認，請按「重新連線／確認送出」；重試不會重複執行。' : state.error;
  $('retry-jobs').hidden = !state.error && !state.uncertain;
  const card = job => `<article class="job-row" data-job-id="${job.id}"><div><strong>${escapeHtml(job.title)}</strong><span>${labels[job.status]}${job.queue_position ? ` · 第 ${job.queue_position} 順位` : ''} · <time data-elapsed="${job.id}">${Math.floor(job.elapsed_seconds || 0)}</time> 秒</span><small>${active(job) ? escapeHtml(job.progress?.message || '') : ''}</small>${job.progress?.total && active(job) ? `<progress value="${job.progress.completed || 0}" max="${job.progress.total}" aria-label="${escapeHtml(job.title)}進度"></progress>` : ''}</div>${job.can_cancel ? `<button type="button" data-cancel="${job.id}">取消</button>` : ''}${(job.result || job.has_result) ? `<button type="button" data-result="${job.id}">查看結果</button>` : ''}</article>`;
  const markup = current.map(card).join('') + '|' + state.jobs.filter(job => !active(job)).slice(0,10).map(card).join('');
  // Keep focused controls in place while only the elapsed time changes.
  const stable = markup.replace(/(<time[^>]*>)\d+(<\/time>)/g,'$1$2');
  if (stable !== lastMarkup) {
    const focus = document.activeElement?.dataset;
    const focusId = focus?.cancel || focus?.result;
    $('active-jobs').innerHTML = current.map(card).join('');
    $('job-history').innerHTML = state.jobs.filter(job => !active(job)).slice(0,10).map(card).join('');
    $('job-tray').querySelectorAll('[data-cancel]').forEach(button => {button.onclick = async () => {
      button.disabled = true;
      try { await store.cancel(button.dataset.cancel); }
      catch(error) { button.disabled = false; renderTransientMessage('無法取消',error.message,true); }
    };});
    $('job-tray').querySelectorAll('[data-result]').forEach(button => {button.onclick = async () => {
      try {
        const job = await store.getResult(button.dataset.result);
        renderResult(job.result,job); $('output-panel').scrollIntoView({block:'start'});
      } catch (error) { renderTransientMessage('無法讀取結果', error.message, true); }
    };});
    if (focusId) $('job-tray').querySelector(`[data-cancel="${focusId}"], [data-result="${focusId}"]`)?.focus({preventScroll:true});
    lastMarkup = stable;
  } else {
    state.jobs.forEach(job => {const time = document.querySelector(`[data-elapsed="${job.id}"]`); if(time)time.textContent = Math.floor(job.elapsed_seconds || 0);});
  }
  syncRunButton();
}
