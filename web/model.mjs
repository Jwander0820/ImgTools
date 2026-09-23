export const LIMITS = Object.freeze({pixels:24_000_000,totalPixels:48_000_000,edge:16384,bytes:50*1024*1024,totalBytes:100*1024*1024});
export function checkSize(width,height) {
  if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>LIMITS.edge||height>LIMITS.edge||width*height>LIMITS.pixels)
    throw Error('圖片／成品尺寸過大：單邊最多 16,384 px，總像素最多 2,400 萬。請先縮小圖片或降低 DPI。');
}
export function validateFiles(files,action) {
  const max={stack:9,dialogue:12,watermark:12,pdf:1}[action];
  if(!max||files.length>max) throw Error(`此工具最多選擇 ${max||0} 個檔案。`);
  for(const f of files) {
    if(!(action==='pdf'?/\.pdf$/i:/\.(png|jpe?g|webp)$/i).test(f.name)) throw Error(action==='pdf'?'請選擇 PDF 檔案。':'請選擇 PNG、JPEG 或 WebP 圖片。');
    if(f.size>LIMITS.bytes) throw Error('每個檔案最多 50 MB。');
  }
  if(files.reduce((n,f)=>n+f.size,0)>LIMITS.totalBytes) throw Error('一次選取的檔案合計最多 100 MB。');
}
export function moveItem(items,index,delta) {
  const result=[...items], target=index+delta;
  if(target>=0&&target<items.length) [result[index],result[target]]=[result[target],result[index]];
  return result;
}
export function outputName(name,action) {
  return `${name.replace(/\.[^.]+$/,'').replace(/[<>:"/\\|?*\x00-\x1f]/g,'_')||'image'}-${action}.png`;
}
export function subtitleBand(height,ratio) {
  const cut=height*ratio;
  const rounded=cut%1===0.5?2*Math.round(cut/2):Math.round(cut);
  const top=Math.min(Math.max(rounded,1),height-1);
  return {top,height:height-top};
}
const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
export function watermarkLayout(width,height,textWidth,textHeight,p) {
  const angle=p.angle*Math.PI/180;
  const bw=Math.abs(textWidth*Math.cos(angle))+Math.abs(textHeight*Math.sin(angle));
  const bh=Math.abs(textWidth*Math.sin(angle))+Math.abs(textHeight*Math.cos(angle));
  let x=width/2,y=height/2;
  if(p.position==='custom') {
    if(!Number.isFinite(p.x)||!Number.isFinite(p.y))throw Error('請輸入有效的浮水印位置。');
    x=clamp(p.x,0,1)*width;y=clamp(p.y,0,1)*height;
  } else {
    if(!['center','top_left','top_right','bottom_left','bottom_right'].includes(p.position))throw Error('不支援的浮水印位置。');
    x=p.position.includes('left')?16+bw/2:p.position.includes('right')?width-16-bw/2:x;
    y=p.position.startsWith('top')?16+bh/2:p.position.startsWith('bottom')?height-16-bh/2:y;
  }
  return {x:bw>=width?width/2:clamp(x,bw/2,width-bw/2),y:bh>=height?height/2:clamp(y,bh/2,height-bh/2),width:bw,height:bh};
}
export function dragWatermark(start,dx,dy,rect) {
  return {x:clamp(start.x+dx/rect.width,0,1),y:clamp(start.y+dy/rect.height,0,1)};
}
export function resizeWatermark(size,startDistance,distance) {
  return clamp(Math.round(size*distance/Math.max(1,startDistance)),1,500);
}
export function rotateWatermark(angle,start,current) {
  if(Math.hypot(start.x,start.y)<1||Math.hypot(current.x,current.y)<1)return angle;
  const delta=(Math.atan2(current.y,current.x)-Math.atan2(start.y,start.x))*180/Math.PI;
  return ((Math.round(angle+delta)+180)%360+360)%360-180;
}
export function watermarkHandles(g,width,height) {
  const padx=Math.min(24,width/2),pady=Math.min(24,height/2);
  const point=(x,y)=>({x:clamp(x,padx,width-padx),y:clamp(y,pady,height-pady)});
  const move=point(g.x,g.y);
  let resize=point(g.x+g.width/2,g.y+g.height/2);
  if(Math.hypot(move.x-resize.x,move.y-resize.y)<56){
    const candidates=[point(move.x+56,resize.y),point(move.x-56,resize.y),point(resize.x,move.y+56),point(resize.x,move.y-56)];
    resize=candidates.reduce((best,p)=>Math.hypot(p.x-move.x,p.y-move.y)>Math.hypot(best.x-move.x,best.y-move.y)?p:best,resize);
  }
  let rotate=point(move.x,move.y-Math.max(56,g.height/2+32));
  const clearance=p=>Math.min(Math.hypot(p.x-move.x,p.y-move.y),Math.hypot(p.x-resize.x,p.y-resize.y));
  if(clearance(rotate)<56) {
    const candidates=[point(move.x-56,move.y),point(move.x+56,move.y),point(move.x,move.y+56),
      point(24,24),point(width-24,24),point(24,height-24),point(width-24,height-24)];
    rotate=candidates.find(p=>clearance(p)>=56)||candidates.reduce((best,p)=>clearance(p)>clearance(best)?p:best,rotate);
  }
  return {move,resize,rotate};
}
export function imagePlan(action,images,params) {
  if(!['stack','dialogue','watermark'].includes(action)) throw Error('不支援的工具。');
  const max=action==='stack'?9:12;
  if(images.length<(action==='watermark'?1:2)||images.length>max) throw Error(`請選擇 ${action==='watermark'?'1':'2'}～${max} 張圖片。`);
  for(const i of images)checkSize(i.width,i.height);
  if(images.reduce((n,i)=>n+i.width*i.height,0)>LIMITS.totalPixels) throw Error('來源圖片總像素最多 4,800 萬，請減少張數或縮小圖片。');
  const {width,height}=images[0];
  if(action==='watermark')return {width,height,parts:[{index:0,sx:0,sy:0,sw:width,sh:height,dx:0,dy:0}]};
  if(images.some(i=>i.width!==width))throw Error('請選擇同寬圖片。');
  let parts,outputHeight;
  if(action==='stack') {
    let y=0;
    parts=images.map((im,index)=>{const p={index,sx:0,sy:0,sw:width,sh:im.height,dx:0,dy:y}; y+=im.height;return p;});
    outputHeight=y;
  } else {
    if(images.some(i=>i.height!==height))throw Error('台詞疊圖需要同尺寸圖片。');
    const {ratio,spacing}=params;
    if(!Number.isFinite(ratio)||ratio<=0||ratio>=1||!Number.isInteger(spacing)||spacing<1)throw Error('請輸入有效的字幕帶起點與每句間距。');
    const {top,height:band}=subtitleBand(height,ratio);
    if(spacing>band)throw Error(`每句間距不可超過字幕帶高度 ${band} px。請降低間距或將起點上移。`);
    outputHeight=height+spacing*(images.length-1);
    parts=images.map((im,index)=>({index,sx:0,sy:index?top:0,sw:width,sh:index?band:height,dx:0,dy:index?top+spacing*index:0}));
  }
  checkSize(width,outputHeight);
  return {width,height:outputHeight,parts};
}
