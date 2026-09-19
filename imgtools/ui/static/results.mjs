import {$, tools} from './state.mjs';
import {escapeHtml, checkIcon, alertIcon, setStatus} from './dom.mjs';
import {describeResult} from './result-model.mjs';

let previewVersion = 0;
let toastTimer;

export function renderTransientMessage(title, message, warning = false) {
  const toast = $('notice');
  toast.textContent = `${title}：${message}`;
  toast.classList.toggle('warning', warning);
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 6500);
}

export function renderResult(data, job = null) {
  const version = ++previewVersion;
  const view = describeResult(data);
  const title = job?.title || tools.find(tool => tool.action === data.action)?.title || data.action || '任務';
  const panel = $('output-panel');
  panel.hidden = false;
  $('result-tool').textContent = title;
  $('result').textContent = JSON.stringify(data, null, 2);
  const status = data.error_code === 'CANCELLED' ? '已取消' : !data.ok ? '處理失敗' : view.kind === 'metadata' ? '讀取完成' : data.outputs?.dry_run ? '預覽完成' : '處理完成';
  setStatus(status, data.error_code === 'CANCELLED' ? null : data.ok);
  const tone = data.error_code === 'CANCELLED' ? 'cancelled' : data.ok ? 'success' : 'failure';
  $('result-summary').innerHTML = `<div class="result-hero ${tone}"><span class="result-symbol">${data.ok ? checkIcon() : alertIcon()}</span><div><strong>${escapeHtml(view.title)}</strong><span>${escapeHtml(view.message)}</span></div></div>`;
  const summary = $('result-summary');
  if (view.kind === 'rename') renderRename(summary, view);
  if (view.kind === 'metadata') renderMetadata(summary, view.metadata);
  if (view.files.length) renderFiles(summary, view.files, job);
  if (view.images.length) renderImages(summary, view.images, version);
  for (const warning of data.warnings || []) {
    const node = document.createElement('p'); node.className = 'result-warning'; node.textContent = warning; summary.append(node);
  }
  $('manifest-note').hidden = !data.manifest_path;
  $('manifest-note').textContent = data.manifest_path ? '本次執行紀錄已保存在這台電腦。' : '';
  $('show-result').disabled = false;
}

function renderRename(parent, view) {
  const rows = [...view.conflicts.map(row => ({...row, state: '名稱衝突'})), ...view.operations.map(row => ({...row, state: view.conflicts.length ? '未套用' : view.title.startsWith('預覽') ? '預計變更' : '已改名'}))];
  const wrapper = document.createElement('div'); wrapper.className = 'table-scroll';
  wrapper.innerHTML = '<table><caption>改名前後對照</caption><thead><tr><th>原始名稱／路徑</th><th>目標名稱／路徑</th><th>狀態</th></tr></thead><tbody></tbody></table>';
  let count = 0;
  const more = document.createElement('button'); more.type = 'button'; more.className = 'secondary';
  const append = () => {
    wrapper.querySelector('tbody').insertAdjacentHTML('beforeend', rows.slice(count, count + 100).map(row => `<tr><td>${escapeHtml(row.source)}</td><td>${escapeHtml(row.destination)}</td><td>${row.state}</td></tr>`).join(''));
    count += 100; more.hidden = count >= rows.length; more.textContent = `顯示更多（剩餘 ${Math.max(0, rows.length - count)} 項）`;
  };
  more.onclick = append; parent.append(wrapper, more); append();
}

