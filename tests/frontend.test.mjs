import {test} from 'node:test';
import assert from 'node:assert/strict';
import {describeResult} from '../imgtools/ui/static/result-model.mjs';
import {createTaskStore} from '../imgtools/ui/static/task-store.mjs';

test('rename dry-run is a preview with inspectable changes, never a success implying mutation', () => {
  const view=describeResult({ok:true,action:'rename.files_replace',outputs:{dry_run:true,changed:false,operations:[{source:'old.tif',destination:'new.tif'}],count:1}});
  assert.equal(view.kind,'rename');
  assert.equal(view.title,'預覽完成，尚未修改檔案');
  assert.equal(view.operations[0].destination,'new.tif');
});
test('metadata and conflicts remain available without opening JSON', () => {
  const metadata=describeResult({ok:true,outputs:{metadata:{256:'500',257:'600'}}});
  assert.deepEqual(metadata.metadata,[['256','500'],['257','600']]);
  const conflict=describeResult({ok:false,outputs:{conflicts:[{source:'a',destination:'b'}],operations:[]}});
  assert.equal(conflict.title,'發現名稱衝突，未套用變更');
  assert.equal(conflict.conflicts.length,1);
});
test('preview support covers output images across all tools and preserves partial cancelled outputs', () => {
  for (const action of ['watermark.text','merge.dialogue_stack','pdf.render_all_pages']) {
    const result=describeResult({ok:true,action,outputs:{files:['one.PNG','two.tif','three.mp4']}});
    assert.deepEqual(result.images,['one.PNG','two.tif']);
  }
  assert.equal(describeResult({ok:false,error_code:'CANCELLED',outputs:{files:['done.png']}}).title,'任務已取消');
});
test('switching tools cannot submit the same action twice while a job is active', async () => {
  const jobs=[];
  const store=createTaskStore({request:async(url,payload)=>{
    if (!payload) return {jobs};
    const job={id:String(jobs.length),action:payload.action,status:'queued'};
    jobs.unshift(job); return {job};
  }});
  await store.submit('pdf.render_page',{page:1});
  assert.equal(store.busy('pdf.render_page'),true);
  assert.equal(store.busy('tif.extract_page'),false);
  await assert.rejects(()=>store.submit('pdf.render_page',{page:1}));
  await store.submit('tif.extract_page',{});
  assert.equal(jobs.length,2);
});
test('uncertain submission retries the same id and payload', async () => {
  const requests=[];
  const store=createTaskStore({request:async(url,payload)=>{
    if (!payload) return {jobs:[]};
    requests.push(payload);
    if(requests.length===1) throw Error('connection lost');
    return {job:{id:'accepted',action:payload.action,status:'queued'}};
  }});
  await assert.rejects(()=>store.submit('pdf.render_page',{page:2}));
  assert.equal(store.snapshot().uncertain,true);
  await store.retrySubmission();
  assert.deepEqual(requests[0],requests[1]);
  assert.equal(store.snapshot().uncertain,false);
});
test('poll failure retains known jobs; terminal result is delivered once and keeps original action',async()=>{
  let fail=false,finished=false;
  const received=[];
  const store=createTaskStore({request:async()=>{
    if(fail)throw Error('offline');
    return {jobs:[{id:'pdf',action:'pdf.render_page',status:finished?'completed':'running',result:finished?{ok:true,action:'pdf.render_page'}:null}]};
  },onResult:job=>received.push(job)});
  await store.refresh(); fail=true;
  await assert.rejects(()=>store.refresh());
  assert.equal(store.busy('pdf.render_page'),true);
  fail=false;finished=true;
  await store.refresh();await store.refresh();
  assert.equal(store.busy('pdf.render_page'),false);
  assert.equal(received.length,1);
  assert.equal(received[0].result.action,'pdf.render_page');
});

test('compact summaries fetch a full result only when needed', async()=>{
  const requests=[];const received=[];
  const job={id:'1',action:'pdf.render_page',status:'completed',has_result:true};
  const store=createTaskStore({request:async url=>{
    requests.push(url);
    return url==='/api/jobs'?{jobs:[job],session_id:'server-1'}:{job:{...job,result:{ok:true,outputs:{files:['done.png']}}}};
  },onResult:item=>received.push(item)});
  await store.refresh();await store.refresh();
  assert.deepEqual(requests,['/api/jobs','/api/jobs/1','/api/jobs']);
  assert.equal(received[0].result.outputs.files[0],'done.png');
});

test('an old poll cannot clear a newly submitted job or allow a duplicate', async()=>{
  let resolvePoll;
  const store=createTaskStore({request:async(url,payload)=>{
    if (!payload) return new Promise(resolve=>{resolvePoll=resolve;});
    return {job:{id:'new',action:payload.action,status:'queued'}};
  }});
  const oldPoll=store.refresh();
  await store.submit('pdf.render_page',{});
  resolvePoll({jobs:[]});
  await oldPoll;
  assert.equal(store.busy('pdf.render_page'),true);
  await assert.rejects(()=>store.submit('pdf.render_page',{}));
});

test('overlapping polls keep the latest response and ignore a stale failure',async()=>{
  let rejectOld;
  let count=0;
  const store=createTaskStore({request:async()=>{
    if (++count===1) return new Promise((resolve,reject)=>{rejectOld=reject;});
    return {jobs:[{id:'current',action:'pdf.render_page',status:'running'}]};
  }});
  const first=store.refresh();
  await store.refresh();
  rejectOld(Error('stale failure'));
  await first;
  assert.equal(store.snapshot().error,'');
  assert.equal(store.busy('pdf.render_page'),true);
});
