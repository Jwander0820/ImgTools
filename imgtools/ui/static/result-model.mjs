export function describeResult(data) {
  const outputs = data.outputs || {};
  const files = Array.isArray(outputs.files) ? outputs.files : [];
  const operations = outputs.operations || [];
  const conflicts = outputs.conflicts || [];
  const metadata = Object.entries(outputs.metadata || {});
  const kind = outputs.metadata ? 'metadata' : outputs.operations || outputs.conflicts ? 'rename' : 'files';
  let title = data.ok ? '處理完成' : '無法完成處理';
  let message = data.ok ? `已建立 ${files.length} 個輸出檔案` : data.message || '請檢查輸入後再試一次';
  if (kind === 'metadata' && data.ok) {
    title = '讀取完成'; message = `共 ${metadata.length} 個欄位，可在下方搜尋`;
  }
  if (kind === 'rename') {
    title = conflicts.length ? '發現名稱衝突，未套用變更' : outputs.dry_run ? '預覽完成，尚未修改檔案' : '改名完成';
    message = `${operations.length} 項${outputs.dry_run ? '預計變更' : '變更'}${conflicts.length ? `，${conflicts.length} 項衝突` : ''}`;
    if (!operations.length && !conflicts.length) message = '沒有符合條件的名稱';
  }
  if (data.error_code === 'CANCELLED') {
    title = '任務已取消';
    message = files.length ? `保留 ${files.length} 個已完成的輸出` : '沒有完成的輸出檔案';
  }
  return {kind, title, message, files, operations, conflicts, metadata,
    images: files.filter(path => /\.(png|jpe?g|webp|bmp|tiff?|gif)$/i.test(path))};
}
