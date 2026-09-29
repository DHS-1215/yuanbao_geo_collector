from __future__ import annotations

import re


MAX_QUOTA_MESSAGE_LENGTH = 300


# 第一版使用通用额度提示。
# 后续真实遇到腾讯元宝自己的提示文案时，
# 只需要继续补充这里，不需要修改整体架构。
_PROVISIONAL_QUOTA_PATTERNS = (
    r"今日使用次数已达上限",
    r"今日次数已达上限",
    r"今日次数已用完",
    r"使用次数已达上限",
    r"已达到使用上限",
    r"本次服务次数已用完",
    r"暂无可用次数",
    r"当前账号暂无可用次数",
    r"当前账号使用次数已达上限",
    r"今日可用次数已用完",
)


def normalize_quota_text(
        text: str,
) -> str:
    return " ".join(
        text.strip().split()
    )


def is_yuanbao_quota_exhausted(
        answer: str,
) -> bool:
    normalized = normalize_quota_text(
        answer
    )

    if not normalized:
        return False

    # 防止正常长回答里提到
    # “使用次数已达上限”时被误判。
    if (
            len(normalized)
            > MAX_QUOTA_MESSAGE_LENGTH
    ):
        return False

    phrase_group = "|".join(
        _PROVISIONAL_QUOTA_PATTERNS
    )

    pattern = (
        rf"^(?:抱歉[，, ]*)?"
        rf"(?:{phrase_group})"
        rf"(?:[，,。.!！ ]*"
        rf"(?:请稍后再试|请稍后重试|请明日再试)?"
        rf"[。.!！ ]*)?$"
    )

    return (
        re.fullmatch(
            pattern,
            normalized,
        )
        is not None
    )