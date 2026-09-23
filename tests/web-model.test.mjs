import test from 'node:test';
import assert from 'node:assert/strict';
import {imagePlan, moveItem, outputName, validateFiles, subtitleBand, watermarkLayout, dragWatermark, resizeWatermark, rotateWatermark, watermarkHandles} from '../web/model.mjs';

test('直向疊圖維持順序與原始尺寸', () => {
  const p = imagePlan('stack', [{width:100,height:80},{width:100,height:60}], {});
  assert.deepEqual([p.width,p.height], [100,140]);
  assert.equal(p.parts[1].dy, 80);
  assert.throws(() => imagePlan('stack', [{width:100,height:80},{width:90,height:60}], {}), /同寬/);
});
test('字幕帶依本機規則覆蓋，保留第一張完整畫面', () => {
  const p = imagePlan('dialogue', Array(3).fill({width:1920,height:1080}), {ratio:0.88,spacing:85});
  assert.deepEqual([p.width,p.height], [1920,1250]);
  assert.equal(p.parts[0].sh,1080);
  assert.deepEqual(p.parts.slice(1).map(x=>[x.sy,x.dy,x.sh]), [[950,1035,130],[950,1120,130]]);
  assert.throws(() => imagePlan('dialogue', Array(2).fill({width:100,height:100}), {ratio:0.9,spacing:20}), /字幕帶/);
});
test('拒絕錯誤尺寸與過大輸出', () => {
  assert.throws(() => imagePlan('stack', Array(2).fill({width:8000,height:8000}), {}), /像素|尺寸/);
  assert.throws(() => imagePlan('dialogue', Array(2).fill({width:100,height:100}), {ratio:NaN,spacing:1}));
  assert.throws(() => imagePlan('missing', [{width:10,height:10}], {}));
});
test('字幕帶半像素邊界與 Python 的偶數捨入一致', () => {
  const p = imagePlan('dialogue', Array(2).fill({width:100,height:100}), {ratio:0.885,spacing:10});
  assert.equal(p.parts[1].sy,88);
  assert.equal(p.parts[1].sh,12);
});
test('排序不修改原陣列，來源名稱安全且可辨認', () => {
  const original=['a','b','c'];
  assert.deepEqual(moveItem(original,2,-1), ['a','c','b']);
  assert.deepEqual(original,['a','b','c']);
  assert.deepEqual(moveItem(original,0,-1), original);
  assert.equal(outputName('畫面.jpeg','stack'), '畫面-stack.png');
});
test('檔案限制在解碼之前檢查', () => {
  assert.throws(() => validateFiles([{name:'a.svg',size:1}], 'stack'), /PNG/);
  assert.throws(() => validateFiles([{name:'a.png',size:100*1024*1024}], 'stack'), /MB/);
  assert.doesNotThrow(() => validateFiles([{name:'test.pdf',size:100}], 'pdf'));
  assert.throws(() => validateFiles(Array(2).fill({name:'test.pdf',size:100}), 'pdf'));
});
test('字幕帶尺寸供滑桿與輸出共用，半像素規則一致', () => {
  assert.deepEqual(subtitleBand(100,0.885),{top:88,height:12});
  assert.deepEqual(subtitleBand(720,0.88),{top:634,height:86});
});
test('浮水印自訂位置以比例套用各尺寸圖片並保留字框在畫面內', () => {
  const p={position:'custom',x:0.25,y:0.75,angle:0};
  const a=watermarkLayout(1000,800,200,40,p);
  assert.deepEqual([a.x,a.y,a.width,a.height],[250,600,200,40]);
  const b=watermarkLayout(2000,1600,200,40,p);
  assert.deepEqual([b.x,b.y],[500,1200]);
  const edge=watermarkLayout(1000,800,200,40,{...p,x:0,y:1});
  assert.deepEqual([edge.x,edge.y],[100,780]);
  assert.throws(()=>watermarkLayout(1000,800,200,40,{...p,x:NaN}));
});
test('拖曳以顯示尺寸換算比例，超出畫面也能夾限', () => {
  assert.deepEqual(dragWatermark({x:0.5,y:0.5},50,-25,{width:200,height:100}),{x:0.75,y:0.25});
  assert.deepEqual(dragWatermark({x:0.5,y:0.5},999,-999,{width:200,height:100}),{x:1,y:0});
});
test('縮放依與中心的距離比例，限制字級範圍', () => {
  assert.equal(resizeWatermark(40,100,150),60);
  assert.equal(resizeWatermark(40,100,0),1);
  assert.equal(resizeWatermark(400,100,1000),500);
});
test('窄螢幕的小字浮水印仍保留分開的觸控控制點', () => {
  const points=watermarkHandles({x:150,y:100,width:10,height:10},300,225);
  assert.ok(Math.hypot(points.move.x-points.resize.x,points.move.y-points.resize.y)>=56);
  for(const p of Object.values(points)){assert.ok(p.x>=24&&p.x<=276);assert.ok(p.y>=24&&p.y<=201);}
});

test('旋轉依指標繞中心的角度，跨越正負 180 度保持連續方向', () => {
  assert.equal(rotateWatermark(30,{x:100,y:0},{x:0,y:100}),120);
  assert.equal(rotateWatermark(170,{x:100,y:0},{x:0,y:100}),-100);
  const vector=degrees=>({x:100*Math.cos(degrees*Math.PI/180),y:100*Math.sin(degrees*Math.PI/180)});
  assert.equal(rotateWatermark(20,vector(179),vector(-179)),22);
  assert.equal(rotateWatermark(20,vector(-179),vector(179)),18);
  assert.equal(rotateWatermark(40,{x:100,y:0},{x:0,y:0}),40);
});

test('旋轉控制點在手機四角與小字模式不遮住移動或縮放', () => {
  for(const [x,y] of [[125,94],[0,0],[250,0],[0,188],[250,188]]) {
    const points=watermarkHandles({x,y,width:10,height:10},250,188);
    assert.ok(points.rotate);
    const all=Object.values(points);
    for(let i=0;i<all.length;i++) {
      assert.ok(all[i].x>=24&&all[i].x<=226&&all[i].y>=24&&all[i].y<=164);
      for(let j=i+1;j<all.length;j++)assert.ok(Math.hypot(all[i].x-all[j].x,all[i].y-all[j].y)>=56);
    }
  }
});
