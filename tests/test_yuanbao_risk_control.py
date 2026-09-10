from app.yuanbao.risk_control import (
    find_risk_control_marker,
)


def test_detect_frequency_risk_control():
    marker = find_risk_control_marker(
        "当前访问过于频繁，请稍后操作"
    )

    assert marker == "访问过于频繁"


def test_detect_security_verification():
    marker = find_risk_control_marker(
        "请完成安全验证后继续使用"
    )

    assert marker == "请完成安全验证"


def test_generic_retry_message_is_not_risk():
    marker = find_risk_control_marker(
        "服务繁忙，请稍后再试"
    )

    assert marker is None
