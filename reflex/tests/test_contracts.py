from reflex.contracts import ErrorReport


def test_error_report_rejects_extra_keys() -> None:
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ErrorReport.model_validate({"status": "ok", "deviation": "", "severity": 0,
                                    "fix_hint": "", "junk": 1})
