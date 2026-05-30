# placeholder: report_builder.py
"""
Report builder for the interview flow.

Exports:
- build_report(agg_result, details=None) -> FinalReport
- render_report_html(final_report) -> str

Keeps dependencies minimal; HTML rendering is a simple template string.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.schemas import FinalReport


def _recommendation_from_score(score: float) -> str:
    if score >= 85:
        return "hire"
    if score >= 65:
        return "onsite"
    if score >= 45:
        return "phone_screen"
    return "reject"


def build_report(agg_result: Dict[str, Any], details: Optional[Dict[str, Any]] = None) -> FinalReport:
    """
    Build a FinalReport from aggregation results.

    agg_result expected keys:
      - final_score (0..100)
      - per_skill (dict)
      - details (optional)
    """
    final_score = float(agg_result.get("final_score", 0.0))
    per_skill = agg_result.get("per_skill", {})
    recommendation = _recommendation_from_score(final_score)
    notes = []

    # add basic note about distribution
    if final_score >= 85:
        notes.append("Candidate demonstrates strong mastery across evaluated skills.")
    elif final_score >= 65:
        notes.append("Candidate shows solid capability with some areas to probe further.")
    elif final_score >= 45:
        notes.append("Candidate meets minimum expectations but requires follow-up on gaps.")
    else:
        notes.append("Candidate falls below the current role expectations.")

    raw = {"agg": agg_result}
    if details:
        raw["details"] = details

    return FinalReport(
        final_score=final_score,
        per_skill=per_skill,
        recommendation=recommendation,
        notes=notes,
        raw=raw,
    )


def render_report_html(report: FinalReport, title: str = "Interview Report") -> str:
    """
    Render a minimal HTML report (string). Suitable for quick viewing or emailing.
    """
    ts = datetime.utcnow().isoformat() + "Z"
    skills_rows = ""
    for skill, score in (report.per_skill or {}).items():
        skills_rows += f"<tr><td>{skill}</td><td style='text-align:right'>{score:.1f}</td></tr>"

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; padding: 20px; }}
    .score {{ font-size: 48px; font-weight: 700; }}
    table {{ border-collapse: collapse; width: 480px; margin-top: 12px; }}
    td, th {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background: #f7f7f7; text-align: left; }}
    .notes {{ margin-top: 16px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p><strong>Generated:</strong> {ts}</p>
  <p class="score">{report.final_score:.1f}</p>
  <p><strong>Recommendation:</strong> {report.recommendation}</p>

  <h3>Per-skill scores</h3>
  <table>
    <thead><tr><th>Skill</th><th style='text-align:right'>Score</th></tr></thead>
    <tbody>
      {skills_rows or '<tr><td colspan="2">No skill scores available</td></tr>'}
    </tbody>
  </table>

  <div class="notes">
    <h3>Notes</h3>
    <ul>
      {"".join(f"<li>{n}</li>" for n in (report.notes or []))}
    </ul>
  </div>
</body>
</html>"""
    return html