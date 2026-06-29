from memeforge.contracts import CaptionSet, Ranking


def test_caption_set_rejects_extra_keys() -> None:
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CaptionSet.model_validate({"persona": "x", "captions": ["a"], "junk": 1})


def test_ranking_requires_nonempty() -> None:
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Ranking.model_validate({"ranked": []})
