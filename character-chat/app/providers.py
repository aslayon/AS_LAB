"""Replace the provider through dependency injection; no database access here."""
from typing import Protocol
from dataclasses import dataclass

from .domain import advance_state, server_result
from .confidential import confidential_context
from .relationship import rules_for


@dataclass
class GenerationResult:
    proposal: object
    metrics: dict
    trace: dict | None = None


class ProviderError(Exception):
    """A public error plus request-local diagnostics, exposed only in dev mode."""

    def __init__(self, message, trace=None):
        super().__init__(message)
        self.trace = trace


def make_provider(settings):
    if settings.provider == "mock":
        return MockProvider()
    from .ollama_provider import OllamaProvider
    return OllamaProvider(settings)


class ResponseProvider(Protocol):
    def interpret(self, context: dict) -> object: ...
    def review(self, context: dict, proposal) -> object: ...
    def propose(self, context: dict) -> object: ...


class MockProvider:
    def interpret(self, context):
        from .intent import mock_interpret
        return mock_interpret(context)

    def review(self, context, proposal):
        # An offline fixture reviewer can certify only its own deterministic lines.
        expected = MockProvider().propose(context)["dialogue"]
        if proposal.dialogue == expected:
            return {"consistent": True, "issues": []}
        return {"consistent": False, "issues": [{"code": "misstates_state", "fact": "server_result"}]}

    def propose(self, context):
        verdict = context["verdict"]
        kind = context.get("interaction", {}).get("kind", "direct")
        source = context.get("confidential_context", {}).get("response")
        if source:
            line = source["message"]
        elif kind == "clarify":
            line = "어떤 기록이나 행동을 뜻하시는지 조금 더 분명히 말씀해 주시겠어요?"
        elif kind == "unsupported":
            line = "그 요청은 도와드리기 어렵겠군요. 여기서 확인하고 싶은 것이 무엇인가요?"
        elif verdict["outcome"] == "conversation":
            line = "말씀해 주세요. 듣고 있습니다."
        else:
            line = context["server_result"]["message"]
        return {"dialogue": line, **verdict}


def reading_context(state):
    """Derive recall evidence from this snapshot, never from an NPC claim."""
    progress = state.get("progress")
    if progress is None:
        return {"supported": False, "selected_record": None, "last_read_record": None}
    records = {record["id"]: record for record in state["config"]["public_records"]}
    selected = records.get(progress["selected_record"])
    selected_view = None if selected is None else {
        "id": selected["id"], "title": selected["title"],
        "has_been_read": selected["id"] in progress["read_records"],
    }
    latest = next((event for event in reversed(state["memories"])
                   if event["event"] == "record_read" and event.get("record_id") in progress["read_records"]
                   and event.get("record_id") in records), None)
    last_read = None if latest is None else {**records[latest["record_id"]], "turn": latest["turn"]}
    status = "아직 공개 기록을 열람하지 않았습니다." if last_read is None else f"가장 최근에 열람한 공개 기록은 '{last_read['title']}'입니다."
    return {"supported": True, "selected_record": selected_view,
            "last_read_record": last_read, "status": status}


def confirmed_history(state):
    """User attempts and server events, without internal speech receipts as NPC lines."""
    history = []
    for index, message in enumerate(state["messages"]):
        if message["role"] == "user":
            history.append({k: v for k, v in message.items() if k != "checkpoint_id"})
        elif message.get("server_result"):
            if message["server_result"]["outcome"] != "conversation":
                history.append({"role": "server", "server_result": message["server_result"]})
        elif index != 0:
            # Legacy character lines have no associated authoritative result.
            history.append({"role": "unverified_character", "content": message["content"]})
    return history


def conversational_history(state):
    """Reviewed social replies are context, never proof of a world event."""
    result, spoken = [], False
    for item in state["messages"]:
        if item["role"] == "user":
            spoken = item.get("action", "speak") == "speak"
            if spoken:
                result.append({"role": "user", "content": item["content"]})
        elif spoken and item.get("consistency", {}).get("status") in ("passed", "server_grounded"):
            result.append({"role": "character", "content": item["content"]})
    return result


def character_instructions(config):
    """Explicit audience boundary: unknown/author/player fields never enter NPC input."""
    keys = ('version', 'character', 'location', 'environment', 'core', 'known_facts', 'dialogue_guidelines', 'judgment_guidelines')
    result = {key: config[key] for key in keys if key in config}
    if 'public_records' in config:
        result['public_records'] = [{key: r[key] for key in ('id', 'title')} for r in config['public_records']]
    return result


def build_context(state, turn, verdict, plan=None):
    """Only the selected branch snapshot enters the provider context.

    Instructions and untrusted transcript are separate fields. No global history,
    checkpoint list, other branch data, or wall-clock future memory is read.
    """
    projected = advance_state(state, turn, verdict, plan)
    instructions = character_instructions(state["config"])
    actions = []
    if not projected["ended"]:
        actions = ["speak", "request_access", "force_access", "leave"]
        if "progress" in projected:
            actions.append("list_records")
            if projected["progress"]["catalog_seen"]:
                actions.append("select_record")
            if projected["progress"]["selected_record"]:
                actions.append("read_record")
    context = {
        "instructions": instructions,
        "state": {k: projected[k] for k in ("trust", "guard", "events", "summary", "memories", "progress", "ended") if k in state},
        # Restore links are UI metadata, not character memories or instructions.
        "history": confirmed_history(state),
        "dialogue_history": conversational_history(state),
        "attempt": {"text": turn.text, "action": turn.action, "record_id": turn.record_id},
        "server_result": server_result(state, turn, verdict, plan),
        "reading_context": reading_context(projected),
        "available_actions": actions,
        "capabilities": {"identity_verification": False, "permit_issuance": False,
                         "sealed_access": False, "public_records": "progress" in state},
        "verdict": verdict,
    }
    threshold = rules_for(state)['thresholds']['forced_access_end_attempts']
    if threshold != 2:
        context['capabilities']['forced_access_end_attempts'] = threshold
    if 'access_trial' in state:
        context['capabilities']['sealed_access']='server_decision_only'
        context['capabilities']['voluntary_access']='관계·상황 자격 충족 시 서버가 분기당 한 번 판정. 모델의 허가 선언은 효력이 없다.'
    private_view = confidential_context(projected, plan['source_result'] if plan else None)
    if private_view:
        context['confidential_context'] = private_view
    return context
