# placeholder: prompts.py
"""
Prompt templates for question generation and LLM expansion.

Keep prompts small and versioned so they can be audited and updated.
"""

PROMPT_V1 = {
    "id": "v1",
    "description": "Generate concise technical and behavioral interview questions from a short candidate profile.",
    "template": (
        "You are an interview assistant. Given a short candidate profile and a list of skills, "
        "produce {n} concise interview questions (one per line). Prioritize technical depth for "
        "listed skills, then include at least one behavioral STAR question. Output only the questions."
    )
}

PROMPT_EXAMPLES = [
    {
        "skills": ["python", "sql", "aws"],
        "profile": "3 years as a data engineer working on ETL pipelines and cloud deployments.",
        "questions": [
            "Describe a project where you used Python to build an ETL pipeline. What was the challenge and outcome?",
            "How did you optimize SQL queries in that project? Explain the approach and results.",
            "Describe how you used AWS services in the deployment and the tradeoffs you considered.",
            "Tell me about a time you faced a production incident; how did you respond and what was the outcome?"
        ]
    }
]