import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve, extname, sep} from 'node:path';
const root = fileURLToPath(new URL('./dist/',import.meta.url));
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.mjs':'text/javascript','.svg':'image/svg+xml','.wasm':'application/wasm','.bcmap':'application/octet-stream'};
const server=createServer(async(req,res)=>{
  try {
    if(req.method!=='GET' && req.method!=='HEAD'){res.writeHead(405).end();return;}
    const path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=resolve(root,`.${path==='/'?'/index.html':path}`);
    if(!file.startsWith(root.endsWith(sep)?root:root+sep)){res.writeHead(403).end();return;}
    const body=await readFile(file);
    res.writeHead(200,{'Content-Type':types[extname(file)]||'application/octet-stream','Cache-Control':'no-store'});
    res.end(req.method==='HEAD'?undefined:body);
  } catch {res.writeHead(404).end('Not found');}
});
server.listen(Number(process.env.PORT||5859),'127.0.0.1',()=>console.log(`Preview: http://127.0.0.1:${server.address().port}`));
