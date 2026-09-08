from __future__ import annotations

import hashlib

from app.yuanbao.types import YuanbaoMode

GEO_SCHEMA_VERSION = "geo_package_v1"
GEO_BATCH_VERSION = "geo_batch_v1"

YUANBAO_PLATFORM_CODE = "yuanbao"
YUANBAO_PLATFORM_NAME = "腾讯元宝"

DEFAULT_PRODUCT_ID = "hongmao_yaojiu"
DEFAULT_PRODUCT_NAME = "鸿茅药酒"

COLLECTOR_VERSION = "0.1.0"


def to_geo_mode(mode: YuanbaoMode) -> str:
    if mode == YuanbaoMode.QUICK:
        return "quick"

    if mode == YuanbaoMode.EXPERT:
        return "expert"

    if mode == YuanbaoMode.THINKING:
        raise ValueError(
            "腾讯元宝“深度思考”暂不纳入 GEO v1 标准模式"
        )

    raise ValueError(
        f"未知腾讯元宝模式：{mode}"
    )


def normalize_question_text(text: str) -> str:
    return (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def _stable_hash(
        *parts: object,
        length: int = 24,
) -> str:
    payload = "\n".join(
        str(part)
        for part in parts
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:length]


def build_question_id(
        csv_id: str,
        question: str,
) -> str:
    normalized_question = normalize_question_text(
        question
    )

    question_hash = _stable_hash(
        normalized_question,
        length=12,
    )

    return (
        f"ybq_{csv_id.strip()}_"
        f"{question_hash}"
    )


def build_task_id(
        batch_id: str,
        question_id: str,
        mode_code: str,
) -> str:
    digest = _stable_hash(
        YUANBAO_PLATFORM_CODE,
        batch_id,
        question_id,
        mode_code,
    )

    return f"yb_t_{digest}"


def build_answer_id(
        batch_id: str,
        task_id: str,
) -> str:
    digest = _stable_hash(
        YUANBAO_PLATFORM_CODE,
        batch_id,
        task_id,
    )

    return f"yb_a_{digest}"


def build_occurrence_id(
        batch_id: str,
        answer_id: str,
        source_order: int,
        source_url_raw: str,
) -> str:
    digest = _stable_hash(
        YUANBAO_PLATFORM_CODE,
        batch_id,
        answer_id,
        source_order,
        source_url_raw.strip(),
    )

    return f"yb_s_{digest}"
