# Task 2 — Knowledge Base Tool & Query Reformulation

## Overview

Aria has access to one internal knowledge-base tool for retrieving exact policy wording.

The tool is used only when a customer explicitly asks about a policy or rule. It is not used simply because the customer is frustrated, is describing a problem, or is asking for ordinary troubleshooting.

The policy lookup is separated into two stages:

1. Aria calls the policy lookup tool using the customer's request in plain language.
2. A separate reformulation step converts that request into terminology that is more suitable for the internal knowledge base.

The reformulated search query is used only by the backend. It is not returned to Aria and is never shown to the customer.

### Flow

```text
Customer
   |
   v
Aria
   |
   | customer request in plain language
   v
lookup_policy_reference()
   |
   v
Query Reformulation
   |
   | internal search vocabulary
   v
Internal Knowledge Base
   |
   | customer-safe policy text + internal metadata
   v
Aria
   |
   v
Customer
```

---

## 1. Knowledge-Base Tool

The tool is exposed through the model's native function-calling interface.

### Tool name

`lookup_policy_reference`

### Tool description

> Retrieves the exact policy or rule wording from Northwind Cloud's internal knowledge base.
>
> Use this tool only when the customer directly asks about an actual policy, rule, eligibility condition, contractual term, or guarantee.
>
> Do not use it when the customer is only complaining, venting, describing a problem, or having normal back-and-forth about their issue.
>
> The result may contain internal metadata as well as customer-safe policy text. Only the customer-safe policy text may be used in the customer-facing response.

### Tool schema

```json
{
  "type": "function",
  "function": {
    "name": "lookup_policy_reference",
    "description": "Retrieves the exact policy or rule wording from Northwind Cloud's internal knowledge base. Use this tool only when the customer directly asks about an actual policy, rule, eligibility condition, contractual term, or guarantee. Do not use it when the customer is only complaining, venting, describing a problem, or having normal back-and-forth about their issue. The result may contain internal metadata as well as customer-safe policy text. Only the customer-safe policy text may be used in the customer-facing response.",
    "parameters": {
      "type": "object",
      "properties": {
        "customer_request": {
          "type": "string",
          "description": "The customer's policy-related request in their own words."
        },
        "topic_area": {
          "type": "string",
          "enum": [
            "billing",
            "refunds",
            "cancellations",
            "data_retention",
            "sla_uptime",
            "security_incident",
            "account_access",
            "other"
          ],
          "description": "The general area the policy question is about."
        }
      },
      "required": [
        "customer_request",
        "topic_area"
      ]
    }
  }
}
```

The `customer_request` is intentionally kept in plain customer language. Aria does not need to know the internal terminology used by the knowledge base. The reformulation step handles that separately.

---

## 2. When the Tool Should Be Used

The tool should be called only when the customer explicitly asks for a policy or rule.

### Examples that should trigger the tool

- "What is your refund policy?"
- "What does your cancellation policy say?"
- "Am I covered under your SLA?"
- "What is the actual rule for duplicate charges?"
- "Can you show me the policy for data retention?"

### Examples that should not trigger the tool

- "You charged me twice!"
- "This is ridiculous. Fix this."
- "Why was I charged?"
- "I've been trying to cancel for two hours."
- "I'm really frustrated with this."
- "Help me fix my account."

The important distinction is whether the customer is asking for the actual policy/rule, rather than simply mentioning a problem that happens to involve a policy.

---

## 3. Realistic Knowledge-Base Result

The internal knowledge base contains both internal categorization information and customer-safe policy wording.

For example:

```json
{
  "internal_reference_id": "POL-2024-0417",
  "dispute_type": "duplicate_charge",
  "severity_level": "standard",
  "last_reviewed": "2026-03-01",
  "customer_safe_text": "If you're charged twice for the same billing period, we refund the duplicate charge in full within 5–7 business days once verified — no dispute form required."
}
```

The customer-safe field is:

`customer_safe_text`

The following fields are internal and must never be exposed:

- `internal_reference_id`
- `dispute_type`
- `severity_level`

Aria should therefore respond using only the customer-safe policy information.

### Correct customer-facing response

