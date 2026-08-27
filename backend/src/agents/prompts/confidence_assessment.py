from langchain_core.prompts import PromptTemplate

CONFIDENCE_PROMPT = """Based on the provided narrative and evidence, provide a brief qualitative assessment of our chances to win this chargeback dispute.
The Machine Learning model gave a win probability score of {win_probability}.

Narrative:
{narrative}

Assessment:
"""

confidence_assessment_template = PromptTemplate(
    input_variables=["win_probability", "narrative"],
    template=CONFIDENCE_PROMPT
)
