// Run real app.js against a DOM substitute. This is not browser rendering.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
class Element {
  constructor(tag) { this.tag=tag; this.children=[]; this.dataset={}; this.listeners={}; this.value=''; this.textContent=''; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=nodes; }
  addEventListener(name, fn) { this.listeners[name]=fn; }
  setAttribute(name,value) { this[name]=value; }
  focus() {}
}
const visit = e => [e,...e.children.flatMap(visit)];
async function main() {
  const html = fs.readFileSync(path.join(root,'app/static/index.html'),'utf8');
  const ids = new Map([...html.matchAll(/<([a-z]+)\b[^>]*\bid="([^"]+)"/g)].map(m=>[m[2],new Element(m[1])]));
  const document = {getElementById(id) { assert(ids.has(id),id); return ids.get(id); }, createElement: tag=>new Element(tag),
    querySelectorAll: ()=>[...ids.values()].flatMap(visit).filter(e=>['button','select','input','textarea'].includes(e.tag))};
  const record={id:'rain-log',title:'빗물 관측 일지',content:'SERVER_FIXED_TEXT_831'};
  let branch={id:'public',revision:0,state:{trust:30,guard:20,expression:'차분',ended:false,events:{forced_attempts:0},
    config_version:'archive-2.0',config:{public_records:[record]},summary:'초기',
    progress:{catalog_seen:false,selected_record:null,read_records:[]},messages:[{role:'assistant',content:'첫 인사'}]}};
  let selected;
  const requests=[];
  const fetch=async(url,options)=>{
    let body;
    if(url==='/api/health') body={provider:'MockProvider',model:null,dev_mode:true};
    else if(url==='/api/branches') body=[{id:branch.id}];
    else if(url==='/api/branches/public') body=branch;
    else if(url.endsWith('/chat')) {
      const request=JSON.parse(options.body);requests.push(request);
      const n=requests.length;
      branch=structuredClone(branch);
      let result;
      if(n===1){ assert.equal(request.action,'list_records'); branch.state.progress.catalog_seen=true;result={message:'목록 확인',records:[{id:record.id,title:record.title}]}; }
      if(n===2){ assert.equal(request.action,'select_record');assert.equal(request.record_id,record.id);branch.state.progress.selected_record=record.id;result={message:'기록 선택',record:{id:record.id,title:record.title}}; }
      if(n===3){ assert.equal(request.action,'read_record');assert(!('record_id' in request));branch.state.progress.read_records=[record.id];result={message:'열람 성공',record}; }
      branch.state.messages.push({role:'user',content:request.text,action:request.action,checkpoint_id:`cp-${n}`},
        {role:'assistant',content:'모델 참고 대사',server_result:result});
      branch.revision++;
      if(n===2) selected=structuredClone(branch);
      body={...branch,debug:{committed:true,selected_action:request}};
    } else if(url.endsWith('/regress')){
      assert.equal(JSON.parse(options.body).turn_number,2); branch={...structuredClone(selected),id:'restored',revision:0};body=branch;
    } else throw new Error(url);
    return {ok:true,json:async()=>structuredClone(body)};
  };
  vm.runInNewContext(fs.readFileSync(path.join(root,'app/static/app.js'),'utf8'),{document,fetch,localStorage:{getItem:()=>null,setItem(){}}});
  await new Promise(setImmediate);
  ids.get('input-mode').value='direct'; ids.get('input-mode').listeners.change();
  const send=async action=>{
    ids.get('action').value=action; ids.get('action').listeners.change();
    ids.get('chat-form').listeners.submit({preventDefault(){}});
    await new Promise(setImmediate);
    assert.equal(ids.get('status').textContent,'');
  };
  await send('list_records');
  assert.equal(ids.get('record-choice').children[0].textContent,record.title);
  ids.get('action').value='select_record';ids.get('action').listeners.change();
  assert.equal(ids.get('record-choice').hidden,false);
  await send('select_record'); await send('read_record');
  assert(visit(ids.get('messages')).some(e=>e.textContent===record.content));
  assert.equal(ids.get('debug-panel').hidden,false);
  assert(ids.get('debug-content').textContent.includes('read_record'));
  const buttons=visit(ids.get('messages')).filter(e=>e.className==='jump-button');
  await buttons[1].listeners.click();
  assert(!visit(ids.get('messages')).some(e=>e.textContent===record.content));
  assert.equal(ids.get('debug-panel').hidden,true);
  assert.equal(ids.get('debug-content').textContent,'');
  assert.equal(requests.length,3);
  console.log('PASS: UI 공개 목록→선택→열람·서버 본문·개발 진단 표시·열람 전 회귀');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