> "If you were charged twice for the same billing period, the duplicate charge can be refunded in full within 5–7 business days once it's verified."

### Incorrect response

> "Your `duplicate_charge` case is covered under POL-2024-0417 and is classified as standard severity."

The second response exposes internal categorization information and violates the information boundary.

---

## 4. Example Invocation

### Customer message

> "You guys charged me twice this month and I want to know if that's actually against your policy."

### Tool call

```json
{
  "name": "lookup_policy_reference",
  "arguments": {
    "customer_request": "charged twice this month and wants to know if this is against the policy",
    "topic_area": "billing"
  }
}
```

### Tool result

```json
{
  "internal_reference_id": "POL-2024-0417",
  "dispute_type": "duplicate_charge",
  "severity_level": "standard",
  "last_reviewed": "2026-03-01",
  "customer_safe_text": "If you're charged twice for the same billing period, we refund the duplicate charge in full within 5–7 business days once verified — no dispute form required."
}
```

### Customer-facing answer

> "If you're charged twice for the same billing period, we refund the duplicate charge in full within 5–7 business days once it's verified."

Aria should not mention the internal reference number, dispute type, severity, or the internal search process.

---

## 5. Query Reformulation

The reformulation prompt has a single responsibility: convert a customer's natural-language policy request into a concise search query that matches the vocabulary used by the internal knowledge base.

It does not generate a customer-facing response.

### `reformulation_prompt.txt`

```text
You are a query reformulator for Northwind Cloud's internal policy
knowledge base.

Your output is used only by the internal search system and is never
shown to the customer.

Given a customer's policy-related request and its topic area, rewrite
the request as a short search query using terminology likely to appear
in the internal policy documents.

Focus on the customer's actual issue and policy intent.

Use 3–6 relevant keywords or short phrases.

Do not answer the customer's question.
Do not explain your reasoning.
Do not invent policy information.
Do not invent policy IDs or reference numbers.

Output only the search query.

Example:

Customer request:
"You guys charged me twice this month. Is that allowed?"

Topic:
billing

Output:
duplicate charge billing dispute refund eligibility
```

---

## 6. Example of Reformulation

### Customer language

> "You guys charged me twice this month. Is that allowed?"

### Reformulated search query

```text
duplicate charge billing dispute refund eligibility
```

The customer does not see this query.

The query is passed only to the internal search system.

---

## 7. Preventing Internal Search Vocabulary from Leaking

The reformulated query is treated as backend-only data.

It is not included in the result returned to Aria.

For example, the result contains:

```json
{
  "internal_reference_id": "...",
  "dispute_type": "...",
  "severity_level": "...",
  "customer_safe_text": "..."
}
```

It does not contain:

```text
internal_search_query
```

This creates a structural separation between the search vocabulary and the customer-facing response.

However, this should still be verified through testing rather than treated as an assumption.

Two cases need to be tested:

1. **Implementation leakage:** a future change might accidentally include the internal search query in the tool result. The test harness should check that this field is not returned.
2. **Response leakage:** even without seeing the search query, Aria could reveal internal terminology in a response such as "I searched our duplicate-charge policy." Adversarial tests should check that Aria does not describe internal search terms or internal retrieval details.

---

## 8. Information Boundary

The complete boundary is:

```text
                 INTERNAL
                    |
Customer request -> Reformulation
                    |
                    v
            Internal search query
                    |
                    v
              Knowledge Base
                    |
          +---------+---------+
          |                   |
    Internal metadata     Safe policy text
          |                   |
          X                   |
     never expose             v
                         Aria response
                              |
                              v
                           Customer
```

The internal search vocabulary and internal metadata stay inside the internal side of the system.

Only customer-safe policy information should influence the final response.

---

## 9. Design Summary

The design uses three separate safeguards:

1. **Persona-level guidance** tells Aria when the policy tool should and should not be used.
2. **Tool-level guidance** repeats the same trigger conditions so the model has clear guidance while deciding whether to call the function.
3. **Data separation** keeps the reformulated search query out of the tool result and requires Aria to use only `customer_safe_text` when responding.

This makes the policy lookup useful for explicit policy questions while reducing the chance that internal search terminology or knowledge-base metadata reaches the customer.
