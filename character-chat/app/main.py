import json
import os
import sqlite3
from copy import deepcopy
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .domain import Proposal, Turn, apply_turn, initial_state, resolve
from .intent import Decision, ground_intent, intent_context
from .dialogue_review import grounded_reply, required_reply_reason, validate_review
from .providers import GenerationResult, MockProvider, ProviderError, build_context, make_provider
from .settings import Settings
from .store import Store, encode, new_id
from .relationship import load_rules, relationship_plan
from .world import load_world
from .approach import approach_diagnostic
from .access import load_ending, private_settings, copy_private_settings, request_hash, eligibility, reserve, apply_decision, now
from .exports import Exporter, code_version, queue_report, markdown

ROOT = Path(__file__).resolve().parent


class CheckpointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    label: str = Field(min_length=1, max_length=80)
    revision: int = Field(ge=0)


class RegressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    turn_number: int = Field(ge=1)
    revision: int = Field(ge=0)


def create_app(db_path=None, provider=None, settings=None, relationship_rules_path=None, world_path=None,
               ending_path=None, export_dir=None, seed_factory=None):
    tuning = load_rules(relationship_rules_path)
    world = load_world(world_path)
    ending = load_ending(ending_path or ROOT.parent/'config'/'ending.json')
    if tuning.get('access_policy') and tuning['access_policy']['minimum_public_reads']>len(world['public_records']):
        rules_path=Path(relationship_rules_path or ROOT.parent/'config'/'relationship_rules.json').resolve()
        raise ValueError(f'관계 규칙 설정 오류 ({rules_path}), access_policy.minimum_public_reads: 공개 기록 수보다 큽니다')
    app = FastAPI(title="기록 보관소 · Character Chat")
    store = Store(db_path or os.getenv("CHARACTER_CHAT_DB", str(ROOT.parent / "data" / "game.sqlite3")))
    settings = settings or Settings.from_env()
    app.state.provider = provider if provider is not None else make_provider(settings)
    exporter=Exporter(store,export_dir or Path(store.path).parent/'exports')
    app.state.exporter=exporter
    code=code_version()
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    def branch(db, branch_id):
        row = db.execute("SELECT * FROM branches WHERE id=?", (branch_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "분기를 찾을 수 없습니다.")
        return row

    def check_revision(row, revision):
        if row["revision"] != revision:
            raise HTTPException(409, "다른 요청이 상태를 변경했습니다. 분기를 다시 불러오세요.")

    def model_info():
        return {'provider':type(app.state.provider).__name__,'model':getattr(app.state.provider,'model',None)}

    def decorated(view, publish=False, force_export=False):
        if publish:
            try:
                exporter.publish(view['id'],force=force_export)
            except (OSError,sqlite3.Error):
                view['export_warning']='게임 결과는 DB에 저장됐습니다. 파일은 다시 내보내기할 수 있습니다.'
        try:
            reports=exporter.metadata(view['id'])
            if reports:
                view['exports']=reports
            with store.connect() as db:
                pending=db.execute("SELECT request_json FROM access_attempts WHERE branch_id=? AND status='reserved'",(view['id'],)).fetchone()
                if pending:
                    view['pending_request']=json.loads(pending['request_json'])
        except sqlite3.Error:
            view['export_warning']='내보내기 상태를 다시 조회하세요. 게임 결과는 유지됩니다.'
        return view

    @app.get("/")
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "provider": type(app.state.provider).__name__,
                "model": getattr(app.state.provider, "model", None)} | ({"dev_mode": True} if settings.dev_mode else {})

    @app.post("/api/games", status_code=201)
    def new_game():
        bid, gid = new_id(), new_id()
        with store.connect(write=True) as db:
            state=initial_state(tuning, world)
            db.execute("INSERT INTO branches(id, game_id, snapshot) VALUES(?,?,?)", (bid, gid, encode(state)))
            if 'access_trial' in state:
                private_settings(db,bid,ending,seed_factory)
            return store.view(branch(db, bid))

    @app.get("/api/branches")
    def branches():
        with store.connect() as db:
            return [dict(row) for row in db.execute("SELECT id, game_id, parent_checkpoint_id, revision, created_at FROM branches ORDER BY created_at DESC, rowid DESC")]

    @app.get("/api/branches/{branch_id}")
    def get_branch(branch_id: str):
        with store.connect() as db:
            view=store.view(branch(db, branch_id))
        return decorated(view)

    @app.post('/api/branches/{branch_id}/exports/retry')
    def retry_exports(branch_id: str):
        with store.connect() as db:
            view=store.view(branch(db,branch_id))
        return decorated(view,publish=True,force_export=True)

    @app.get('/api/exports/{export_id}/{format}')
    def download_report(export_id: str, format: str):
        if format not in ('json','markdown'):
            raise HTTPException(404,'지원하지 않는 형식입니다.')
        with store.connect() as db:
            row=db.execute('SELECT payload FROM exports WHERE id=?',(export_id,)).fetchone()
        if row is None:
            raise HTTPException(404,'기록을 찾을 수 없습니다.')
        payload=json.loads(row['payload'])
        content=json.dumps(payload,ensure_ascii=False,indent=2)+'\n' if format=='json' else markdown(payload)
        suffix='json' if format=='json' else 'md'
        return Response(content,media_type='application/json' if format=='json' else 'text/markdown',
                        headers={'Content-Disposition':f'attachment; filename="{export_id}.{suffix}"'})

    @app.post("/api/branches/{branch_id}/chat")
    def chat(branch_id: str, turn: Turn):
        if not turn.text.strip():
            raise HTTPException(422, "빈 입력은 보낼 수 없습니다.")
        with store.connect() as db:
            row = branch(db, branch_id)
            state = json.loads(row["snapshot"])
            existing=db.execute('SELECT * FROM access_attempts WHERE branch_id=?',(branch_id,)).fetchone()
            existing=dict(existing) if existing else None
            replay=None
            if existing and existing['request_hash']==request_hash(turn) and existing['status']=='committed':
                replay=json.loads(existing['receipt'])
            if replay is None:
                check_revision(row, turn.revision)
                if existing and existing['status']=='reserved' and existing['request_hash']!=request_hash(turn):
                    raise HTTPException(409,'열람 판정 요청이 보류 중입니다. 저장된 같은 입력을 재전송하거나 판정 전으로 회귀하세요.')
        if replay is not None:
            return decorated({**replay,'replayed':True},publish=True)
        trial_record=existing if existing and existing['status']=='reserved' else None
        resumed=trial_record is not None
        if state["ended"]:
            raise HTTPException(409, "종료된 분기입니다. 체크포인트를 복원하거나 새 게임을 시작하세요.")
        started = perf_counter()
        request = turn
        trace = {"requested_input": request.model_dump(), "before": deepcopy(state)}
        metrics, stage = None, "intent"

        def unwrap(value):
            if isinstance(value, GenerationResult):
                return value.proposal, {"trace": deepcopy(value.trace), "metrics": value.metrics}
            return value, {"trace": {"raw_output": deepcopy(value)}, "metrics": {}}

        def generation_error(message, provider_trace=None):
            if trial_record:
                decorated({'id':branch_id},publish=True)
                message+=' 판정값은 보존됐습니다. 같은 입력을 재전송하면 재추첨하지 않습니다.'
            if settings.dev_mode:
                if provider_trace is not None:
                    if stage == "draft":
                        trace["model"] = provider_trace
                    else:
                        trace.setdefault(stage, {})["trace"] = provider_trace
                trace["failure_stage"] = stage
                trace["saved_final_state"], trace["committed"] = None, False
                return HTTPException(502, {"message": message, "debug": trace})
            return HTTPException(502, message)

        raw_intent = None
        try:
            if resumed:
                saved=json.loads(trial_record['resolution'])
                turn=Turn.model_validate(saved['turn'])
                d=saved['decision']
                decision=Decision(turn,d['kind'],d['reason'],d.get('focus'))
                raw_intent={'source_answer':saved['source_answer']}
                trace['intent']={'reused_resolution':True,'metrics':{'elapsed_ms':0}}
            elif request.mode == "free":
                raw_intent, trace["intent"] = unwrap(app.state.provider.interpret(deepcopy(intent_context(state, request.text, diagnostics=settings.dev_mode))))
                trace["intent"]["proposal"] = deepcopy(raw_intent)
                if settings.dev_mode:
                    trace['approach'] = approach_diagnostic(raw_intent.pop('approach', None), request.text)
                decision = ground_intent(state, request, raw_intent)
                turn = decision.turn
            else:
                decision = Decision(turn, "direct", "explicit_action")
            trace["decision"] = decision.view()
            trace["selected_action"] = turn.model_dump()
            stage = "server"
            try:
                verdict = resolve(state, turn.action, turn.record_id)
            except ValueError as error:
                raise HTTPException(409, str(error)) from None
            source_answer = raw_intent.get('source_answer') if raw_intent else None
            plan = relationship_plan(state, turn, verdict, source_answer)
            verdict = plan['verdict']
            if turn.action=='request_access' and 'access_trial' in state:
                if state['access_trial']['status']=='untried' and not eligibility(state):
                    with store.connect(write=True) as db:
                        current=branch(db,branch_id)
                        check_revision(current,request.revision)
                        trial_record,created=reserve(db,current,state,request,
                            {'turn':turn.model_dump(),'decision':decision.view(),'source_answer':source_answer})
                        if created:
                            queue_report(db,current,state,trial_record,'reserved',model_info(),code)
                verdict=apply_decision(state,verdict,plan,trial_record)
                plan['verdict']=verdict
            trace['relationship'] = deepcopy(plan['audit'])
            trace['source_check'] = deepcopy(plan['source_result'])
            context = build_context(state, turn, verdict, plan)
            context["interaction"] = decision.view()
            if decision.kind in ("clarify", "unsupported") and not plan["source_result"]:
                context["server_result"] = {
                    "outcome": "conversation", "interaction_kind": decision.kind,
                    "message": "대상이 분명하지 않아 행동을 실행하지 않았습니다." if decision.kind == "clarify" else "지원 범위 밖의 요청으로 행동을 실행하지 않았습니다.",
                    "next_step": "대상이나 원하는 도움을 조금 더 구체적으로 말씀해 주세요." if decision.reason != "select_before_read" else "해당 공개 기록을 먼저 선택해 주세요.",
                }
            trace["server_result"], trace["provider_input"] = deepcopy(context["server_result"]), deepcopy(context)
            stage = "draft"
            raw = app.state.provider.propose(deepcopy(context))
            if isinstance(raw, GenerationResult):
                trace["model"] = deepcopy(raw.trace or {"raw_output": raw.proposal})
                metrics, raw = raw.metrics, raw.proposal
            else:
                trace["model"] = {"raw_output": deepcopy(raw)}
            proposal = Proposal.model_validate(raw)
            updated = apply_turn(state, turn, proposal, verdict, plan)
            stage = "review"
            reviewer = getattr(app.state.provider, "review", MockProvider().review)
            raw_review, trace["review"] = unwrap(reviewer(deepcopy(context), proposal.model_copy(deep=True)))
            trace["review"]["proposal"] = deepcopy(raw_review)
            review = validate_review(raw_review, proposal.dialogue)
            reply_reason = required_reply_reason(context) or ("review_rejected" if not review.consistent else None)
            if reply_reason:
                proposal = proposal.model_copy(update={"dialogue": grounded_reply(context)})
                updated = apply_turn(state, turn, proposal, verdict, plan)
            trace["final_dialogue_source"] = "server_grounded" if reply_reason else "model"
            trace["finalization_reason"] = reply_reason
            updated["messages"][-1]["server_result"] = deepcopy(context["server_result"])
            updated["messages"][-1]["consistency"] = {"status": "server_grounded" if reply_reason else "passed", "provider": type(app.state.provider).__name__, "reason": reply_reason,
                                                         "issues": [item.model_dump() for item in review.issues]}
            if request.mode == "free":
                updated["messages"][-2]["input_mode"] = "free"
                updated["messages"][-2]["interpretation"] = decision.view()
        except HTTPException:
            raise
        except ProviderError as error:
            raise generation_error(str(error), error.trace) from None
        except (ValidationError, ValueError, TypeError, AttributeError):
            raise generation_error("의도·응답·대사 검토 형식 또는 상태 제안이 잘못됐습니다. 이번 턴은 저장하지 않았습니다.") from None
        except Exception:
            raise generation_error("응답 처리에 실패했습니다. 이번 턴은 저장하지 않았습니다.") from None
        if metrics is not None:
            metrics = {**metrics, "draft_elapsed_ms": metrics["elapsed_ms"],
                       "elapsed_ms": round((perf_counter() - started) * 1000, 2),
                       "intent_elapsed_ms": trace.get("intent", {}).get("metrics", {}).get("elapsed_ms", 0),
                       "review_elapsed_ms": trace["review"]["metrics"].get("elapsed_ms", 0),
                       "llm_calls": 2 if resumed else 3 if request.mode == "free" else 2,
                       "dialogue_replaced": bool(reply_reason)}
        # Preserve the exact pre-turn state; never reconstruct it from dialogue.
        checkpoint_id = new_id()
        updated["messages"][-2]["checkpoint_id"] = checkpoint_id
        if 'access_trial' in state:
            updated['messages'][-1]['turn_audit']={'turn':len(state['messages'])//2+1,'timestamp':now(),
                'action':turn.action,'outcome':verdict['outcome'],'relationship':deepcopy(plan['audit']),
                'model':model_info(),'decision':plan.get('access_decision')}
        # Provider runs outside the write transaction; CAS prevents late overwrites.
        try:
            with store.connect(write=True) as db:
                current=branch(db, branch_id)
                check_revision(current, turn.revision)
                if verdict['outcome']=='access_granted':
                    private=db.execute('SELECT ending FROM private_settings WHERE branch_id=?',(branch_id,)).fetchone()
                    updated['ending']=json.loads(private['ending'])
                db.execute("INSERT INTO checkpoints(id,branch_id,label,revision,snapshot) VALUES(?,?,?,?,?)",
                           (checkpoint_id, branch_id, f"발언 {len(state['messages']) // 2 + 1} 전", turn.revision, encode(state)))
                db.execute("UPDATE branches SET snapshot=?, revision=revision+1 WHERE id=?", (encode(updated), branch_id))
                result = store.view(branch(db, branch_id))
                if plan.get('access_decision'):
                    db.execute("UPDATE access_attempts SET status='committed',receipt=? WHERE id=?",(encode(result),trial_record['id']))
                    queue_report(db,current,updated,trial_record,'committed',model_info(),code)
                    if verdict['outcome']=='access_granted':
                        queue_report(db,current,updated,trial_record,'committed',model_info(),code,kind='success')
        except sqlite3.Error:
            if trial_record:
                decorated({'id':branch_id},publish=True)
                raise HTTPException(503,'게임 턴 저장 실패. 판정값은 보존됐습니다. 같은 입력으로 재전송하세요.') from None
            raise
        if metrics is not None:
            result["generation"] = metrics
        if settings.dev_mode:
            trace["saved_final_state"] = deepcopy(result["state"])
            trace["committed"] = True
            result["debug"] = trace
        return decorated(result,publish=True)

    @app.get("/api/branches/{branch_id}/checkpoints")
    def checkpoints(branch_id: str):
        with store.connect() as db:
            row = branch(db, branch_id)
            # Other checkpoint metadata is visible, but snapshots never enter context.
            return [dict(r) for r in db.execute("""SELECT c.id,c.branch_id,c.label,c.revision,c.created_at
                FROM checkpoints c JOIN branches b ON c.branch_id=b.id WHERE b.game_id=?
                ORDER BY c.created_at DESC, c.rowid DESC""", (row["game_id"],))]

    @app.post("/api/branches/{branch_id}/regress", status_code=201)
    def regress(branch_id: str, request: RegressRequest):
        """Keep the selected turn and its reply; discard later state in a new branch.

        The next turn's pre-state is exactly the selected turn's post-state.
        This also works with checkpoints saved by the previous app version.
        """
        with store.connect(write=True) as db:
            source = branch(db, branch_id)
            check_revision(source, request.revision)
            state = json.loads(source["snapshot"])
            positions = [i for i, message in enumerate(state["messages"]) if message["role"] == "user"]
            if request.turn_number > len(positions):
                raise HTTPException(422, "돌아갈 대화 번호를 확인하세요.")
            if request.turn_number < len(positions):
                next_index = positions[request.turn_number]
                checkpoint_id = state["messages"][next_index].get("checkpoint_id")
                cp = db.execute("""SELECT c.* FROM checkpoints c
                    JOIN branches b ON b.id=c.branch_id WHERE c.id=? AND b.game_id=?""",
                    (checkpoint_id, source["game_id"])).fetchone()
                if cp is None or json.loads(cp["snapshot"])["messages"] != state["messages"][:next_index]:
                    raise HTTPException(409, "해당 대화가 끝난 시점의 상태가 저장되어 있지 않아 회귀할 수 없습니다.")
                snapshot = cp["snapshot"]
            else:
                # Latest turn: current state already is the exact post-turn state.
                checkpoint_id = new_id()
                snapshot = source["snapshot"]
                db.execute("INSERT INTO checkpoints(id,branch_id,label,revision,snapshot) VALUES(?,?,?,?,?)",
                           (checkpoint_id, branch_id, f"대화 {request.turn_number} 후", source["revision"], snapshot))
            bid = new_id()
            db.execute("INSERT INTO branches(id,game_id,parent_checkpoint_id,snapshot) VALUES(?,?,?,?)",
                       (bid, source["game_id"], checkpoint_id, snapshot))
            copy_private_settings(db,branch_id,bid,seed_factory)
            return store.view(branch(db, bid))

    @app.post("/api/branches/{branch_id}/checkpoints", status_code=201)
    def save_checkpoint(branch_id: str, request: CheckpointRequest):
        if not request.label.strip():
            raise HTTPException(422, "체크포인트 이름을 입력하세요.")
        cid = new_id()
        with store.connect(write=True) as db:
            row = branch(db, branch_id)
            check_revision(row, request.revision)
            db.execute("INSERT INTO checkpoints(id,branch_id,label,revision,snapshot) VALUES(?,?,?,?,?)",
                       (cid, branch_id, request.label, row["revision"], row["snapshot"]))
        return {"id": cid, "label": request.label}

    @app.post("/api/checkpoints/{checkpoint_id}/restore", status_code=201)
    def restore(checkpoint_id: str):
        with store.connect(write=True) as db:
            cp = db.execute("SELECT * FROM checkpoints WHERE id=?", (checkpoint_id,)).fetchone()
            if cp is None:
                raise HTTPException(404, "체크포인트를 찾을 수 없습니다.")
            source = branch(db, cp["branch_id"])
            bid = new_id()
            db.execute("INSERT INTO branches(id,game_id,parent_checkpoint_id,snapshot) VALUES(?,?,?,?)",
                       (bid, source["game_id"], checkpoint_id, cp["snapshot"]))
            copy_private_settings(db,cp['branch_id'],bid,seed_factory)
            return store.view(branch(db, bid))

    return app


app = create_app()
