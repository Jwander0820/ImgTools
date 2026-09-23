import {dragWatermark,resizeWatermark,rotateWatermark,watermarkHandles} from './model.mjs';

// Only the handles capture touch gestures; the rest of the image remains scrollable.
export function createWatermarkEditor({wrap,outline,move,resize,rotate,onChange}) {
  let view=null,gesture=null,enabled=true;
  function cancel() {
    if(!gesture)return;
    const {target,id}=gesture;gesture=null;
    if(target.hasPointerCapture(id))target.releasePointerCapture(id);
  }
  function update(result) {
    view=result?.watermark?result:null;
    for(const el of [outline,move,resize,rotate])el.hidden=!view;
    if(!view){cancel();return;}
    const {watermark:g,width:w,height:h}=view;
    outline.style.left=`${(g.x-g.width/2)/w*100}%`;
    outline.style.top=`${(g.y-g.height/2)/h*100}%`;
    outline.style.width=`${g.width/w*100}%`;
    outline.style.height=`${g.height/h*100}%`;
    const rect=wrap.getBoundingClientRect();
    const points=watermarkHandles({x:g.x/w*rect.width,y:g.y/h*rect.height,width:g.width/w*rect.width,height:g.height/h*rect.height},rect.width,rect.height);
    for(const [el,p] of [[move,points.move],[resize,points.resize],[rotate,points.rotate]]){
      el.style.left=`${p.x}px`;el.style.top=`${p.y}px`;
    }
  }
  for(const [target,mode] of [[move,'move'],[resize,'resize'],[rotate,'rotate']]) {
    target.addEventListener('pointerdown',event=>{
      if(!enabled||!view||gesture||event.button!==0||!event.isPrimary)return;
      event.preventDefault();
      const rect=wrap.getBoundingClientRect(),g=view.watermark;
      const cx=rect.left+g.x/view.width*rect.width,cy=rect.top+g.y/view.height*rect.height;
      gesture={target,mode,id:event.pointerId,rect,cx,cy,x:event.clientX,y:event.clientY,
        position:{x:g.x/view.width,y:g.y/view.height},size:g.size,angle:g.angle,
        distance:Math.hypot(event.clientX-cx,event.clientY-cy)};
      target.setPointerCapture(event.pointerId);
    });
    target.addEventListener('pointermove',event=>{
      if(!gesture||gesture.id!==event.pointerId)return;
      const g=gesture;
      if(g.mode==='move')onChange({position:'custom',...dragWatermark(g.position,event.clientX-g.x,event.clientY-g.y,g.rect)});
      else if(g.mode==='resize')onChange({fontSize:resizeWatermark(g.size,g.distance,Math.hypot(event.clientX-g.cx,event.clientY-g.cy))});
      else onChange({angle:rotateWatermark(g.angle,{x:g.x-g.cx,y:g.y-g.cy},{x:event.clientX-g.cx,y:event.clientY-g.cy})});
    });
    for(const name of ['pointerup','pointercancel','lostpointercapture'])target.addEventListener(name,event=>{if(gesture?.id===event.pointerId)cancel();});
    target.addEventListener('keydown',event=>{
      if(!enabled||!view||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-'].includes(event.key))return;
      event.preventDefault();const g=view.watermark;
      const sign=['ArrowLeft','ArrowUp','-'].includes(event.key)?-1:1;
      if(mode==='resize')onChange({fontSize:Math.min(500,Math.max(1,g.size+sign*(event.shiftKey?10:1)))});
      else if(mode==='rotate')onChange({angle:rotateWatermark(g.angle+sign*(event.shiftKey?10:1),{x:1,y:0},{x:1,y:0})});
      else if(event.key.startsWith('Arrow')) {
        const horizontal=['ArrowLeft','ArrowRight'].includes(event.key),step=sign*(event.shiftKey?0.1:0.01);
        onChange({position:'custom',...dragWatermark({x:g.x/view.width,y:g.y/view.height},horizontal?step:0,horizontal?0:step,{width:1,height:1})});
      }
    });
  }
  new ResizeObserver(()=>{if(view)update(view);}).observe(wrap);
  return {update,clear:()=>update(null),setEnabled(value){enabled=value;move.disabled=resize.disabled=rotate.disabled=!value;if(!value)cancel();}};
}
