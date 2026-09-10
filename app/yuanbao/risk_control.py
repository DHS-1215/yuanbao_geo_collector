from __future__ import annotations

RISK_CONTROL_MARKERS = (
    "访问过于频繁",
    "操作过于频繁",
    "请求过于频繁",
    "请勿频繁操作",
    "检测到异常访问",
    "当前访问存在异常",
    "当前账号存在异常",
    "账号存在异常",
    "请完成安全验证",
    "完成安全验证后继续",
)


def find_risk_control_marker(
        text: str | None,
) -> str | None:
    if not text:
        return None

    normalized = "".join(
        str(text).split()
    )

    for marker in RISK_CONTROL_MARKERS:
        normalized_marker = "".join(
            marker.split()
        )

        if normalized_marker in normalized:
            return marker

    return None
