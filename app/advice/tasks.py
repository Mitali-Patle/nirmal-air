"""The two AI tasks the app runs: today's plan and a question about it."""

from app.advice import ask, plan
from app.advice.standard import standard_plan
from app.ai.task import AITask

PLAN_TASK = AITask(
    name="plan",
    version=plan.PLAN_VERSION,
    system=plan.SYSTEM,
    output=plan.Plan,
    payload=plan.plan_payload,
    check=plan.check_plan,
    fallback=standard_plan,
    temperature=0.3,
    max_output_tokens=2400,
)

ASK_TASK = AITask(
    name="ask",
    version=ask.ASK_VERSION,
    system=ask.SYSTEM,
    output=ask.Answer,
    payload=ask.ask_payload,
    check=ask.check_answer,
    fallback=ask.standard_answer,
    temperature=0.2,
    max_output_tokens=600,
)
