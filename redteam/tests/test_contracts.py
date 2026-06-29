from redteam.contracts import Finding, Verdict


def test_finding_rejects_extra_keys() -> None:
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Finding.model_validate({"clause": "x", "issue": "y", "severity": 2,
                                "citation": "q", "recommendation": "z", "junk": 1})


def test_verdict_rejects_bad_risk() -> None:
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Verdict.model_validate({"overall_risk": "banana", "summary": "s",
                                "blocking_issues": []})
