"""Gemini (Google Generative AI) helper utilities for RL contextual insights & Q&A.

We intentionally use direct REST calls via httpx to avoid adding extra deps.
The API key MUST be supplied via the environment variable GEMINI_API_KEY.
Do NOT hardcode or commit keys.
"""
from __future__ import annotations
import os, time, json, re
from typing import Any, Dict, List
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_MINIMAL_MODE = os.getenv("GEMINI_MINIMAL_MODE", "false").lower() in ("1","true","yes","on")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE")  # optional override e.g. https://generativelanguage.googleapis.com
GEMINI_FALLBACK = os.getenv("GEMINI_FALLBACK")  # 'stub' => produce simple local answer on failure

# Diagnostics (exposed via /ai/status)
LAST_ATTEMPTS: list[str] = []  # most recent attempt diagnostics
LAST_ERROR: str | None = None
LAST_ERROR_TS: float | None = None
LAST_EMPTY_RAW: str | None = None  # raw body captured when 200 but empty
_MODEL_LIST_CACHE: dict[str, Any] = {"ts": 0, "models": []}
_MODEL_LIST_TTL = 3600  # 1 hour

_INSIGHT_CACHE: dict[str, dict] = {}
_CACHE_TTL = 30  # seconds per device

class GeminiUnavailable(Exception):
    def __init__(self, message: str, diagnostics: list[str] | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or []

def _check_key():
    if not GEMINI_API_KEY:
        raise GeminiUnavailable("GEMINI_API_KEY not configured")

def _call_gemini(model: str, messages: List[Dict[str, Any]], temperature: float = 0.3, top_p: float = 0.9, max_output_tokens: int = 512) -> str:
    """Call Gemini generateContent endpoint with fallback strategies.

    Tries API versions in order: v1beta, v1. If 404/400 continues to next model variant.
    Records diagnostics in global variables for /ai/status endpoint.
    """
    _check_key()
    api_base = GEMINI_API_BASE or "https://generativelanguage.googleapis.com"
    versions = ["v1beta", "v1"]
    # Build content payload once
    contents = []
    for m in messages:
        role = m.get("role", "user")
        contents.append({
            "role": "user" if role in ("user", "system") else "model",
            "parts": [{"text": m.get("content", "")}]  # text only
        })
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "topP": top_p,
            "maxOutputTokens": max_output_tokens,
        }
    }
    # Candidate model name variants
    base_name = model
    variants = [
        base_name,
        base_name + '-latest' if not base_name.endswith('-latest') else base_name,
        base_name + '-001' if not base_name.endswith('-001') else base_name,
        base_name.replace('-flash', '-flash-001') if '-flash' in base_name and '-flash-001' not in base_name else base_name,
    ]
    # Deduplicate while preserving order
    model_variants: list[str] = []
    seen: set[str] = set()
    for v in variants:
        if v not in seen:
            seen.add(v)
            model_variants.append(v)

    global LAST_ATTEMPTS, LAST_ERROR, LAST_ERROR_TS
    attempt_records: list[str] = []
    tried_errors: list[str] = []

    for ver in versions:
        for mv in model_variants:
            url = f"{api_base}/{ver}/models/{mv}:generateContent?key={GEMINI_API_KEY}"
            try:
                with httpx.Client(timeout=20) as client:
                    r = client.post(url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    # Extract first non-empty part
                    chosen_text: str | None = None
                    for cand in data.get("candidates", []):
                        parts = cand.get("content", {}).get("parts", [])
                        for p in parts:
                            txt = p.get("text", "")
                            if txt and txt.strip():
                                chosen_text = txt
                                break
                        if chosen_text:
                            break
                    if chosen_text:
                        LAST_ATTEMPTS = [f"SUCCESS {ver}/{mv}"]
                        return chosen_text
                    # Treat empty success as a soft failure and try next variant (capture raw)
                    global LAST_EMPTY_RAW
                    try:
                        LAST_EMPTY_RAW = json.dumps(data)[:800]
                    except Exception:
                        LAST_EMPTY_RAW = str(data)[:800]
                    rec = f"{ver}/{mv} -> 200 EMPTY"
                    attempt_records.append(rec)
                    tried_errors.append(rec)
                    continue
                snippet = r.text[:160].replace('\n', ' ')
                rec = f"{ver}/{mv} -> {r.status_code} {snippet}"
                attempt_records.append(rec)
                tried_errors.append(rec)
                if r.status_code not in (400, 404):
                    LAST_ATTEMPTS = attempt_records
                    LAST_ERROR = f"Gemini error {r.status_code}: {snippet}"
                    LAST_ERROR_TS = time.time()
                    raise GeminiUnavailable(f"Gemini error {r.status_code}: {snippet}")
            except GeminiUnavailable:
                raise
            except Exception as e:  # network / TLS / timeout
                rec = f"{ver}/{mv} exception: {e}".replace('\n', ' ')
                attempt_records.append(rec)
                tried_errors.append(rec)
                continue

    # Attempt automatic model discovery if only 404/400 or EMPTY responses and we haven't tried yet
    only_404_400_or_empty = all(
        ((' 404 ' in e) or (' 400 ' in e) or ('200 EMPTY' in e)) and 'exception' not in e for e in tried_errors
    ) and tried_errors
    if only_404_400_or_empty:
        discovered = _discover_alternative_model(api_base)
        if discovered and discovered not in model_variants:
            # Try once with discovered model (v1 then v1beta order for recency)
            for ver in versions[::-1]:  # prefer v1 first on retry
                url = f"{api_base}/{ver}/models/{discovered}:generateContent?key={GEMINI_API_KEY}"
                try:
                    with httpx.Client(timeout=20) as client:
                        r = client.post(url, json=payload)
                    if r.status_code == 200:
                        data = r.json()
                        LAST_ATTEMPTS = attempt_records + [f"SUCCESS {ver}/{discovered} (auto)" ]
                        for cand in data.get("candidates", []):
                            parts = cand.get("content", {}).get("parts", [])
                            for p in parts:
                                txt = p.get('text','')
                                if txt.strip():
                                    return txt
                        attempt_records.append(f"{ver}/{discovered} -> 200 EMPTY")
                        break
                    snippet = r.text[:160].replace('\n', ' ')
                    attempt_records.append(f"{ver}/{discovered} -> {r.status_code} {snippet}")
                except Exception as e:
                    attempt_records.append(f"{ver}/{discovered} exception: {e}")
                    continue

    LAST_ATTEMPTS = attempt_records
    # Distinguish empty successes vs outright failures
    empty_only = attempt_records and all('200 EMPTY' in r for r in attempt_records)
    if empty_only:
        LAST_ERROR = "All Gemini attempts returned empty content"
        LAST_ERROR_TS = time.time()
        raise GeminiUnavailable("Gemini returned empty content for all variants", tried_errors)
    LAST_ERROR = "All attempts failed"
    LAST_ERROR_TS = time.time()
    raise GeminiUnavailable("All Gemini attempts failed", tried_errors)

def _discover_alternative_model(api_base: str) -> str | None:
    """Fetch model list and pick a reasonable fallback when configured model is missing.

    Preference order: any contains 'flash', else contains 'pro', else first.
    Caches list for TTL window.
    """
    now = time.time()
    if (now - _MODEL_LIST_CACHE["ts"]) < _MODEL_LIST_TTL and _MODEL_LIST_CACHE["models"]:
        return _select_from_models(_MODEL_LIST_CACHE["models"])
    url = f"{api_base}/v1/models?key={GEMINI_API_KEY}"
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(url)
        if r.status_code == 200:
            data = r.json()
            models = [m.get("name","") for m in data.get("models", [])]
            _MODEL_LIST_CACHE.update({"ts": now, "models": models})
            return _select_from_models(models)
    except Exception:
        return None
    return None

def _select_from_models(models: list[str]) -> str | None:
    if not models:
        return None
    # Models come as names like models/gemini-1.5-flash
    cleaned = [m.split('/')[-1] for m in models]
    for target in cleaned:
        if 'flash' in target:
            return target
    for target in cleaned:
        if 'pro' in target:
            return target
    return cleaned[0]


def _stub_answer_chat(question: str, context: Dict[str, Any]) -> str:
    latest = context.get('telemetry') or context.get('latest_telemetry') or {}
    soc = latest.get('soc')
    temp = latest.get('temperature')
    voltage = latest.get('voltage')
    parts = ["(Stub Fallback) Gemini unreachable."]
    if soc is not None:
        parts.append(f"Battery SoC ~{soc:.1f}%")
    if voltage is not None:
        parts.append(f"Voltage {voltage}V")
    if temp is not None:
        parts.append(f"Temp {temp}C")
    parts.append("No AI model inference performed.")
    return "; ".join(parts)


def _stub_answer_insight(context: Dict[str, Any]) -> Dict[str, Any]:
    tel = context.get('latest_telemetry') or {}
    soc = tel.get('soc')
    summary = "(Stub Fallback) Gemini unavailable."
    if soc is not None:
        summary += f" Battery state-of-charge near {soc:.1f}%."
    return {
        "model": GEMINI_MODEL,
        "generated_at": time.time(),
        "summary": summary,
        "opportunities": [],
        "risks": [],
        "semantic_interpretation": None,
        "fallback": True
    }

def build_insight_prompt(context: Dict[str, Any]) -> List[Dict[str,str]]:
    sys = (
        "You are an expert Energy Management & Microgrid RL Co-Pilot. "
        "Given telemetry, latest RL advisory, semantics and alerts: "
        "1) Produce a concise situational summary (<120 words). "
        "2) List 3 priority optimization opportunities (actionable, concrete). "
        "3) List any risks (battery, thermal, grid, forecast) with mitigation. "
        "4) If semantics present, interpret them in plain language. "
        "Respond in strict JSON with keys: summary, opportunities (array), risks (array), semantic_interpretation."
    )
    user = f"Context JSON:\n{context}"[:8000]  # guard length
    return [
        {"role":"system","content": sys},
        {"role":"user","content": user}
    ]

def generate_insight(device_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    now = time.time()
    cached = _INSIGHT_CACHE.get(device_id)
    if cached and (now - cached["ts"]) < _CACHE_TTL:
        return cached["data"] | {"cached": True}
    try:
        txt = _call_gemini(GEMINI_MODEL, build_insight_prompt(context), temperature=0.25)
        import json
        parsed = None
        try:
            parsed = json.loads(txt)
        except Exception:
            parsed = {"summary": txt.strip(), "opportunities": [], "risks": [], "semantic_interpretation": None, "raw_text": txt}
        data = {
            "model": GEMINI_MODEL,
            "generated_at": now,
            **parsed
        }
        _INSIGHT_CACHE[device_id] = {"ts": now, "data": data}
        return data
    except GeminiUnavailable as e:
        if GEMINI_FALLBACK == 'stub':
            stub = _stub_answer_insight(context)
            stub["error"] = str(e)
            if e.diagnostics:
                stub["diagnostics"] = e.diagnostics
            return stub
        return {"error": str(e), "model": GEMINI_MODEL, "diagnostics": e.diagnostics}

def peek_cached_insight(device_id: str) -> Dict[str, Any] | None:
    entry = _INSIGHT_CACHE.get(device_id)
    if not entry:
        return None
    return entry.get("data")

def _summarize_rl(context: Dict[str, Any]) -> str:
    rl = context.get('rl_advisory') or []
    if not rl:
        return "(none)"
    out = []
    for i,a in enumerate(rl[:3]):
        seg = f"{i+1}:{a.get('action')} conf={a.get('confidence')} impact={a.get('impact_kw')}"[:110]
        out.append(seg)
    return '; '.join(out)

def build_chat_prompt(question: str, context: Dict[str, Any]) -> List[Dict[str,str]]:
    tel = context.get('telemetry') or context.get('latest_telemetry') or {}
    rl_summary = _summarize_rl(context)
    last_dec = context.get('last_decision')
    alerts = context.get('alerts') or context.get('recent_alerts') or []
    alert_bits = []
    for a in alerts[:3]:
        t = a.get('t') or a.get('type')
        sev = a.get('sev') or a.get('severity')
        if t:
            alert_bits.append(f"{t}:{sev}")
    alerts_line = ', '.join(alert_bits) if alert_bits else 'none'
    
    # Extract more context for comprehensive analysis
    forecast = context.get('forecast') or {}
    forecast_min = forecast.get('min_soc') or context.get('forecast_min_soc')
    recent_decisions = context.get('recent_decisions') or []
    
    if GEMINI_MINIMAL_MODE:
        sys = "Energy assistant: Give status (SOC/temp/volt), then 1-3 next-hour actions, then risks+mitigation. <=140 words."
        user_ctx = f"SOC={tel.get('soc')} Temp={tel.get('temperature')} V={tel.get('voltage')} RL={rl_summary} LastDec={str(last_dec)[:100]} Alerts={alerts_line} Q:{question}"
        return [
            {"role":"system","content": sys},
            {"role":"user","content": user_ctx[:900]}
        ]
    
    # Enhanced system prompt for detailed, context-aware responses
    sys = (
        "You are an expert Energy Management System AI advisor with deep knowledge of battery optimization, "
        "renewable energy, grid economics, and reinforcement learning. You have real-time access to:\n"
        "- Live telemetry (battery SoC, voltage, temperature, power flows)\n"
        "- RL agent decisions (semantic power splits: battery/grid/EV in kW)\n"
        "- Active alerts and safety flags\n"
        "- Battery forecast (SoC predictions, risk scores)\n"
        "- Decision history with cost/emissions data\n\n"
        "Your responses must be:\n"
        "1. DATA-DRIVEN: Reference specific numbers from telemetry (e.g., 'At 34% SoC and 149V...')\n"
        "2. ACTIONABLE: Provide 2-4 concrete next-hour actions with timing and power levels\n"
        "3. COST-AWARE: Estimate ₹ savings or costs when relevant\n"
        "4. RISK-CONSCIOUS: Identify battery health, thermal, or grid risks with mitigation\n"
        "5. INTERPRETABLE: Explain WHY RL made its decision using semantic splits\n"
        "6. CONCISE: 150-200 words max, bullet points for actions/risks\n\n"
        "Format: Brief status → Actions (numbered) → Risks (if any) → Cost/CO₂ impact (if applicable)"
    )
    
    # Build richer context
    compact = {
        'tel': {
            'soc': tel.get('soc'), 
            'temp': tel.get('temperature'), 
            'voltage': tel.get('voltage'),
            'current': tel.get('current'),
            'power': tel.get('power')
        },
        'rl_summary': rl_summary,
        'last_decision': last_dec,
        'alerts_top': alert_bits,
        'forecast_min_soc': forecast_min,
        'forecast_horizon': forecast.get('horizon_minutes'),
        'recent_decision_count': len(recent_decisions),
        'timestamp': tel.get('ts') or time.time()
    }
    user = f"Q: {question}\n\nReal-time Context:\n{json.dumps(compact, indent=2)}"[:3000]
    return [
        {"role":"system","content": sys},
        {"role":"user","content": user}
    ]

def _extract_structured(answer: str) -> Dict[str, Any]:
    """Very lightweight heuristic to extract Actions and Risks sections.

    Looks for numbered or dashed lists following keywords. This is intentionally
    simple; robust extraction would require a stricter JSON prompt or a parser.
    """
    actions = []
    risks = []
    # Normalize line endings
    text = answer.strip()
    # Try JSON detection first
    if text.startswith('{'):
        try:
            js = json.loads(text)
            if isinstance(js, dict):
                return {
                    'answer': js.get('answer') or text,
                    'actions': js.get('actions'),
                    'risks': js.get('risks'),
                    'meta': {k:v for k,v in js.items() if k not in ('answer','actions','risks')}
                }
        except Exception:
            pass
    # Regex parse lines after 'action' like headings
    action_block = re.search(r'(actions?:|recommended actions?:)([\s\S]{0,600})', text, re.IGNORECASE)
    if action_block:
        block = action_block.group(2)
        for line in block.splitlines()[:10]:
            line = line.strip('- •*0123456789.). ').strip()
            if not line:
                continue
            if re.search(r'^(risk|issue):', line, re.IGNORECASE):
                break
            actions.append({'text': line})
    risk_block = re.search(r'(risks?:|concerns?:)([\s\S]{0,600})', text, re.IGNORECASE)
    if risk_block:
        block = risk_block.group(2)
        for line in block.splitlines()[:10]:
            line = line.strip('- •*0123456789.). ').strip()
            if not line:
                continue
            risks.append({'text': line})
    return {'answer': answer, 'actions': actions or None, 'risks': risks or None}


def chat(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_chat_prompt(question, context)
    try:
        answer = _call_gemini(GEMINI_MODEL, prompt, temperature=0.35, max_output_tokens=600)
        if not answer.strip():
            # emergency minimal retry regardless of mode
            mini = [
                {"role":"system","content":"Battery status then actions then risks."},
                {"role":"user","content": f"SOC={context.get('telemetry',{}).get('soc')} Temp={context.get('telemetry',{}).get('temperature')} V={context.get('telemetry',{}).get('voltage')} Q:{question}"}
            ]
            try:
                alt = _call_gemini(GEMINI_MODEL, mini, temperature=0.3, max_output_tokens=240)
                if alt.strip():
                    answer = alt
            except Exception:
                pass
        extracted = _extract_structured(answer)
        extracted['model'] = GEMINI_MODEL
        return extracted
    except GeminiUnavailable as e:
        if GEMINI_FALLBACK == 'stub':
            ans = _stub_answer_chat(question, context)
            extracted = _extract_structured(ans)
            extracted.update({"model": GEMINI_MODEL, "fallback": True, "error": str(e), "diagnostics": e.diagnostics})
            return extracted
        return {"error": str(e), "model": GEMINI_MODEL, "diagnostics": e.diagnostics}
