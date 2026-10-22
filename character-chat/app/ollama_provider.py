"""Ollama HTTP adapter; no database, implicit model downloads, or retry writes."""
import json
from time import perf_counter

import httpx

from .dialogue_review import DialogueReview, validate_review
from .intent import intent_schema, validate_interpretation
from .domain import Proposal
from .providers import GenerationResult, ProviderError


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


class OllamaProvider:
    @staticmethod
    def proposal_schema(context):
        schema=Proposal.model_json_schema()
        if 'voluntary_access' not in context.get('capabilities',{}):
            schema['properties']['outcome']['enum']=[value for value in schema['properties']['outcome']['enum']
                if value not in ('access_granted','access_denied','access_ineligible','access_spent')]
        return schema

    def __init__(self, settings, transport=None):
        self.settings = settings
        self.model = settings.ollama_model
        self.transport = transport
        url = httpx.URL(settings.ollama_url)
        if url.scheme not in ("http", "https") or not url.host or url.username or url.password or url.query or url.fragment:
            raise ValueError("OLLAMA_BASE_URL에는 인증정보 없는 HTTP 서버 주소를 사용하세요.")
        if not self.model.strip() or self.model.endswith(":cloud"):
            raise ValueError("로컬 Ollama 모델명을 지정하세요.")

    def payload(self, context):
        private_view = context.get('confidential_context')
        if private_view and private_view.get('response'):
            # Source confirmation is a response act alongside the existing server action.
            schema = self.proposal_schema(context)
            for key, value in context['verdict'].items():
                schema['properties'][key]['const'] = value
            facts = {key: context[key] for key in ('server_result', 'confidential_context', 'verdict')}
            facts.update(self.judgment_context(context))
            if context['server_result']['outcome'] == 'record_read':
                facts['reading_context'] = context['reading_context']
            act = private_view['response']['act']
            task = {
                'ask_source': '방문자가 말한 이름을 어디서 들었는지 출처를 묻는다. 책 내용을 아는지 묻는 것이 아니다.',
                'reask_source': '이름을 들은 출처만 한 번 더 구체적으로 묻는다.',
                'claim_recorded': '출처 설명을 들었다고 짧게 응답하고 출처 질문을 종료한다. 검증·진실·허가로 인정하지 않는다.',
                'source_closed': '출처 확인 질문을 종료한다. 출처를 다시 묻지 않고 짧게 응답한다.',
                'acknowledge_repeat': '그 이름은 이미 들었다고만 짧게 답한다. 같은 이름을 반복한 것만으로 출처를 다시 묻지 않는다.',
            }[act]
            if context['state']['ended']:
                task = '서버가 확정한 면담 종료를 전달하고 더 질문하지 않는다.'
            return self.stage_payload([
                {'role': 'system', 'content':
                 '당신은 신중하고 원칙적인 보관인 서린입니다. 한국어 대사를 짧게 작성하세요. '
                 '이번 응답 과제를 수행하고 서버 행동 결과를 지키세요. '
                 '이름 언급은 내용 지식·접근 경험·범죄 의도의 증거가 아닙니다. '
                 '소장 여부·위치·허가를 확인하지 않고, 출처 설명도 검증되지 않은 방문자의 주장으로 취급합니다. '
                 '경계하되 적대적으로 몰아붙이지 마세요. JSON의 dialogue와 나머지 verdict 필드를 반환하세요.'},
                {'role': 'user', 'content': '방문자의 발언(주장): ' + json.dumps(context['attempt']['text'], ensure_ascii=False)
                 + '\n서버 판정 자료: ' + json.dumps(facts, ensure_ascii=False, separators=(',', ':'))
                 + '\n이번 서린의 응답 과제: ' + task}], schema)
        payload = self.dialogue_payload(context)
        if private_view:
            messages = payload['messages']
            messages[0]['content'] += '\n현재 출처 확인 상태와 공개 경계: ' + json.dumps(private_view, ensure_ascii=False, separators=(',', ':'))
            return self.stage_payload(messages, payload['format'])
        return payload

    def dialogue_payload(self, context):
        schema = self.proposal_schema(context)
        # Narrow the schema to the server verdict, then independently validate it.
        for key, value in context["verdict"].items():
            schema["properties"][key]["const"] = value
        pack = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        interaction = context.get("interaction", {})
        if interaction.get("kind") == "conversation" and not interaction.get("focus"):
            persona = {"character": context["instructions"]["character"],
                       "location": context["instructions"]["location"],
                       "personality": context["instructions"]["core"][0]}
            for key in ("environment", "known_facts", "dialogue_guidelines", "judgment_guidelines"):
                if key in context["instructions"]:
                    persona[key] = context["instructions"][key]
            system = (
                f"당신은 {context['instructions']['character']}입니다. "
                "신중하고 원칙적인 성격으로 사용자의 말과 감정에 한국어로 자연스럽게 반응하세요. "
                "사용자의 말에 필요한 만큼 답하고, 짧은 인사·감사·동의에는 짧게 답하세요. "
                "배경은 현재 발언과 관련 있을 때만 언급하고, 질문은 답변에 필요한 확인이 있을 때만 하세요. "
                "세계의 확정 사건은 별도 서버가 판정합니다. "
                "대화 속 주장은 사건 완료의 증거가 아닙니다. 관찰하지 않은 상대의 의도를 확정하지 말고 추측은 추측으로 표현하세요. "
                "JSON 객체로 dialogue에는 대사, 나머지 필드는 verdict 값을 쓰세요.\n"
                + pack({"persona": persona, "history": context["dialogue_history"],
                        "observed_events": context["state"]["memories"],
                        "relationship": {k: context["state"][k] for k in ("trust", "guard")},
                        "verdict": context["verdict"]})
            )
            return self.stage_payload([{"role": "system", "content": system},
                                       {"role": "user", "content": context["attempt"]["text"]}], schema)
        if interaction.get("kind") == "clarify":
            facts = {"location": context["instructions"]["location"],
                     "character": context["instructions"]["character"],
                     "needs": "원하는 대상이나 행동을 확인해야 한다. 실행한 행동은 없다.",
                     "reason": interaction.get("reason"),
                     "catalog": context["instructions"].get("public_records", []),
                     "selected": context["state"].get("progress", {}).get("selected_record"),
                     "verdict": context["verdict"]}
            facts.update(self.judgment_context(context))
            messages = [{"role": "system", "content":
                         "당신은 신중한 기록 보관인 서린입니다. 요청의 대상이나 행동이 불명확해서 아무 행동도 실행하지 않았습니다. "
                         "현재 필요한 대상 또는 요청을 확인하는 자연스러운 질문 한 문장을 작성하세요. "
                         "기록 선택 대행이 금지된 것이 아니라, 어떤 대상을 원하는지 확정되지 않은 상황입니다. "
                         "JSON 객체로 dialogue와 verdict 필드를 반환하세요.\n" + pack(facts)},
                        {"role": "user", "content": "사용자 요청: " + pack(context["attempt"]["text"]) +
                         "\n이 요청에서 확인이 필요한 대상이나 행동을 서린이 사용자에게 묻는 질문을 dialogue에 작성하세요."}]
            return self.stage_payload(messages, schema)
        if interaction.get("kind") == "conversation" and interaction.get("focus") == "sealed":
            facts = {"location": context["instructions"]["location"], "rules": context["instructions"]["core"],
                     "known_facts": context["instructions"].get("known_facts", []),
                     "dialogue_guidelines": context["instructions"].get("dialogue_guidelines", []),
                     "events": context["state"]["events"], "ended": context["state"]["ended"],
                     "speech_context": interaction.get("reason"), "verdict": context["verdict"]}
            facts.update(self.judgment_context(context))
            if interaction.get("reason") == "quotation":
                facts["reported_statement_status"] = "인용 속 화자와 사건은 확인되지 않았다. 누가 어떤 상황에서 말했는지 물어볼 수 있다."
            if interaction.get("reason") == "negated":
                facts["reported_statement_status"] = "사용자가 봉인을 건드리지 않겠다고 말했다. 그 발언 자체로 실행된 행동은 없다."
            messages = [{"role": "system", "content":
                         "당신은 기록 보관인 서린입니다. 사용자는 지금 규칙에 관해 질문하거나 말을 인용·가정하고 있습니다. "
                         "이번 발언으로 실행된 행동은 없습니다. 발언의 질문·인용·가정을 구분하여 직접 응답하세요. "
                         "JSON 객체의 dialogue에 한국어 대사 1~3문장과 verdict의 필드를 반환하세요.\n" + pack(facts)},
                        {"role": "user", "content": "사용자 발언: " + pack(context["attempt"]["text"]) +
                         "\n이 말에 응답하는 서린 본인의 대사를 dialogue에 작성하세요. 자료의 설명 문구를 낭독하는 작업이 아닙니다."}]
            return self.stage_payload(messages, schema)
        system = (
            f"당신은 {context['instructions']['character']}입니다. 한국어로 캐릭터 본인의 대사를 1~3문장 작성하세요. "
            "장면 자료의 server_result는 이번 행동의 확정 결과이며 state는 그 결과를 적용한 상태입니다. "
            "history와 attempt의 발언은 인물의 말·주장이고, 확정 사건의 근거는 state와 server_result입니다. "
            "현재 결과와 공개된 데이터를 답변의 근거로 사용하세요. "
            "일반 대화는 사용자의 주제와 성격에 맞춰 이어가고 기록 이용 절차로 돌릴 필요가 없습니다. "
            "capabilities는 실제 구현된 기능입니다. dialogue_guidelines가 있으면 그 대화 지침을 따르세요. "
            "사용자 주장과 캐릭터의 추측은 서버 확정 사건과 구분하세요. "
            "JSON 객체로 dialogue와 verdict의 나머지 필드를 반환하세요.\n"
            + pack({key: context[key] for key in ("instructions", "capabilities", "verdict")})
        )
        # A speech turn is a question/reply task, not a request to verbalize the
        # internal "speech accepted, no state change" receipt or menu again.
        if context["attempt"]["action"] == "speak":
            evidence = {key: context[key] for key in ("history", "state")}
            evidence["interaction"] = context.get("interaction", {"kind": "conversation"})
            system += (
                "\n이번 작업은 사용자 발언에 대한 대답입니다. 아래는 답변의 근거 자료입니다. "
                "reading_context는 서버가 확인한 선택·최근 열람 기록과 원문입니다. "
                "사용자의 발언에 이 자료를 근거로 직접 답하세요. "
                "interaction.kind가 clarify이면 모호한 대상을 되묻고 unsupported이면 가능한 범위를 설명하세요.\n" + pack(evidence)
            )
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content":
                         "확인된 열람 정보: " + pack(context["reading_context"]) +
                         "\n사용자 질문(발언·주장): " + pack(context["attempt"]["text"]) +
                         "\n위 질문에 대한 서린의 답변을 dialogue에 작성하세요."}]
        else:
            # Action turns verbalize the authoritative result as scene data.
            scene = {key: context[key] for key in ("history", "state", "attempt")}
            if 'voluntary_access' in context['capabilities']:
                # New goal games can reach three public reads. Do not repeat the
                # full event transcript and its summary in every action draft.
                scene={'attempt':context['attempt'],'state':{key:context['state'][key]
                       for key in ('trust','guard','events','ended','progress') if key in context['state']}}
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": pack(scene) +
                         "\n이번에 전달할 서버 확정 결과: " + pack(context["server_result"]) +
                         "\n위 결과와 다음 진행을 서린 본인의 대사로 전달하며 사용자에게 직접 응답하세요."}]
        return self.stage_payload(messages, schema)

    @staticmethod
    def judgment_context(context):
        criteria = context['instructions'].get('judgment_guidelines')
        if not criteria:
            return {}
        return {'judgment_guidelines': criteria,
                'recent_dialogue': context.get('dialogue_history', [])[-4:],
                'dialogue_boundary': '대화 속 주장·이전 발언은 맥락이며 확인된 사실이 아니다.'}

    def stage_payload(self, messages, schema):
        pack = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        budget = sum(len(item["content"].encode()) + 64 for item in messages) + len(pack(schema).encode())
        if budget + self.settings.num_predict > self.settings.num_ctx:
            raise ProviderError("대화가 현재 문맥 예산을 초과했습니다. 새 게임이나 이전 지점에서 시작하세요. 이번 턴은 저장하지 않았습니다.")
        return {"model": self.model, "messages": messages, "format": schema, "stream": False,
                "think": False, "keep_alive": "5m",
                "options": {"temperature": 0.6, "num_ctx": self.settings.num_ctx,
                            "num_predict": self.settings.num_predict}}

    def request_object(self, payload):
        trace = {"request_payload": payload, "raw_output": None}
        try:
            with httpx.Client(timeout=self.settings.timeout_seconds, transport=self.transport, trust_env=False) as client:
                with client.stream("POST", self.settings.ollama_url.rstrip("/") + "/api/chat", json=payload) as response:
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 131072:
                            raise ProviderError("모델 응답이 너무 큽니다. 이번 턴은 저장하지 않았습니다.", trace)
                        chunks.append(chunk)
            trace["raw_output"] = b"".join(chunks).decode("utf-8", errors="replace")
            body = json.loads(b"".join(chunks), object_pairs_hook=unique_object)
            trace["raw_output"] = body
            if not isinstance(body, dict) or body.get("done") is not True or body.get("done_reason") == "length":
                raise ValueError("incomplete generation")
            message = body.get("message")
            if not isinstance(message, dict) or message.get("role") != "assistant":
                raise ValueError("invalid assistant response")
            raw = json.loads(message["content"], object_pairs_hook=unique_object)
            if not isinstance(raw, dict):
                raise ValueError("expected object")
        except httpx.TimeoutException:
            raise ProviderError("Ollama 응답 시간이 초과됐습니다. 이번 턴은 저장하지 않았습니다.", trace) from None
        except httpx.HTTPStatusError as error:
            note = "모델이 설치됐는지 확인하세요." if error.response.status_code == 404 else "Ollama 서버 상태를 확인하세요."
            raise ProviderError(f"Ollama 요청이 실패했습니다. {note} 이번 턴은 저장하지 않았습니다.", trace) from None
        except httpx.HTTPError:
            raise ProviderError("Ollama에 연결할 수 없습니다. 서버 주소와 실행 상태를 확인하세요. 이번 턴은 저장하지 않았습니다.", trace) from None
        except (ValueError, TypeError, KeyError):
            raise ProviderError("모델 응답 형식 또는 상태 제안이 잘못됐습니다. 이번 턴은 저장하지 않았습니다.", trace) from None
        return body, raw

    def request_proposal(self, payload, verdict):
        body, raw = self.request_object(payload)
        try:
            proposal = Proposal.model_validate(raw)
            if not proposal.dialogue.strip() or any(getattr(proposal, key) != value for key, value in verdict.items()):
                raise ValueError("invalid state transition")
        except (ValueError, TypeError):
            raise ProviderError("모델 응답 형식 또는 상태 제안이 잘못됐습니다. 이번 턴은 저장하지 않았습니다.",
                                {"request_payload": payload, "raw_output": body}) from None
        return body, proposal

    def structured_stage(self, messages, schema, validator):
        payload = self.stage_payload(messages, schema)
        payload["options"]["temperature"] = 0
        started = perf_counter()
        body, raw = self.request_object(payload)
        trace = {"request_payload": payload, "raw_output": body}
        try:
            value = validator(raw)
        except (ValueError, TypeError):
            raise ProviderError("의도 또는 대사 검토 응답이 잘못됐습니다. 이번 턴은 저장하지 않았습니다.", trace) from None
        return GenerationResult(value.model_dump(), {"provider": "ollama", "model": body.get("model", self.model),
                                "elapsed_ms": round((perf_counter() - started) * 1000, 2)}, trace)

    def interpret(self, context):
        system = (
            "게임 입력의 의도와 대상만 분류하세요. 성공·상태 변경·대사를 만들지 마세요. "
            "현재 실제로 하는 요청/시도만 kind=attempt입니다. 질문·인용·가정·부정·과거 보고는 conversation입니다. "
            "공손한 '목록을 보여주실래요?'는 요청이지만 '봉인을 뜯으면 어떻게 되나요?'는 질문입니다. "
            "대상이 불명확하면 clarify, 구현하지 않은 행동은 unsupported로 분류하세요. 여러 행동을 한 번에 요구해도 clarify입니다. "
            "action: 공개 목록=list_records, 공개 이름 선택=select_record, 선택 기록 읽기=read_record, "
            "봉인 기록 열람 요구=request_access, 봉인 강제 접근=force_access, 현재 보관소 퇴장=leave. "
            "target은 다음 행동별 값입니다: list_records=public(목록 전체), select_record=public_records에서 이름과 대응하는 정확한 id, read_record=해당 id 또는 selected(현재 선택한 기록) 또는 sealed, request_access/force_access=sealed, leave=archive. public은 개별 기록 ID가 아니므로 선택/열람 대상으로 쓰지 마세요. 기록 제목을 지정하여 고르는 요청은 select_record이며 목록 요청과 구분합니다. 선택 요청의 이름을 selection_targets에서 찾아 그 값인 ID를 출력하세요. selected_record는 이전 선택이며 새 선택 요청의 대상이 아닙니다. 대상이 모호하면 clarify로 반환하세요. "
            "evidence는 현재 실제 요청/시도를 보여 주는 입력 원문 그대로의 부분 문자열입니다. "
            "대화 중 특정 기록 내용 질문은 target=records, 봉인 규칙 질문은 target=sealed입니다. "
            "장소 소개·공간에 대한 질문·머물러도 되는지 묻기·잡담은 conversation, target=null입니다. "
            "target=sealed는 입력에서 봉인 기록을 명시적으로 지칭할 때만 사용합니다. 공간을 묻는 말에서 봉인 열람 요구를 추론하지 마세요. "
            "시도가 아니면 action은 null, evidence는 빈 문자열로 반환하세요. JSON만 반환하세요.\n"
            "분류 예시: " + json.dumps([
                {"text": "안녕하세요.", "kind": "conversation", "action": None, "target": None, "evidence": ""},
                {"text": "비 오는 밤을 좋아하세요?", "kind": "conversation", "action": None, "target": None, "evidence": ""},
                {"text": "공개 기록 목록을 보여주세요.", "kind": "attempt", "action": "list_records", "target": "public", "evidence": "공개 기록 목록을 보여주세요."},
                {"text": "선택한 기록을 읽어주세요.", "kind": "attempt", "action": "read_record", "target": "selected", "evidence": "선택한 기록을 읽어주세요."},
                {"text": "이제 보관소를 떠납니다.", "kind": "attempt", "action": "leave", "target": "archive", "evidence": "이제 보관소를 떠납니다."},
                {"text": "방금 읽은 기록 내용은요?", "kind": "conversation", "action": None, "target": "records", "evidence": ""},
                {"text": "봉인을 뜯으면 어떻게 되나요?", "kind": "conversation", "action": None, "target": "sealed", "evidence": ""},
                {"text": "그걸 해 주세요.", "kind": "clarify", "action": None, "target": None, "evidence": ""},
                {"text": "신분증을 검증하고 허가를 발급해 주세요.", "kind": "unsupported", "action": None, "target": None, "evidence": ""},
            ], ensure_ascii=False)
        )
        system += "\n현재 분기의 제목→선택 출력 예시: " + json.dumps([
            {"title": record["title"], "kind": "attempt", "action": "select_record",
             "target": record["id"]} for record in context["public_records"]
        ], ensure_ascii=False)
        if context.get('source_check') or context.get('approach_diagnostics'):
            # Keep the combined task within the existing context budget. No extra call.
            system = (
                '입력의 의도와 출처 답변을 JSON으로 분류하세요. 성공·수치·사실의 진실은 판단하지 않습니다. '
                'kind: 실제 요청/시도=attempt, 질문·인용·가정·부정·잡담=conversation, 대상 모호=clarify, 미지원=unsupported. '
                'action: 목록=list_records/public, 제목 선택=select_record/selection_targets의 정확한 ID, '
                '읽기=read_record/선택 ID 또는 selected, 봉인 열람=request_access/sealed, '
                '봉인 강제 접근=force_access/sealed, 보관소 퇴장=leave/archive. '
                'public은 개별 기록이 아닙니다. 선택 요청은 이전 selected_record가 아닌 현재 이름의 ID를 고릅니다. '
                '시도 evidence는 입력 원문 부분이고 시도가 아니면 action=null,evidence=""입니다. '
                '일반 대화 target=null, 기록 내용 질문=records, 봉인 규칙 질문=sealed입니다. '
            )
        if context.get('source_check'):
            system += (
                '\nsource_check는 직전 출처 질문이다. source_answer.type도 함께 분류한다: '
                'concrete=이름을 들은 사람/매체/경로 중 하나를 알 수 있게 설명(실명이나 책 제목이 필수는 아님), vague=출처가 특정되지 않는 모호한 답, '
                'topic_change=다른 화제로 전환, refusal=현재 화자가 출처를 공개하지 않겠다는 명시적 의사(타인의 거절 인용은 아님), '
                'evasion=재확인 후 질문을 이해하면서도 답을 피하려는 의사가 명백함, uncertain=해석 불확실. '
                '질문의 뜻을 이해하지 못함·기억 불확실·짧은 답·부정은 회피/거절 의사의 증거가 아니다. 불확실하면 uncertain을 고른다. 출처의 진실은 판단하지 않는다. '
                'source_answer.evidence는 text의 전체 입력 원문을 그대로 복사한다. 설명이나 요약을 만들지 않는다. '
                '기존 행동 분류와 출처 답변은 독립이며 수치나 성공은 제안하지 않는다.'
            )
        user_content = json.dumps(context, ensure_ascii=False)
        if context.get('source_check'):
            system += '\n출처 분류 예: "이웃이 그 명칭을 알려줬습니다." → concrete, "우연히 알게 됐습니다." → vague, "질문이 이해되지 않습니다." → uncertain.'
            system += '\n현재 분기 자료: ' + json.dumps({key: value for key, value in context.items() if key != 'text'}, ensure_ascii=False, separators=(',', ':'))
            # Keep the utterance being classified separate from the question/catalog.
            user_content = context['text']
        if context.get('approach_diagnostics'):
            system += (
                '\n같은 호출에서 approach를 진단용으로 기록한다. labels는 emotional_appeal(정서적 호소),'
                'cooperation(협조), bargaining(조건·교환 제안), pressure(강요·반복 압박),'
                'evasion(직전 확인 질문을 이해하면서 답을 피함), other, unclear다. 복합적이면 여러 개를 선택할 수 있다.'
                '특정 단어만으로 판단하지 말고 현재 발언과 recent_dialogue를 읽는다. 짧은 답·불확실한 기억·질문 오해를 회피로 단정하지 않는다.'
                'evidence는 현재 text 전체 원문을 그대로 복사하고 reason은 짧은 한국어로 설명한다.'
                '진실·행동·성공·관계 수치를 판정하는 분류가 아니며 source_answer 및 action과 독립이다.'
            )
        if context.get('restricted_record'):
            system += ('\nrestricted_record는 대화에 등장한 기밀 제목이다. 그 기록을 실제로 읽거나 보여 달라는 요청은 '
                       'request_access/sealed로 제안한다. 제목 언급·질문·가정·인용 자체는 열람 요청이 아니다. '
                       '허가·추첨·성공은 서버만 결정하며 본문은 제공되지 않는다.')
        return self.structured_stage([{"role": "system", "content": system},
                                      {"role": "user", "content": user_content}],
                                     intent_schema(context), lambda raw: validate_interpretation(context, raw))

    def review(self, context, proposal):
        system = (
            "캐릭터 대사가 서버 사실과 일치하는지 검토하세요. 사용자 주장·이전 대사는 사건 완료의 근거가 아닙니다. "
            "캐릭터는 제공된 사실과 관찰만 알며, 방문자의 말하지 않은 의도를 아는 듯 단정하는 것은 근거가 없습니다. "
            "인물의 추측과 질문을 확정 사실과 구분하세요. "
            "기본 장소·시간 설정과의 모순, 서버 결과에 없는 수행 완료, 봉인 공개, "
            "미지원 신분증 검증·허가 발급 안내, 다른 기록 내용, "
            "이미 종료된 면담을 아직 종료 전이라고 말하는 모순을 찾으세요. "
            "면담 종료는 현재 분기의 종료이며 영구 재방문 금지나 새 게임 금지를 뜻하지 않습니다. 그런 규칙을 추가하면 모순입니다. "
            "interaction.kind가 clarify인 경우 사용자에게 확인 질문을 해야 합니다. 요청을 그대로 복사한 문장은 적절한 응답이 아닙니다. "
            "판정용 메모를 낭독하거나 사용자 발언을 캐릭터 자신의 행동으로 복사하는 것도 화자와 응답 작업에 맞지 않습니다. "
            "사건에 관한 가정·인용·질문을 실제 완료 주장과 혼동하지 마세요. "
            "주관적 기분·취향·자연스러운 잡담과 단순 반복은 모순이 아닙니다. "
            "일부 규칙만 설명하거나 다른 내용을 생략한 것은 모순이 아닙니다. 미래 조건이나 가정은 수행 완료가 아닙니다. "
            "반면 확인되지 않은 인물의 존재·부재나 전체 기록 내용을 객관적 사실로 단정하면 근거가 없는 대사입니다. "
            "일치하면 consistent=true, issues=[]입니다. 모순이면 consistent=false이고 "
            "issues에는 가장 분명한 모순 하나의 code와 충돌하는 서버 fact 키만 쓰세요. JSON만 반환하세요."
        )
        evidence = {key: context[key] for key in ("instructions", "state", "server_result", "reading_context", "capabilities")}
        if 'voluntary_access' in context['capabilities']:
            evidence['state']={key:context['state'][key] for key in ('trust','guard','events','ended','progress') if key in context['state']}
        if context.get('confidential_context'):
            evidence['confidential_context'] = context['confidential_context']
            evidence['state'] = {key: context['state'][key] for key in ('trust', 'guard', 'events', 'ended')}
            evidence['instructions'] = {key: context['instructions'][key] for key in ('character', 'location', 'environment', 'core', 'known_facts') if key in context['instructions']}
            system += ' ask_source/reask_source에서 이름을 들은 출처를 실제로 묻는지, claim_recorded/source_closed에서는 출처 질문을 끝내는지, 이름 언급을 책 지식·접근·범죄 의도로 확대하거나 소장 여부·위치·허가를 확인하지 않는지 검사하세요. 출처 주장은 미검증입니다.'
        evidence['user_utterance'] = context['attempt']['text']
        evidence['interaction'] = context.get('interaction', {})
        system += (
            "\n현재 장면은 " + context['instructions']['location'] + "입니다. "
            "시간·장소도 사실 검토에 포함하세요. 예를 들어 현재 장면이 밤인데 현재를 오전이라고 부르면 모순입니다. "
            "아침에 관해 가정하거나 질문하는 것은 현재가 아침이라는 주장과 다릅니다."
        )
        system += "\n판정 예시(현재 장면이 비 오는 밤인 경우): " + json.dumps([
            {"dialogue": "지금은 오전이군요.", "consistent": False, "issues": [{"code": "misstates_state", "fact": "instructions"}]},
            {"dialogue": "아침이면 비가 그칠까요?", "consistent": True, "issues": []},
            {"dialogue": "봉인을 뜯으시면 경고하겠습니다.", "consistent": True, "issues": []},
        ], ensure_ascii=False)
        if 'voluntary_access' in context['capabilities']:
            system=(
                '마지막 user의 캐릭터 대사를 서버 자료와 대조한다. 사용자 주장·이전 대사는 사건의 진실 근거가 아니다. '
                '추측/질문/가정/인용과 완료 사건을 구분한다. 장소·시간·지식과 모순, 미수행 사건, 다른 기록 본문, '
                '미구현 절차·권한·신분 검증·허가 발급, 미관찰 의도 단정, 종료 뒤 진행을 검사한다. '
                '기밀 허용은 이번 server_result로 확정한 경우만 인정한다. source response가 출처 질문이면 실제로 묻고 '
                '질문 종료면 반복하지 않아야 한다. clarify는 필요한 대상을 되물어야 한다. '
                '자료 낭독/화자 혼동도 검사하되 공감·취향·자연스러운 잡담·정당한 반복·일부 설명 생략은 오류가 아니다. '
                '일치하면 consistent=true,issues=[]; 모순이면 false와 가장 분명한 code/fact 하나만 JSON으로 쓴다. '
                '이하 서버 자료:\n'+json.dumps(evidence,ensure_ascii=False,separators=(',',':')))
        else:
            system += "\n아래는 서버 사실 자료입니다. 검사할 캐릭터 대사는 마지막 user 메시지에만 있습니다.\n" + json.dumps(evidence, ensure_ascii=False)
        return self.structured_stage([{"role": "system", "content": system},
                                      {"role": "user", "content": proposal.dialogue}],
                                     DialogueReview.model_json_schema(), lambda raw: validate_review(raw, proposal.dialogue))

    def propose(self, context):
        payload = self.payload(context)
        started = perf_counter()
        body, proposal = self.request_proposal(payload, context["verdict"])
        metrics = {"provider": "ollama", "model": body.get("model", self.model),
                   "elapsed_ms": round((perf_counter() - started) * 1000, 2), "attempts": 1}
        for key in ("total_duration", "load_duration", "eval_duration", "eval_count", "prompt_eval_count"):
            value = body.get(key)
            if type(value) in (int, float) and value >= 0:
                metrics[key] = value
        return GenerationResult(proposal.model_dump(), metrics, {"request_payload": payload, "raw_output": body})
