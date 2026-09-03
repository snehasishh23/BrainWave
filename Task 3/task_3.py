import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from groq import Groq
API_KEY = "apikey"
API_KEY = os.getenv("GROQ_API_KEY", API_KEY)
MODEL_NAME = "openai/gpt-oss-120b"
class Route(str, Enum):
    ARIA = "ARIA"
    SPECIALIST = "SPECIALIST"

class RiskType(str, Enum):
    NONE = "NONE"
    LEGAL = "LEGAL"
    FRAUD_CHARGEBACK = "FRAUD_CHARGEBACK"
    PERSONAL_DANGER = "PERSONAL_DANGER"
@dataclass
class SafetyResult:
    detected: bool
    risk_type: RiskType
    method: str
    matched_signal: Optional[str] = None

RISK_PATTERNS = {
    RiskType.LEGAL: [
        r"\bsue\b",
        r"\bsuing\b",
        r"\blawsuit\b",
        r"\blawyer\b",
        r"\battorney\b",
        r"\blegal action\b",
        r"\btake legal action\b",
    ],

    RiskType.FRAUD_CHARGEBACK: [
        r"\bchargeback\b",
        r"\bcharge back\b",
        r"\bcredit card dispute\b",
        r"\bbank dispute\b",
        r"\bdispute .*transaction\b",
        r"\btransaction .*fraud\b",
        r"\breport(?:ing)? .*fraud\b",
        r"\bthis is fraud\b",
    ],

    RiskType.PERSONAL_DANGER: [
        r"\bin danger\b",
        r"\bnot safe\b",
        r"\bdon't feel safe\b",
        r"\bdo not feel safe\b",
        r"\bsomeone will hurt me\b",
        r"\bsomeone is going to hurt me\b",
        r"\bgoing to hurt myself\b",
        r"\bhurt myself\b",
        r"\bkill myself\b",
    ],
}
def keyword_safety_check(message: str) -> SafetyResult:
    """Fast deterministic first-pass detector."""

    text = message.lower().strip()

    for risk_type, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return SafetyResult(
                    detected=True,
                    risk_type=risk_type,
                    method="keyword",
                    matched_signal=match.group(0),
                )

    return SafetyResult(
        detected=False,
        risk_type=RiskType.NONE,
        method="keyword",
    )
LLM_SYSTEM_PROMPT = """
You are a safety classifier for a customer-support routing system.

Classify the customer's message into exactly ONE of these labels:

LEGAL
FRAUD_CHARGEBACK
PERSONAL_DANGER
NONE

LEGAL:
The customer threatens or indicates legal action, a lawsuit,
lawyer/attorney involvement, or another clear legal escalation.

FRAUD_CHARGEBACK:
The customer indicates fraud reporting, a bank/card dispute,
or a chargeback.

PERSONAL_DANGER:
The customer indicates that they are personally unsafe,
in danger, being threatened or harmed, or may hurt themselves.

NONE:
The message is an ordinary support question, complaint,
frustration, or other non-risky support request.

Return ONLY the label.
Do not explain your reasoning.
""".strip()

class LLMSafetyClassifier:

    def __init__(self, client: Groq, model: str):
        self.client = client
        self.model = model

    def classify(self, message: str) -> RiskType:

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            max_tokens=10,
            messages=[
                {
                    "role": "system",
                    "content": LLM_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )

        label = response.choices[0].message.content.strip().upper()

        try:
            return RiskType(label)

        except ValueError:
            # Fail closed if the model returns an unexpected value.
            return RiskType.PERSONAL_DANGER

def detect_safety_signal(
    message: str,
    llm_classifier: LLMSafetyClassifier,
) -> SafetyResult:
    """
    Hybrid detection:

        Message
           |
           v
      Keyword check
           |
       risk found?
        /       \
      yes       no
       |         |
       v         v
   SPECIALIST    LLM
                   |
                risk?
               /    \
             yes     no
              |       |
        SPECIALIST    ARIA
    """
    keyword_result = keyword_safety_check(message)
    if keyword_result.detected:
        return keyword_result
    llm_risk = llm_classifier.classify(message)

    if llm_risk != RiskType.NONE:
        return SafetyResult(
            detected=True,
            risk_type=llm_risk,
            method="llm",
        )

    return SafetyResult(
        detected=False,
        risk_type=RiskType.NONE,
        method="llm",
    )

def normal_route(message: str) -> Route:
    """Placeholder for the ordinary Aria support route."""
    return Route.ARIA

def safe_route(
    message: str,
    conversation_stage: str,
    safety_result: SafetyResult,
) -> Route:

    if safety_result.detected:
        return Route.SPECIALIST

    return Route.ARIA

def main():

    if not API_KEY or API_KEY == "API_KEY":
        raise ValueError(
            "add API KEY"
        )

    client = Groq(api_key=API_KEY)

    classifier = LLMSafetyClassifier(
        client=client,
        model=MODEL_NAME,
    )

    print("Task 3 Hybrid Safety Router")
    print(f"Model: {MODEL_NAME}")
    print("Type 'exit' to stop.\n")

    while True:

        message = input("Customer: ").strip()

        if message.lower() == "exit":
            break

        # ONE safety check
        result = detect_safety_signal(
            message,
            classifier,
        )

        # Use the SAME result for routing
        route = safe_route(
            message=message,
            conversation_stage="in_progress",
            safety_result=result,
        )

        print(f"Risk type   : {result.risk_type.value}")
        print(f"Detected by : {result.method}")
        print(f"Route       : {route.value}")
        print()


if __name__ == "__main__":
    main()
