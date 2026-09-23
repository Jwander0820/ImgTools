import {mkdir, copyFile, cp} from 'node:fs/promises';
const root = new URL('./', import.meta.url);
const dest = new URL('./dist/', root);
await mkdir(new URL('vendor/', dest), {recursive:true});
for (const name of ['index.html','app.css','app.mjs','model.mjs','render.mjs','pdf.mjs','fields.mjs','watermark-editor.mjs']) {
  await copyFile(new URL(name,root),new URL(name,dest));
}
const pdf = new URL('node_modules/pdfjs-dist/',root);
for (const name of ['pdf.mjs','pdf.worker.mjs']) {
  await copyFile(new URL(`build/${name}`,pdf),new URL(`vendor/${name}`,dest));
}
for (const name of ['cmaps','standard_fonts','wasm']) {
  await cp(new URL(name,pdf),new URL(`vendor/${name}`,dest),{recursive:true});
}
await copyFile(new URL('LICENSE',pdf),new URL('vendor/PDFJS-LICENSE',dest));
console.log('Static site ready: web/dist (no Python or Node server required in production)');
