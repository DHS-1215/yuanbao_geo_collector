from app.yuanbao.client import YuanbaoClient
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


def build_client_without_init():
    return object.__new__(
        YuanbaoClient
    )


def test_source_failure_does_not_fail_answer():
    client = build_client_without_init()

    client.page = type(
        "FakePage",
        (),
        {
            "url": "https://yuanbao.tencent.com/test"
        },
    )()

    client.new_chat = lambda: None

    client.set_profile = (
        lambda model, mode: None
    )

    client.ask = (
        lambda question: "这是一个完整回答"
    )

    def raise_source_error():
        raise RuntimeError(
            "来源面板打开失败"
        )

    client.get_sources = (
        raise_source_error
    )

    result = client.collect(
        question="测试问题",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )

    assert result.status == "success"
    assert result.acquisition_status == "success"

    assert result.answer == "这是一个完整回答"
    assert result.is_complete is True

    assert result.sources == []
    assert result.source_count_raw == 0
    assert result.source_collection_status == "failed"

    assert (
            "来源面板打开失败"
            in result.source_error
    )


def test_answer_failure_is_acquisition_failure():
    client = build_client_without_init()

    client.page = type(
        "FakePage",
        (),
        {
            "url": "https://yuanbao.tencent.com/test"
        },
    )()

    client.new_chat = lambda: None

    client.set_profile = (
        lambda model, mode: None
    )

    def raise_answer_error(question):
        raise RuntimeError(
            "回答等待超时"
        )

    client.ask = raise_answer_error

    result = client.collect(
        question="测试问题",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )

    assert result.status == "failed"
    assert result.acquisition_status == "failed"

    assert result.answer == ""
    assert result.is_complete is False

    assert result.sources == []
    assert result.source_count_raw == 0
    assert result.source_collection_status == "failed"

    assert "回答等待超时" in result.error


def test_empty_source_list_is_valid_source_result():
    client = build_client_without_init()

    client.page = type(
        "FakePage",
        (),
        {
            "url": "https://yuanbao.tencent.com/test"
        },
    )()

    client.new_chat = lambda: None

    client.set_profile = (
        lambda model, mode: None
    )

    client.ask = (
        lambda question: "正常回答"
    )

    client.get_sources = lambda: []

    result = client.collect(
        question="测试问题",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )

    assert result.acquisition_status == "success"
    assert result.is_complete is True

    assert result.source_collection_status == "success"
    assert result.source_count_raw == 0
    assert result.source_error == ""


def test_successful_sources_keep_answer_success():
    client = build_client_without_init()

    client.page = type(
        "FakePage",
        (),
        {
            "url": "https://yuanbao.tencent.com/test"
        },
    )()

    client.new_chat = lambda: None

    client.set_profile = (
        lambda model, mode: None
    )

    client.ask = (
        lambda question: "正常回答"
    )

    client.get_sources = lambda: [
        object(),
        object(),
    ]

    result = client.collect(
        question="测试问题",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )

    assert result.status == "success"
    assert result.acquisition_status == "success"
    assert result.is_complete is True

    assert result.source_collection_status == "success"
    assert result.source_count_raw == 2

    assert result.collected_at
