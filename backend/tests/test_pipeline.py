from app.analysis.contracts import FindingSeverity, SourceFile
from app.analysis.pipeline import AnalysisPipeline


def test_pipeline_detects_security_quality_and_architecture_findings() -> None:
    files = [
        SourceFile("src/domain/order.py", """from fastapi import FastAPI
api_key = 'supersecretcredentialvalue'
def find_user(cursor, user_id):
    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")
    # TODO remove legacy path
    if user_id:
        for _ in range(20):
            if user_id % 2:
                pass
"""),
        SourceFile("requirements.txt", "requests==2.19.0"),
    ]

    result = AnalysisPipeline().run(files)

    assert result.language_breakdown == {"Python": 1}
    assert {finding.rule_id for finding in result.findings} >= {"CG-SEC-001", "CG-SEC-002", "CG-ARC-001", "CG-DEP-001"}
    assert any(finding.severity is FindingSeverity.CRITICAL for finding in result.findings)
    assert result.security_score < 100
    assert result.technical_debt_minutes > 0


def test_pipeline_ignores_non_source_files_for_static_scan() -> None:
    result = AnalysisPipeline().run([SourceFile("notes.txt", "api_key = 'supersecretcredentialvalue'")])
    assert result.findings == []
    assert result.quality_score == 100

