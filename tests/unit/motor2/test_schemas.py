from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.motor2.schemas import MatchmakingRequest


def test_request_accepts_limit() -> None:
    request = MatchmakingRequest.model_validate(
        {"funcionario_ausente_id": str(uuid4()), "limit": 3}
    )

    assert request.limit == 3


def test_request_keeps_limite_as_legacy_alias() -> None:
    request = MatchmakingRequest.model_validate(
        {"funcionario_ausente_id": str(uuid4()), "limite": 4}
    )

    assert request.limit == 4


def test_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        MatchmakingRequest.model_validate(
            {
                "funcionario_ausente_id": str(uuid4()),
                "limit": 2,
                "limti": 9,
            }
        )
