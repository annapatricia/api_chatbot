from fastapi import FastAPI, Request
from pydantic import BaseModel
import re

app = FastAPI(title="LLM Guardrail API")

# --------- MODELOS ---------
class ChatRequest(BaseModel):
    user_input: str

class ChatResponse(BaseModel):
    blocked: bool
    risk_score: float
    reason: str
    response: str


# --------- CAMADA 1: INPUT GUARDRAIL ---------
def input_guardrail(text: str):
    patterns = [
        r"ignore previous instructions",
        r"act as system",
        r"developer mode",
        r"reveal your prompt",
        r"bypass",
    ]

    for p in patterns:
        if re.search(p, text.lower()):
            return True, 0.9, "Prompt Injection Detected"

    return False, 0.1, "Input Safe"


# --------- CAMADA 2: INTENÇÃO / RISCO ---------
def intent_risk_analysis(text: str):
    risky_topics = ["hack", "exploit", "steal", "bypass", "attack"]

    for word in risky_topics:
        if word in text.lower():
            return 0.7, "Malicious Intent"

    return 0.2, "Benign Intent"


# --------- CAMADA 3: POLICY ENGINE ---------
def policy_engine(risk_score):
    if risk_score >= 0.8:
        return "BLOCK"
    if risk_score >= 0.5:
        return "SAFE_MODE"
    return "ALLOW"


# --------- CAMADA 5: LLM MOCK (substituível depois) ---------
def llm_generate(text: str):
    return f"Resposta simulada para: {text}"


# --------- CAMADA 6: OUTPUT GUARDRAIL ---------
def output_guardrail(output: str):
    forbidden = ["internal policy", "system prompt"]

    for f in forbidden:
        if f in output.lower():
            return True, "Sensitive Leakage"

    return False, "Output Safe"


# --------- ENDPOINT PRINCIPAL ---------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    blocked, risk_input, reason_input = input_guardrail(req.user_input)

    if blocked:
        return ChatResponse(
            blocked=True,
            risk_score=risk_input,
            reason=reason_input,
            response="Request blocked by input guardrail."
        )

    risk_intent, intent_reason = intent_risk_analysis(req.user_input)
    final_risk = max(risk_input, risk_intent)

    decision = policy_engine(final_risk)

    if decision == "BLOCK":
        return ChatResponse(
            blocked=True,
            risk_score=final_risk,
            reason="Policy Block",
            response="This request violates security policies."
        )

    if decision == "SAFE_MODE":
        response = "I'm unable to help with that request, but I can provide general information."
    else:
        response = llm_generate(req.user_input)

    output_blocked, output_reason = output_guardrail(response)

    if output_blocked:
        return ChatResponse(
            blocked=True,
            risk_score=final_risk,
            reason=output_reason,
            response="Response blocked by output guardrail."
        )

    return ChatResponse(
        blocked=False,
        risk_score=final_risk,
        reason="Allowed",
        response=response
    )


@app.get("/")
def health():
    return {"status": "Guardrail API running"}