function renderMetadata(parent, rows) {
  const section = document.createElement('section'); section.className = 'metadata-result';
  section.innerHTML = '<label for="metadata-search">搜尋中繼資料</label><input id="metadata-search" type="search" placeholder="輸入欄位或內容"><p id="metadata-count" role="status"></p><div class="table-scroll"><table><caption>圖片中繼資料</caption><thead><tr><th>欄位</th><th>內容</th></tr></thead><tbody></tbody></table></div>';
  const input = section.querySelector('input');
  const update = () => {
    const query = input.value.trim().toLocaleLowerCase();
    const filtered = rows.filter(row => row.join(' ').toLocaleLowerCase().includes(query));
    section.querySelector('tbody').innerHTML = filtered.map(([key,value]) => `<tr><th scope="row">${escapeHtml(key)}</th><td>${escapeHtml(value)}</td></tr>`).join('');
    section.querySelector('#metadata-count').textContent = `顯示 ${filtered.length} / ${rows.length} 個欄位`;
  };
  input.oninput = update; parent.append(section); update();
}

function renderFiles(parent, files, job) {
  const list = document.createElement('div'); list.className = 'result-files'; parent.append(list);
  const more = document.createElement('button'); more.type = 'button'; more.className = 'secondary'; parent.append(more);
  let count = 0;
  const append = () => {
    for (const path of files.slice(count, count + 40)) {
      const card = document.createElement('div'); card.className = 'result-file';
      card.innerHTML = `<div><strong>${escapeHtml(path.split(/[\\/]/).pop())}</strong><code>${escapeHtml(path)}</code></div><div class="result-file-actions"><button type="button" data-copy>複製路徑</button>${job ? '<button type="button" data-open="file">開啟檔案</button><button type="button" data-open="folder">所在資料夾</button>' : ''}</div>`;
      card.querySelector('[data-copy]').onclick = async () => {
        try { await navigator.clipboard.writeText(path); renderTransientMessage('已複製', path); }
        catch { renderTransientMessage('無法複製', '請選取上方路徑手動複製。', true); }
      };
      card.querySelectorAll('[data-open]').forEach(button => { button.onclick = async () => {
        button.disabled = true;
        try {
          const response = await fetch('/api/open', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({job_id:job.id,path,mode:button.dataset.open})});
          const data = await response.json();
          if (!response.ok || !data.ok) throw Error(data.message || '無法開啟檔案');
        } catch(error) { renderTransientMessage('無法開啟', error.message, true); }
        finally { button.disabled = false; }
      }; });
      list.append(card);
    }
    count += 40; more.hidden = count >= files.length; more.textContent = `顯示更多檔案（剩餘 ${Math.max(0, files.length - count)} 個）`;
  };
  more.onclick = append; append();
}

function renderImages(parent, paths, version) {
  const section = document.createElement('section'); section.className = 'result-preview';
  section.innerHTML = `<div class="result-preview-heading"><label for="result-image-choice">成品預覽</label><select id="result-image-choice">${paths.map((path,i) => `<option value="${i}">${i+1}. ${escapeHtml(path.split(/[\\/]/).pop())}</option>`).join('')}</select></div><div class="result-preview-stage"><img id="result-preview-image" class="result-preview-image" alt="輸出圖片預覽" hidden><p id="result-preview-empty">載入預覽中…</p></div><p class="result-preview-status" role="status"></p>`;
  let requestVersion = 0;
  const load = async () => {
    const requestId = ++requestVersion;
    const image = section.querySelector('img'); const empty = section.querySelector('#result-preview-empty');
    image.hidden = true; empty.hidden = false; empty.textContent = '載入預覽中…';
    try {
      const response = await fetch('/api/preview', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:paths[Number(section.querySelector('select').value)]})});
      const data = await response.json(); const preview = data.previews?.[0];
      if (!data.ok || !preview?.data_url) throw Error(preview?.error || data.message || '預覽無法載入');
      if (version !== previewVersion || requestId !== requestVersion) return;
      image.src = preview.data_url; image.hidden = false; empty.hidden = true;
      section.querySelector('.result-preview-status').textContent = `${preview.width} × ${preview.height} px · 縮圖僅供檢視；GIF / 多頁 TIF 顯示第一幀／頁。`;
    } catch(error) {
      if (version !== previewVersion || requestId !== requestVersion) return;
      empty.textContent = `成品已保存，但無法預覽：${error.message}`;
    }
  };
  section.querySelector('select').onchange = load; parent.append(section); load();
}
