import {validateFiles,moveItem,outputName,LIMITS,checkSize,subtitleBand} from './model.mjs';
import {renderImages,pngBlob,yieldUI} from './render.mjs';
import {settingsMarkup,editorMarkup} from './fields.mjs';
import {createWatermarkEditor} from './watermark-editor.mjs';
const $=id=>document.getElementById(id);
const tools={
  dialogue:{title:'台詞疊圖',description:'保留第一張完整畫面，再接上後續圖片的字幕帶。請選擇 2～12 張同尺寸圖片。'},
  stack:{title:'直向疊圖',description:'依清單順序由上到下合成。請選擇 2～9 張同寬圖片，高度可以不同。'},
  watermark:{title:'文字浮水印',description:'為 1～12 張圖片加上文字。預覽第一張，產生後可逐張下載 PNG。'},
  pdf:{title:'PDF 單頁轉 PNG',description:'選擇一份 PDF，指定頁碼與解析度。檔案與密碼只在這個分頁使用。'}
};
let action='dialogue',entries=[],busy=false,version=0,timer,downloads=[],editor;
const number=(id)=>Number($(id).value);
function params(){
  if(action==='dialogue')return {ratio:number('ratio')/100,spacing:number('spacing')};
  if(action==='watermark')return {text:$('text').value,fontSize:number('font-size'),angle:number('angle'),opacity:number('opacity')/100,color:$('color').value,position:$('position').value,x:number('position-x')/100,y:number('position-y')/100,repeat:$('repeat').checked};
  if(action==='pdf')return {page:number('page'),dpi:number('dpi'),password:$('password').value};
  return {};
}
function message(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function clearResults(){for(const u of downloads)URL.revokeObjectURL(u);downloads=[];$('results').replaceChildren();}
function clearPreview(){const c=$('preview');c.width=1;c.height=1;c.hidden=true;$('preview-wrap').hidden=true;editor?.clear();$('empty').hidden=false;$('dimensions').textContent='尚無預覽';}
function releaseEntries(){for(const e of entries){e.image?.close?.();URL.revokeObjectURL(e.url);}entries=[];}
function lock(value){busy=value;$('inputs').disabled=value;$('editor-controls').disabled=value;editor?.setEnabled(!value);$('clear').disabled=value;for(const b of document.querySelectorAll('[data-tool]'))b.disabled=value;$('form').setAttribute('aria-busy',String(value));}
function invalidate(keepPreview=false){version++;clearTimeout(timer);clearResults();if(!keepPreview)clearPreview();}
function syncEditors(clampSpacing=false){
  $('editor-controls').hidden=!entries.length||!['dialogue','watermark'].includes(action);
  if(action==='dialogue'){
    const ratio=number('ratio')/100;
    const max=entries[0]?.image&&ratio>0&&ratio<1?subtitleBand(entries[0].image.height,ratio).height:220;
    $('spacing').max=$('spacing-range').max=String(max);
    if(clampSpacing&&number('spacing')>max)$('spacing').value=String(max);
    for(const key of ['ratio','spacing']){
      $(`${key}-range`).value=$(key).value;
      $(`${key}-range-value`).textContent=`${$(key).value}${key==='ratio'?'%':' px'}`;
    }
  }
  if(action==='watermark'){
    const size=number('font-size')||Math.min(500,Math.max(12,Math.round((entries[0]?.image.width||960)/24)));
    $('size-range').value=String(size);$('size-range-value').textContent=`${size} px${number('font-size')===0?'（自動）':''}`;
    $('angle-range').value=$('angle').value;$('angle-range-value').textContent=`${$('angle').value}°`;
    $('custom-position').hidden=$('position').value!=='custom';
    $('gesture-help').textContent=$('repeat').checked?'平鋪模式可用滑桿調整字級與角度。':'拖曳十字箭頭移動、斜箭頭縮放、環形箭頭旋轉。方向鍵可微調，Shift 加大步幅。';
  }
}
function drawList(){
  $('file-list').replaceChildren();
  entries.forEach((e,index)=>{
    const li=document.createElement('li');
    if(e.image){const img=document.createElement('img');img.src=e.url;img.alt='';li.append(img);}else{const span=document.createElement('span');span.textContent='PDF';li.append(span);}
    const name=document.createElement('span');name.className='name';name.textContent=`${index+1}. ${e.file.name}`;li.append(name);
    const group=document.createElement('span');group.className='arrows';
    for(const [label,delta] of [['↑',-1],['↓',1],['×',0]]){
      const b=document.createElement('button');b.type='button';b.textContent=label;b.setAttribute('aria-label',`${delta===0?'移除':delta===-1?'上移':'下移'} ${e.file.name}`);
      b.disabled=(delta===-1&&index===0)||(delta===1&&index===entries.length-1);
      b.onclick=()=>{if(busy)return;invalidate();if(delta)entries=moveItem(entries,index,delta);else{e.image?.close?.();URL.revokeObjectURL(e.url);entries.splice(index,1);}drawList();syncEditors(true);schedulePreview();};group.append(b);
    }
    li.append(group);$('file-list').append(li);
  });
}
function showCanvas(result){
  const target=$('preview'),scale=Math.min(1,1000/result.canvas.width,1800/result.canvas.height);
  target.width=Math.max(1,Math.round(result.canvas.width*scale));target.height=Math.max(1,Math.round(result.canvas.height*scale));
  target.getContext('2d').drawImage(result.canvas,0,0,target.width,target.height);target.hidden=false;$('empty').hidden=true;
  $('preview-wrap').hidden=false;editor.update(result);
  $('dimensions').textContent=`${result.width} × ${result.height} px`;
}
function schedulePreview(delay=100){
  if(action==='pdf'){message(entries.length?'設定頁碼後，按「產生 PNG」檢視與下載。':'請選擇一份 PDF。');return;}
  const token=version;
  timer=setTimeout(async()=>{
    if(!entries.length){message('選擇圖片，開始整理。');return;}
    let result;
    try {
      result=await renderImages(action,entries.map(e=>e.image),params(),{preview:true});
      if(token!==version)return;
      showCanvas(result);message('預覽已更新。確認後按「產生 PNG」。');
    } catch(e){if(token===version){clearPreview();message(e.message,true);}}
    finally{if(result){result.canvas.width=1;result.canvas.height=1;}}
  },delay);
}
function selectTool(next){
  if(busy)return;invalidate();releaseEntries();action=next;
  for(const b of document.querySelectorAll('[data-tool]'))b.setAttribute('aria-pressed',String(b.dataset.tool===action));
  $('tool-title').textContent=tools[action].title;$('description').textContent=tools[action].description;
  $('settings').innerHTML=settingsMarkup(action);$('editor-fields').innerHTML=editorMarkup(action);$('files').value='';$('files').multiple=action!=='pdf';$('files').accept=action==='pdf'?'.pdf':'image/png,image/jpeg,image/webp';
  $('pick-label').textContent=action==='pdf'?'選擇 PDF':'加入圖片';$('file-help').textContent=action==='pdf'?'選擇或拖曳一份 PDF · 最多 50 MB':'選擇或拖曳 PNG、JPEG、WebP 加入清單 · 每檔最多 50 MB';
  $('preview-note').textContent=action==='watermark'?'預覽第一張圖片；每張成果會套用相同設定。':'預覽會縮小顯示，輸出保留原始像素尺寸。';
  drawList();syncEditors();message(action==='pdf'?'請選擇一份 PDF。':'選擇圖片，開始整理。');
}
async function loadFiles(files){
  if(busy)return;
  if(!files.length)return;
  version++;clearTimeout(timer);lock(true);message('正在讀取檔案…');
  const added=[];
  try {
    validateFiles(action==='pdf'?files:[...entries.map(e=>e.file),...files],action);
    let total=entries.reduce((n,e)=>n+(e.image?e.image.width*e.image.height:0),0);
    for(const file of files){
      const url=URL.createObjectURL(file);let image;
      try {
        if(action!=='pdf'){
          image=await createImageBitmap(file,{imageOrientation:'from-image'});checkSize(image.width,image.height);
          total+=image.width*image.height;
          if(total>LIMITS.totalPixels)throw Error('來源圖片總像素最多 4,800 萬，請減少張數或縮小圖片。');
        }
        added.push({file,url,image});
      } catch(e){URL.revokeObjectURL(url);image?.close?.();throw e;}
      await yieldUI();
    }
    invalidate();if(action==='pdf')releaseEntries();entries.push(...added);
    drawList();syncEditors(true);schedulePreview();
  } catch(e){for(const entry of added){entry.image?.close?.();URL.revokeObjectURL(entry.url);}message(e.message||'讀取失敗，請確認檔案格式。',true);}
  finally{lock(false);$('files').value='';}
}
$('files').onchange=()=>loadFiles([...$('files').files]);
let dragDepth=0;
const isFileDrag=event=>[...(event.dataTransfer?.types||[])].includes('Files');
window.addEventListener('dragenter',event=>{if(isFileDrag(event)){event.preventDefault();dragDepth++;if(!busy)$('drop-zone').classList.add('drag-over');}});
window.addEventListener('dragover',event=>{if(isFileDrag(event)){event.preventDefault();event.dataTransfer.dropEffect=busy?'none':'copy';}});
window.addEventListener('dragleave',event=>{if(isFileDrag(event)&&--dragDepth<=0){dragDepth=0;$('drop-zone').classList.remove('drag-over');}});
window.addEventListener('drop',event=>{
  if(!isFileDrag(event))return;event.preventDefault();dragDepth=0;$('drop-zone').classList.remove('drag-over');
  if(busy){message('正在處理，請完成後再加入檔案。');return;}
  if([...event.dataTransfer.items].some(i=>i.webkitGetAsEntry?.()?.isDirectory)){message('請拖曳檔案，不支援整個資料夾。',true);return;}
  const files=[...event.dataTransfer.files];
  if(!files.length){message('請從電腦拖曳圖片或 PDF 檔案。',true);return;}
  loadFiles(files);
});
function settingsChanged(event){
  if(busy)return;
  const bind=event.target.dataset.bind;if(bind)$(bind).value=event.target.value;
  syncEditors((bind||event.target.id)==='ratio');invalidate(true);schedulePreview();
}
$('settings').oninput=settingsChanged;$('editor-fields').oninput=settingsChanged;
editor=createWatermarkEditor({wrap:$('preview-wrap'),outline:$('wm-outline'),move:$('wm-move'),resize:$('wm-resize'),rotate:$('wm-rotate'),onChange(change){
  if(busy||action!=='watermark')return;
  if(change.position)$('position').value=change.position;
  if(change.x!==undefined)$('position-x').value=(change.x*100).toFixed(1);
  if(change.y!==undefined)$('position-y').value=(change.y*100).toFixed(1);
  if(change.fontSize!==undefined)$('font-size').value=String(change.fontSize);
  if(change.angle!==undefined)$('angle').value=String(change.angle);
  syncEditors();invalidate(true);schedulePreview(0);
}});
$('clear').onclick=()=>{selectTool(action);};
for(const b of document.querySelectorAll('[data-tool]'))b.onclick=()=>selectTool(b.dataset.tool);
$('form').onsubmit=async(event)=>{
  event.preventDefault();if(busy)return;
  if(!entries.length){message('請先選擇檔案。',true);return;}
  invalidate();lock(true);message('正在產生 PNG，請保留這個分頁…');await yieldUI();
  const p=params();
  try {
    const count=action==='watermark'?entries.length:1;
    for(let index=0;index<count;index++){
      let result;
      try{
        if(action==='pdf'){
          const {renderPdf}=await import('./pdf.mjs');result=await renderPdf(entries[0].file,p);
        }else result=await renderImages(action,action==='watermark'?[entries[index].image]:entries.map(e=>e.image),p);
        if(index===0)showCanvas(result);
        const blob=await pngBlob(result.canvas),url=URL.createObjectURL(blob);downloads.push(url);
        const source=action==='watermark'?entries[index]:entries[entries.length-1];
        const filename=outputName(source.file.name,action==='pdf'?`page-${p.page}`:action);
        const link=document.createElement('a');link.href=url;link.download=filename;
        const title=document.createElement('span');title.textContent=`下載 ${filename}`;
        const info=document.createElement('small');info.textContent=`${(blob.size/1024/1024).toFixed(2)} MB`;
        link.append(title,info);$('results').append(link);message(`已完成 ${index+1} / ${count} 張。`);await yieldUI();
      }finally{if(result){result.canvas.width=1;result.canvas.height=1;}}
    }
    message(`已產生 ${count} 張 PNG，請點選右側或下方的下載連結。`);
  } catch(e){message(`${e.message||'處理失敗，請減少檔案大小後重試。'}${downloads.length?' 已完成的成果仍可下載。':''}`,true);}
  finally{if(action==='pdf'){$('password').value='';p.password='';}lock(false);}
};
selectTool(action);
