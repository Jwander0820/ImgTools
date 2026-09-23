import {imagePlan,checkSize,watermarkLayout} from './model.mjs';
export const yieldUI = () => globalThis.scheduler?.yield ? globalThis.scheduler.yield() : new Promise(r=>setTimeout(r,0));
export function canvasOf(width,height) {
  checkSize(width,height);
  const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
  if(!canvas.getContext('2d'))throw Error('瀏覽器無法建立畫布，請減少圖片尺寸或關閉其他分頁。');
  return canvas;
}
export async function renderImages(action,images,params,{preview=false}={}) {
  const plan=imagePlan(action,images,params);
  const scale=preview?Math.min(1,1000/plan.width,1800/plan.height):1;
  const canvas=canvasOf(Math.max(1,Math.round(plan.width*scale)),Math.max(1,Math.round(plan.height*scale)));
  const ctx=canvas.getContext('2d');ctx.scale(scale,scale);
  for(const p of plan.parts) {
    // Pillow paste replaces transparent pixels, rather than alpha blending them.
    ctx.clearRect(p.dx,p.dy,p.sw,p.sh);
    ctx.drawImage(images[p.index],p.sx,p.sy,p.sw,p.sh,p.dx,p.dy,p.sw,p.sh);
  }
  const watermark=action==='watermark'?await drawWatermark(ctx,plan.width,plan.height,params):null;
  return {canvas,width:plan.width,height:plan.height,watermark};
}
async function drawWatermark(ctx,width,height,p) {
  if(!p.text?.trim()||p.text.length>200)throw Error('請輸入 1～200 字的浮水印。');
  if(!Number.isFinite(p.fontSize)||p.fontSize<0||p.fontSize>500||!Number.isFinite(p.angle)||Math.abs(p.angle)>180||!Number.isFinite(p.opacity)||p.opacity<0||p.opacity>1)throw Error('請檢查浮水印字級、角度與不透明度。');
  const size=p.fontSize||Math.min(500,Math.max(12,Math.round(width/24)));
  ctx.font=`600 ${size}px "Microsoft JhengHei", "PingFang TC", sans-serif`;
  ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=p.color;ctx.globalAlpha=p.opacity;
  const angle=p.angle*Math.PI/180;
  const tw=ctx.measureText(p.text).width,th=size*1.5;
  const layout=watermarkLayout(width,height,tw,th,p);
  const {width:bw,height:bh}=layout;
  const paint=(x,y)=>{ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.fillText(p.text,0,0);ctx.restore();};
  if(p.repeat) {
    const dx=Math.max(bw+60,80),dy=Math.max(bh+60,80);
    for(let y=dy/2;y<height+dy/2;y+=dy){for(let x=dx/2;x<width+dx/2;x+=dx)paint(x,y);await yieldUI();}
  } else {
    paint(layout.x,layout.y);
  }
  ctx.globalAlpha=1;
  return p.repeat?null:{...layout,size,angle:p.angle};
}
export const pngBlob = canvas => new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(Error('無法輸出圖片，請降低尺寸後重試。')),'image/png'));
