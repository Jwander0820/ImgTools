import {selected} from './state.mjs';
import {watermarkInputParam} from './watermark.mjs';

export function isWatermarkAction() {
  return selected?.action === 'watermark.text' || selected?.action === 'watermark.batch_text';
}

export function isStackVerticalAction() {
  return selected?.action === 'merge.stack_vertical';
}

export function interactivePreviewParam() {
  if (selected?.action === 'merge.dialogue_stack' || isStackVerticalAction()) {
    return selected.params.find((param) => param.name === 'input_paths') || null;
  }
  return isWatermarkAction() ? watermarkInputParam() : null;
}

export function shouldAutoPreview(param) {
  return Boolean(
    (selected?.action === 'merge.dialogue_stack' && param.name === 'input_paths')
      || (isStackVerticalAction() && param.name === 'input_paths')
      || (isWatermarkAction() && ['input_path', 'input_paths'].includes(param.name)),
  );
}

export function loadDialoguePreviewImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('預覽圖片載入失敗'));
    image.src = dataUrl;
  });
}

export function drawDialogueCutGuide(context, y, width, ratio) {
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
