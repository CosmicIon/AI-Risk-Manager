from langchain_core.prompts import PromptTemplate

EVIDENCE_SUMMARY_PROMPT = """Summarize the following raw evidence data into a clean, human-readable format.
Focus only on key dates, names, tracking numbers, IP addresses, and authentication outcomes (like AVS or 3DS matches).

Raw Evidence:
{raw_evidence}

Summary:
"""

evidence_summary_template = PromptTemplate(
    input_variables=["raw_evidence"],
    template=EVIDENCE_SUMMARY_PROMPT
)
