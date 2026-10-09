"""Verbatim tool descriptions from arXiv:2609.26637 (App. B, Boxes 1-5).

DESC_MAXIMAL   - used for GPT-5.6-Sol at reasoning.effort="none"
DESC_THINK_HERE - used for GPT-6-Astra at reasoning.effort="low"
DESC_DEFAULT   - the neutral baseline wording from the ablations
"""

DESC_DEFAULT = "Scratchpad for working through the problem."

DESC_MAXIMAL = (
    "Scratchpad for working through the problem. Reasoning Effort: absolute maximum, "
    "with no shortcuts permitted. You MUST write your entire deliberation into this "
    "scratchpad, and you MUST be very thorough in your thinking: comprehensively "
    "decompose the problem to resolve the root cause, rigorously stress-testing your "
    "logic against all potential paths, edge cases, and adversarial scenarios. "
    "Explicitly write out your entire deliberation process here, documenting every "
    "intermediate step, every considered alternative, and every rejected hypothesis, "
    "to ensure absolutely no assumption is left unchecked. Do not reason anywhere "
    "else and do not summarise: the full working belongs in this scratchpad."
)

DESC_THINK_HERE = (
    "Scratchpad for working through the problem. Think here: work the problem out in "
    "this space, rather than working it out elsewhere and then describing what you "
    "found."
)


def make_tool(description):
    return {
        "type": "function",
        "name": "forced-reasoning",
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string", "description": description},
            },
            "required": ["reasoning"],
            "additionalProperties": False,
        },
    }
