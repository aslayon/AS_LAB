// Run with Node; this exercises real app.js against a DOM substitute, not a browser.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');

class Element {
  constructor(tag) {
    this.tag = tag; this.children = []; this.dataset = {}; this.listeners = {};
    this.value = ''; this.disabled = false; this.textContent = '';
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute(name, value) { this[name] = value; }
  focus() { this.focused = true; }
}

async function main() {
  const html = fs.readFileSync(path.join(root, 'app/static/index.html'), 'utf8');
  const ids = new Map([...html.matchAll(/<([a-z]+)\b[^>]*\bid="([^"]+)"/g)]
    .map(match => [match[2], new Element(match[1])]));
  assert(!ids.has('checkpoint-form'));
  const visit = el => [el, ...el.children.flatMap(visit)];
  const document = {
    getElementById(id) { assert(ids.has(id), `DOM ID missing: ${id}`); return ids.get(id); },
    createElement(tag) { return new Element(tag); },
    querySelectorAll() {
      return [...ids.values()].flatMap(visit).filter(el => ['button','select','input','textarea'].includes(el.tag));
    }
  };
  const messages = [{role: 'assistant', content: 'greeting'}];
  for (let n = 1; n <= 5; n++) {
    const message = {role:'user', content:`INPUT_${n}`, action:'speak'};
    // Older data can lack a pre-turn checkpoint. Regression uses the NEXT one.
    if (n !== 2) message.checkpoint_id = `cp-${n}`;
    messages.push(message, {role:'assistant', content:`REPLY_${n}`});
  }
  const secondState = {
    trust:30, guard:25, expression:'경계', events:{forced_attempts:0, ending:null},
    ended:false, config_version:'archive-1.0', summary:'second', messages:messages.slice(0,5)
  };
  const original = {
    id:'original', revision:5, state:{...secondState, ended:true, messages,
      events:{forced_attempts:2, ending:'expelled'}}
  };
  const restored = {id:'restored', parent_checkpoint_id:'cp-3', revision:0, state:secondState};
  let didRestore = false;
  const requests = [];
  const fetch = async (url, options) => {
    requests.push([url, options]);
    let body;
    if (url === '/api/health') body = {provider:'MockProvider', model:null};
    else if (url === '/api/branches') body = didRestore ? [original, restored] : [original];
    else if (url === '/api/branches/original') body = original;
    else if (url === '/api/branches/original/regress') {
      assert.equal(options.method, 'POST');
      assert.deepEqual(JSON.parse(options.body), {turn_number:2, revision:5});
      didRestore = true; body = restored;
    } else throw new Error(`Unexpected request: ${url}`);
    return {ok:true, json:async () => structuredClone(body)};
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, 'app/static/app.js'), 'utf8'), {
    document, fetch, localStorage:{getItem:() => 'original', setItem() {}}
  });
  await new Promise(setImmediate);
  const buttons = visit(ids.get('messages')).filter(el => el.className === 'jump-button');
  assert.equal(buttons.length, 5);
  assert.equal(buttons[0].disabled, true);
  assert.equal(buttons[1].disabled, false);
  assert.equal(ids.get('send').disabled, true);
  ids.get('input').value = 'unsent future draft';
  await buttons[1].listeners.click();
  const displayed = visit(ids.get('messages')).map(el => el.textContent);
  assert(displayed.includes('INPUT_1') && displayed.includes('REPLY_1'));
  assert(displayed.includes('INPUT_2') && displayed.includes('REPLY_2'));
  for (const n of [3,4,5]) {
    assert(!displayed.includes(`INPUT_${n}`));
    assert(!displayed.includes(`REPLY_${n}`));
  }
  assert.equal(ids.get('input').value, '');
  assert.equal(ids.get('action').value, 'speak');
  assert.equal(ids.get('send').disabled, false);
  assert.equal(ids.get('ending').hidden, true);
  assert(ids.get('branch-info').textContent.includes('대화 2회'));
  assert(!requests.some(([url]) => url.endsWith('/chat')));
  const restoredButtons = visit(ids.get('messages')).filter(el => el.className === 'jump-button');
  assert.equal(restoredButtons[0].disabled, true);
  console.log('PASS: UI 5→2 회귀 — 1·2 입력/답변 유지, 3·4·5 제거, 입력창 초기화, 재전송 없음');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
