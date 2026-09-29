from app.yuanbao.quota import (
    is_yuanbao_quota_exhausted,
)


def test_quota_exhausted_exact_message():
    assert (
            is_yuanbao_quota_exhausted(
                "今日使用次数已达上限"
            )
            is True
    )


def test_quota_exhausted_with_retry_hint():
    assert (
            is_yuanbao_quota_exhausted(
                "抱歉，今日次数已达上限，请明日再试。"
            )
            is True
    )


def test_normal_answer_is_not_quota():
    assert (
            is_yuanbao_quota_exhausted(
                "鸿茅药酒属于药品，"
                "应根据说明书合理使用。"
            )
            is False
    )


def test_long_answer_with_quota_phrase_is_not_quota():
    text = (
            "这是一段正常回答。"
            * 100
            + "部分平台可能出现使用次数已达上限。"
    )

    assert (
            is_yuanbao_quota_exhausted(
                text
            )
            is False
    )
