from app.yuanbao.client import (
    YuanbaoClient,
)


class FakeEditor:

    def __init__(
            self,
            page,
    ):
        self.page = page

    @property
    def first(self):
        return self

    def count(self):
        return 1

    def is_visible(self):
        return self.page.input_visible


class FakePage:

    def __init__(
            self,
            input_visible=True,
    ):
        self.input_visible = (
            input_visible
        )

        self.closed = False
        self.reload_calls = 0

    def is_closed(self):
        return self.closed

    def locator(
            self,
            selector,
    ):
        return FakeEditor(
            self
        )

    def reload(
            self,
            wait_until=None,
            timeout=None,
    ):
        self.reload_calls += 1

        # 模拟刷新后输入框恢复。
        self.input_visible = True

    def wait_for_timeout(
            self,
            timeout,
    ):
        pass


def build_client(
        page,
):
    client = YuanbaoClient(
        page=page
    )

    # 这些测试只验证恢复编排，
    # 不测试真实 DOM 菜单关闭。
    client._close_sources = (
        lambda: None
    )

    client._close_profile_menu = (
        lambda: None
    )

    return client


def test_ready_page_needs_no_reload():
    page = FakePage(
        input_visible=True
    )

    client = build_client(
        page
    )

    client.detect_risk_control = (
        lambda error_message="": None
    )

    assert (
            client.recover_after_risk_control()
            is True
    )

    assert page.reload_calls == 0


def test_page_can_recover_after_reload():
    page = FakePage(
        input_visible=False
    )

    client = build_client(
        page
    )

    client.detect_risk_control = (
        lambda error_message="": None
    )

    assert (
            client.recover_after_risk_control()
            is True
    )

    assert page.reload_calls == 1


def test_existing_risk_control_stops_recovery():
    page = FakePage(
        input_visible=True
    )

    client = build_client(
        page
    )

    client.detect_risk_control = (
        lambda error_message="":
        "访问过于频繁"
    )

    assert (
            client.recover_after_risk_control()
            is False
    )

    assert page.reload_calls == 0


def test_closed_page_cannot_recover():
    page = FakePage()

    page.closed = True

    client = build_client(
        page
    )

    assert (
            client.recover_after_risk_control()
            is False
    )
