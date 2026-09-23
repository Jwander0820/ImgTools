import {canvasOf} from './render.mjs';
export async function renderPdf(file,{page,dpi,password}) {
  if(!Number.isInteger(page)||page<1||!Number.isInteger(dpi)||dpi<36||dpi>600)throw Error('頁碼須為正整數，DPI 須介於 36～600。');
  const pdfjs=await import('./vendor/pdf.mjs');
  pdfjs.GlobalWorkerOptions.workerSrc=new URL('./vendor/pdf.worker.mjs',import.meta.url).href;
  const loading=pdfjs.getDocument({data:new Uint8Array(await file.arrayBuffer()),password,
    cMapUrl:new URL('./vendor/cmaps/',import.meta.url).href,cMapPacked:true,
    standardFontDataUrl:new URL('./vendor/standard_fonts/',import.meta.url).href,
    wasmUrl:new URL('./vendor/wasm/',import.meta.url).href,
    isEvalSupported:false,enableXfa:false});
  let canvas;
  try {
    const doc=await loading.promise;
    if(page>doc.numPages)throw Error(`此 PDF 只有 ${doc.numPages} 頁，請調整頁碼。`);
    const pdfPage=await doc.getPage(page),viewport=pdfPage.getViewport({scale:dpi/72});
    canvas=canvasOf(Math.ceil(viewport.width),Math.ceil(viewport.height));
    await pdfPage.render({canvasContext:canvas.getContext('2d'),viewport,background:'rgb(255,255,255)'}).promise;
    return {canvas,width:canvas.width,height:canvas.height};
  } catch(e) {
    if(canvas){canvas.width=1;canvas.height=1;}
    if(e.name==='PasswordException')throw Error('PDF 需要密碼，或密碼不正確。請輸入後重試。');
    throw e;
  } finally {await loading.destroy();}
}
