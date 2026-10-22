const $ = id => document.getElementById(id);
let current = null;
let busy = false;
const actionLabels = {speak:'발언', list_records:'공개 목록 요청', select_record:'공개 기록 선택', read_record:'공개 기록 열람', request_access:'열람 요청', force_access:'강제 접근 시도', leave:'퇴장 시도'};

async function api(path, method='GET', data) {
  const response = await fetch(path, {method, headers: {'Content-Type':'application/json'}, ...(data === undefined ? {} : {body:JSON.stringify(data)})});
  const body = await response.json();
  if (!response.ok) {
    if (body.detail && body.detail.debug) showDebug(body.detail.debug);
    throw new Error(typeof body.detail === 'string' ? body.detail : (body.detail && body.detail.message) || '입력값을 확인해 주세요.');
  }
  return body.replayed ? api(`/api/branches/${body.id}`) : body;
}
function showDebug(debug) {
  $('debug-panel').hidden = !debug;
  let summary = '';
  if (debug?.relationship) {
    const r = debug.relationship;
    summary = `관계 판정 · ${r.version}\n변경 전: 신뢰 ${r.before.trust}, 경계 ${r.before.guard}\n`;
    for (const rule of r.rules) summary += `${rule.rule}: 신뢰 ${rule.trust_delta}, 경계 ${rule.guard_delta} · ${rule.applied ? '적용' : '반복 한도로 미적용'} · ${rule.reason}\n`;
    if (debug.committed === false) summary += '이번 턴은 저장되지 않았습니다. 아래 최종 수치는 계산값입니다.\n';
    summary += `합산: 신뢰 ${r.proposed_delta.trust_delta}, 경계 ${r.proposed_delta.guard_delta}\n최종: 신뢰 ${r.after.trust}, 경계 ${r.after.guard}\n출처 판정: ${r.source_reason}\n\n`;
  }
  $('debug-content').textContent = debug ? summary + JSON.stringify(debug, null, 2) : '';
}
function syncRecordControl() {
  const selecting = $('input-mode').value === 'direct' && $('action').value === 'select_record';
  $('record-label').hidden = !selecting;
  $('record-choice').hidden = !selecting;
}
function syncInputMode() {
  if (!$('input-mode').value) $('input-mode').value = 'free';
  const direct = $('input-mode').value === 'direct';
  $('action-label').hidden = !direct;
  $('action').hidden = !direct;
  $('input').placeholder = direct ? '선택식 행동은 문장 없이 보낼 수 있습니다.' : '서린에게 말을 걸거나 행동을 시도해 보세요.';
  syncRecordControl();
}
$('input-mode').addEventListener('change', syncInputMode);
$('action').addEventListener('change', syncRecordControl);
syncInputMode();
function controls() {
  document.querySelectorAll('button, select, input, textarea').forEach(el => el.disabled = busy || el.dataset.unavailable === 'true');
  if (!busy && (!current || current.state.ended)) ['input','action','input-mode','send'].forEach(id => $(id).disabled = true);
}
async function run(work) {
  if (busy) return;
  busy = true; showDebug(null); controls(); $('status').textContent = '처리 중…';
  try { await work(); $('status').textContent = ''; }
  catch (error) { $('status').textContent = error.message + ' 필요하면 선택한 분기를 다시 열어 주세요.'; }
  finally { busy = false; controls(); }
}
function node(tag, text, className) {
  const el = document.createElement(tag); el.textContent = text;
  if (className) el.className = className;
  return el;
}
function render(branch) {
  if (!current || current.id !== branch.id) {
    $('input').value = '';
    $('action').value = 'speak';
  }
  current = branch;
  try { localStorage.setItem('character-chat-branch', branch.id); } catch { /* Persistence is on the server. */ }
  showDebug(branch.debug);
  const state = branch.state;
  $('scene-location').textContent = state.config?.location || '기록 보관소';
  $('scene-environment').textContent = state.config?.environment || '';
  $('character-description').textContent = state.config?.core?.[0] || '신중하고 원칙적인 기록 보관인.';
  const progress = state.progress;
  $('progress-info').textContent = progress
    ? `공개 목록: ${progress.catalog_seen ? '확인함' : '미확인'} · 선택: ${progress.selected_record || '없음'} · 열람 ${progress.read_records.length}개`
    : '이전 설정의 분기입니다. 공개 기록을 진행하려면 새 게임을 시작하세요.';
  const records = progress && progress.catalog_seen ? state.config.public_records : [];
  $('record-choice').replaceChildren(...records.map(record => {
    const option = node('option', record.title); option.value = record.id; return option;
  }));
  $('record-choice').value = progress && progress.selected_record || (records[0] && records[0].id) || '';
  $('record-choice').dataset.unavailable = String(records.length === 0);
  syncRecordControl();
  $('generation-info').textContent = branch.generation ? `${branch.generation.model} · 응답 ${(branch.generation.elapsed_ms / 1000).toFixed(2)}초` : '';
  $('expression').textContent = state.expression;
  for (const key of ['trust','guard']) { $(key).value = state[key]; $(key+'-value').textContent = state[key]; }
  $('summary').textContent = state.summary;
  $('events').textContent = `기록: 봉인됨 · 강제 접근 ${state.events.forced_attempts}회`;
  $('version').textContent = `설정 ${state.config_version}`;
  $('branch-info').textContent = `분기 ${branch.id.slice(0,8)} · 대화 ${state.messages.filter(message => message.role === 'user').length}회`;
  $('messages').replaceChildren(...state.messages.map((message, index) => {
    const box = node('article','',`message ${message.role}`);
    const heading = node('div','','message-heading');
    heading.append(node('small', message.role === 'user' ? (message.input_mode === 'free' ? '당신 · 자유 입력' : `당신 · ${actionLabels[message.action] || '발언'}`) : `서린 · ${message.expression || '차분'}`));
    if (message.role === 'user') {
      const turnNumber = Math.floor(index / 2) + 1;
      const nextMessage = state.messages[index + 2];
      const available = !nextMessage || Boolean(nextMessage.checkpoint_id);
      const jump = node('button','↶ 여기로 회귀','jump-button');
      jump.type = 'button';
      jump.title = available ? '이 발언과 답변까지 남기고 이후 대화·상태를 되돌립니다. 원래 분기는 보존됩니다.' : '이 대화가 끝난 시점의 상태가 저장되지 않아 돌아갈 수 없습니다.';
      jump.setAttribute('aria-label', `${turnNumber}번째 대화까지 남기고 회귀`);
      jump.dataset.unavailable = String(!available);
      jump.disabled = busy || !available;
      if (available) jump.addEventListener('click', () => jumpToMessage(turnNumber));
      heading.append(jump);
    }
    box.append(heading);
    if (message.server_result && (message.server_result.outcome !== 'conversation' || message.server_result.interaction_kind || message.server_result.source_check)) {
      const result = message.server_result;
      const facts = node('div', '', 'server-result');
      facts.append(node('strong', '서버 확정 결과'), node('p', result.message));
      if (result.next_step) facts.append(node('p', result.next_step));
      if (result.source_check && result.outcome !== 'conversation') facts.append(node('p', result.source_check.message));
      for (const record of result.records || []) facts.append(node('p', record.title));
      if (result.record) {
        facts.append(node('strong', result.record.title));
        if (result.record.content) facts.append(node('p', result.record.content));
      }
      box.append(facts);
    }
    box.append(node('p',message.content));
    return box;
  }));
  $('messages').scrollTop = $('messages').scrollHeight;
  $('ending').hidden = !state.ended;
  $('ending').textContent = state.events.ending === 'enlightenment_read'
    ? `${state.ending.title}\n\n${state.ending.body}`
    : state.events.ending === 'expelled' ? '반복된 강제 접근으로 면담이 종료됐습니다. 발언 옆 버튼으로 이전 시점에서 다시 시작할 수 있습니다.' : '보관소를 떠났습니다. 발언 옆 버튼으로 이전 시점에서 다시 시작할 수 있습니다.';
  const trial = state.access_trial;
  $('trial-info').textContent = branch.pending_request ? '판정값이 예약되어 있습니다. 같은 요청을 재전송해 완료하거나 판정 전으로 회귀하세요.'
    : trial ? `제한 열람 판정: ${trial.status === 'untried' ? '미사용' : trial.status === 'granted' ? '성공 · 열람 완료' : '실패 · 이 분기 재추첨 없음'}` : '이전 설정: 봉인 열람 예외가 없는 분기입니다.';
  $('retry-trial').hidden = !branch.pending_request;
  $('export-panel').hidden = !(branch.exports && branch.exports.length);
  $('export-status').textContent = branch.export_warning || 'DB에 보존된 판정 기록입니다. 파일 저장이 실패해도 다운로드할 수 있습니다.';
  $('export-links').replaceChildren(...(branch.exports || []).map(report => {
    const box = node('p', `${report.kind === 'success' ? '성공' : '실험'} · ${report.status === 'ready' ? report.directory : '파일 저장 대기/실패 · 다시 내보내기 가능'} `);
    const json = node('a', 'JSON 다운로드'); json.href = report.json_url;
    const md = node('a', 'Markdown 다운로드'); md.href = report.markdown_url;
    box.append(json, node('span', ' · '), md); return box;
  }));
}
async function jumpToMessage(turnNumber) {
  await run(async () => {
    render(await api(`/api/branches/${current.id}/regress`,'POST',{turn_number:turnNumber, revision:current.revision}));
    await refreshLists();
  });
  if (!busy && current && !current.state.ended) $('input').focus();
}
async function refreshLists() {
  const branches = await api('/api/branches');
  $('branches').replaceChildren(...branches.map(branch => {
    const option = node('option', `${branch.id.slice(0,8)} · ${branch.parent_checkpoint_id ? '회귀·복원' : '시작'}`);
    option.value = branch.id; option.selected = branch.id === current.id; return option;
  }));
}
$('retry-export').addEventListener('click', () => run(async () => { render(await api(`/api/branches/${current.id}/exports/retry`, 'POST')); }));
$('retry-trial').addEventListener('click', () => run(async () => { render(await api(`/api/branches/${current.id}/chat`, 'POST', current.pending_request)); }));
$('new-game').addEventListener('click', () => run(async () => { render(await api('/api/games','POST')); $('input').value = ''; await refreshLists(); }));
$('load-branch').addEventListener('click', () => run(async () => { render(await api(`/api/branches/${$('branches').value}`)); await refreshLists(); }));
$('chat-form').addEventListener('submit', event => {
  event.preventDefault(); if (!current || current.state.ended) return;
  const action = $('action').value;
  const mode = $('input-mode').value || 'free';
  const text = $('input').value.trim() || (mode === 'direct' && action !== 'speak' ? actionLabels[action] : '');
  if (!text) return;
  const request = {text, mode, revision:current.revision};
  if (mode === 'direct') request.action = action;
  if (mode === 'direct' && action === 'select_record') {
    if (!$('record-choice').value) { $('status').textContent = '먼저 공개 기록 목록을 요청하세요.'; return; }
    request.record_id = $('record-choice').value;
  }
  run(async () => {
    render(await api(`/api/branches/${current.id}/chat`,'POST',request));
    $('input').value = ''; await refreshLists();
  });
});
run(async () => {
  const health = await api('/api/health');
  $('provider-info').textContent = health.model ? `Ollama · ${health.model}` : '모의 응답';
  let saved; try { saved = localStorage.getItem('character-chat-branch'); } catch {}
  if (saved) {
    // Recover an absent branch (e.g. a newly selected database), but surface network errors.
    const branches = await api('/api/branches');
    if (branches.some(branch => branch.id === saved)) render(await api(`/api/branches/${saved}`));
  }
  if (!current) {
    const branches = await api('/api/branches');
    render(branches.length ? await api(`/api/branches/${branches[0].id}`) : await api('/api/games','POST'));
  }
  await refreshLists();
});
