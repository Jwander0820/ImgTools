const numeric=(id,label,value,min,max,step=1,help='')=>`<label for="${id}">${label}<input id="${id}" name="${id}" type="number" inputmode="decimal" min="${min}" max="${max}" step="${step}" value="${value}" required>${help?`<small>${help}</small>`:''}</label>`;
export function settingsMarkup(action) {
  if(action==='dialogue')return numeric('ratio','字幕帶起點（%）',88,1,99,0.1,'也可使用預覽旁的滑桿。')+numeric('spacing','每句間距（px）',85,1,16384,1,'上限隨字幕帶高度調整。');
  if(action==='watermark')return `<label for="text">浮水印文字（必填）<input id="text" name="text" maxlength="200" value="© 我的影像" required></label>`+
    numeric('font-size','字級（px，0 為自動）',0,0,500)+numeric('angle','角度（度）',30,-180,180)+numeric('opacity','不透明度（%）',25,0,100)+
    `<label for="color">文字顏色<input id="color" type="color" value="#000000"></label><label for="position">位置<select id="position"><option value="center">中央</option><option value="top_left">左上</option><option value="top_right">右上</option><option value="bottom_left">左下</option><option value="bottom_right">右下</option><option value="custom">自訂（可拖曳）</option></select></label><div id="custom-position" hidden>`+
    numeric('position-x','水平位置（%）',50,0,100,0.1)+numeric('position-y','垂直位置（%）',50,0,100,0.1)+
    `</div><label class="check"><input id="repeat" type="checkbox">重複平鋪</label>`;
  if(action==='pdf')return numeric('page','頁碼（從 1 開始）',1,1,999999)+numeric('dpi','解析度（DPI）',144,36,600,1,'提高 DPI 會增加像素與記憶體需求。')+`<label for="password">PDF 密碼（選填）<input id="password" type="password" autocomplete="off"></label>`;
  return '<p class="muted">用清單中的 ↑ ↓ 調整順序。第一張會放在最上方。</p>';
}
const range=(id,bind,label,min,max,step)=>`<label for="${id}"><span>${label} <output id="${id}-value" for="${id}"></output></span><input id="${id}" data-bind="${bind}" type="range" min="${min}" max="${max}" step="${step}"></label>`;
export function editorMarkup(action) {
  if(action==='dialogue')return range('ratio-range','ratio','字幕帶起點',1,99,0.1)+range('spacing-range','spacing','每句間距',1,220,1);
  if(action==='watermark')return range('size-range','font-size','浮水印大小',1,500,1)+range('angle-range','angle','旋轉角度',-180,180,1)+'<p id="gesture-help"></p>';
  return '';
}
