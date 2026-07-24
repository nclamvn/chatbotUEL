from app.models import ChatRequest


def test_chat_request_defaults_to_mock():
    req = ChatRequest(message="Điểm chuẩn 2025?")
    assert req.response_mode == "mock"


def test_chat_request_accepts_api_mode():
    req = ChatRequest(message="Điểm chuẩn 2025?", response_mode="api")
    assert req.response_mode == "api"
