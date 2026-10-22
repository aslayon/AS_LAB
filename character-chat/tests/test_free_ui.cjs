// Exercise real app.js; this is a DOM substitute, not browser rendering.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm'), assert=require('node:assert/strict');
const root=path.join(__dirname,'..');
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.listeners={};this.value='';this.textContent='';}
 append(...items){this.children.push(...items);} replaceChildren(...items){this.children=items;}
 addEventListener(name,fn){this.listeners[name]=fn;} setAttribute(name,value){this[name]=value;} focus(){}
}
const visit=e=>[e,...e.children.flatMap(visit)];
async function main(){
 const html=fs.readFileSync(path.join(root,'app/static/index.html'),'utf8');
 const ids=new Map([...html.matchAll(/<([a-z]+)\b[^>]*\bid="([^"]+)"/g)].map(m=>[m[2],new Element(m[1])]));
 const document={getElementById(id){assert(ids.has(id),id);return ids.get(id);},createElement:tag=>new Element(tag),
 querySelectorAll:()=>[...ids.values()].flatMap(visit).filter(e=>['button','select','input','textarea'].includes(e.tag))};
 let branch={id:'free',revision:0,state:{trust:30,guard:20,expression:'차분',ended:false,events:{forced_attempts:0},summary:'초기',config_version:'archive-2.0',config:{public_records:[{id:'rain-log',title:'빗물 관측 일지',content:'고정 본문'}]},progress:{catalog_seen:false,selected_record:null,read_records:[]},messages:[{role:'assistant',content:'첫 인사'}]}};
 const requests=[];
 const fetch=async(url,options)=>{
  let body;
  if(url==='/api/health')body={provider:'OllamaProvider',model:'test-model'};
  else if(url==='/api/branches')body=[{id:branch.id}];
  else if(url==='/api/branches/free')body=branch;
  else if(url.endsWith('/chat')){
   const input=JSON.parse(options.body); requests.push(input);
   assert.equal(input.mode,'free'); assert(!('action' in input)); assert(!('record_id' in input));
   branch=structuredClone(branch); const first=requests.length===1;
   const source=requests.length===3;
   const result=source?{outcome:'conversation',message:'이름 언급 확인',next_step:'그 이름은 어디서 들으셨습니까?',source_check:{act:'ask_source',message:'그 이름은 어디서 들으셨습니까?'}}:first?{outcome:'conversation',message:'발언 접수'}:{outcome:'catalog_listed',message:'목록 확인',records:[{id:'rain-log',title:'빗물 관측 일지'}]};
   if(!first)branch.state.progress.catalog_seen=true;
   branch.state.messages.push({role:'user',content:input.text,action:first?'speak':'list_records',input_mode:'free',checkpoint_id:'cp'}, {role:'assistant',content:first?'비가 많이 오네요.':'공개 목록입니다.',server_result:result});
   branch.revision++; body=branch;
   if(source) body={...branch,debug:{relationship:{version:'relationship-1.0',before:{trust:30,guard:20},after:{trust:30,guard:30},proposed_delta:{trust_delta:0,guard_delta:10},source_reason:'제목 최초 언급',rules:[{rule:'secret_first_mention',trust_delta:0,guard_delta:10,applied:true,reason:'정확한 제목 최초 언급'}]}}};
  } else throw new Error(url);
  return {ok:true,json:async()=>structuredClone(body)};
 };
 const sandbox={document,fetch,localStorage:{getItem:()=>null,setItem(){}}};
 vm.runInNewContext(fs.readFileSync(path.join(root,'app/static/app.js'),'utf8'),sandbox);
 await new Promise(setImmediate);
 assert.equal(ids.get('input-mode').value,'free'); assert.equal(ids.get('action').hidden,true);
 ids.get('input').value='안녕하세요.'; ids.get('chat-form').listeners.submit({preventDefault(){}});
 await new Promise(setImmediate);
 assert.equal(requests[0].text,'안녕하세요.');
 assert.equal(visit(ids.get('messages')).filter(e=>e.className==='server-result').length,0);
 ids.get('input').value='공개 기록 목록을 보여주세요.'; ids.get('chat-form').listeners.submit({preventDefault(){}});
 await new Promise(setImmediate);
 assert.equal(visit(ids.get('messages')).filter(e=>e.className==='server-result').length,1);
 assert(visit(ids.get('messages')).some(e=>e.textContent==='당신 · 자유 입력'));
 ids.get('input').value='계몽의 서'; ids.get('chat-form').listeners.submit({preventDefault(){}});
 await new Promise(setImmediate);
 assert.equal(visit(ids.get('messages')).filter(e=>e.className==='server-result').length,2);
 assert(visit(ids.get('messages')).some(e=>e.textContent==='그 이름은 어디서 들으셨습니까?'));
 assert(ids.get('debug-content').textContent.includes('변경 전: 신뢰 30, 경계 20'));
 assert(ids.get('debug-content').textContent.includes('최종: 신뢰 30, 경계 30'));
 assert(ids.get('debug-content').textContent.includes('secret_first_mention'));
 ids.get('input-mode').value='direct';ids.get('input-mode').listeners.change();
 assert.equal(ids.get('action').hidden,false);
 ids.get('action').value='select_record';ids.get('action').listeners.change();
 assert.equal(ids.get('record-choice').hidden,false);
 const completed=structuredClone(branch);
 completed.state.ended=true;completed.state.events.ending='enlightenment_read';
 completed.state.ending={title:'계몽의 서',body:'고정 결말 본문 <script>문자 그대로</script>'};
 completed.state.access_trial={status:'granted'};
 completed.exports=[{id:'report',kind:'success',status:'ready',directory:'/tmp/example-export',json_url:'/api/exports/report/json',markdown_url:'/api/exports/report/markdown'}];
 sandbox.render(completed);sandbox.controls();
 assert(ids.get('ending').textContent.includes(completed.state.ending.body));
 assert.equal(ids.get('export-panel').hidden,false);
 assert(visit(ids.get('export-links')).some(e=>e.href==='/api/exports/report/json'));
 assert(visit(ids.get('export-links')).some(e=>e.textContent.includes('/tmp/example-export')));
 assert.equal(ids.get('send').disabled,true);
 assert.equal(ids.get('retry-export').disabled,false);
 const pending=structuredClone(branch);pending.pending_request={text:'같은 요청',mode:'free',revision:pending.revision};
 sandbox.render(pending);assert.equal(ids.get('retry-trial').hidden,false);
 console.log('PASS: 자유 입력 기본·실행 필드 미전송·일반 접수 카드 숨김·출처 질문 카드·관계 판정 개발 요약·개발용 선택 유지·고정 결말/저장 위치/다운로드/재내보내기·보류 재전송 표시');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
