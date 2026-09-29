import pytest

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.loader import load_questions
from app.yuanbao.selectors import (
    ANSWER_SELECTOR,
    INPUT_SELECTOR,
    NEW_CHAT_SELECTOR,
    QUESTION_SELECTOR,
)


def test_load_questions_accepts_utf8_bom(
        tmp_path,
):
    path = (
        tmp_path
        / "questions.csv"
    )

    path.write_text(
        "id,question\n"
        "1,鸿茅药酒到底是药还是酒？\n",
        encoding="utf-8-sig",
    )

    questions = load_questions(
        path
    )

    assert len(questions) == 1

    assert (
        questions[0].question
        == "鸿茅药酒到底是药还是酒？"
    )

    assert questions[0].question_id


class FakeLocator:
    def __init__(
            self,
            *,
            count_value=0,
            visible=False,
            on_click=None,
    ):
        self._count_value = count_value
        self._visible = visible
        self._on_click = on_click

    @property
    def first(self):
        return self

    def count(self):
        return self._count_value

    def is_visible(self):
        return self._visible

    def click(self, **kwargs):
        if self._on_click:
            self._on_click()


class FakePage:
    def __init__(
            self,
            new_chat_label: str,
    ):
        self.new_chat_label = (
            new_chat_label
        )

        self.clicked = False

    def locator(
            self,
            selector,
            *,
            has_text=None,
    ):
        if (
                selector
                == NEW_CHAT_SELECTOR
        ):
            matched = (
                has_text
                == self.new_chat_label
            )

            return FakeLocator(
                count_value=(
                    1
                    if matched
                    else 0
                ),
                visible=matched,
                on_click=(
                    self._mark_clicked
                    if matched
                    else None
                ),
            )

        if selector in (
                QUESTION_SELECTOR,
                ANSWER_SELECTOR,
        ):
            return FakeLocator(
                count_value=0,
                visible=False,
            )

        if (
                selector
                == INPUT_SELECTOR
        ):
            return FakeLocator(
                count_value=1,
                visible=True,
            )

        return FakeLocator()

    def wait_for_timeout(
            self,
            milliseconds,
    ):
        return None

    def _mark_clicked(self):
        self.clicked = True


@pytest.mark.parametrize(
    "label",
    (
        "新建对话",
        "新对话",
    ),
)
def test_new_chat_accepts_both_labels(
        label,
):
    page = FakePage(
        new_chat_label=label,
    )

    client = YuanbaoClient(
        page=page,
    )

    client._random_action_delay = (
        lambda: None
    )

    client.new_chat()

    assert page.clicked is True


class FakeKeyboard:
    def __init__(self, page):
        self.page = page
        self.last_key = None

    def press(self, key):
        self.last_key = key

        if (
                key == "Escape"
                and self.page.dismiss_on_escape
        ):
            self.page.overlay_visible = False


class FakeOverlayItem:
    def __init__(self, page):
        self.page = page

    def is_visible(self):
        return self.page.overlay_visible


class FakeOverlayLocator:
    def __init__(self, page):
        self.page = page

    def count(self):
        return 1

    def nth(self, index):
        assert index == 0
        return FakeOverlayItem(
            self.page
        )


class FakeOverlayPage:
    def __init__(
            self,
            *,
            dismiss_on_escape=True,
    ):
        self.overlay_visible = True
        self.dismiss_on_escape = (
            dismiss_on_escape
        )
        self.keyboard = FakeKeyboard(
            self
        )

    def locator(self, selector):
        assert selector == ".hyc-login-v2"

        return FakeOverlayLocator(
            self
        )

    def wait_for_timeout(
            self,
            milliseconds,
    ):
        return None


def test_source_login_overlay_can_be_dismissed():
    page = FakeOverlayPage(
        dismiss_on_escape=True,
    )

    client = YuanbaoClient(
        page=page,
    )

    client._dismiss_login_overlay_for_sources()

    assert (
        page.keyboard.last_key
        == "Escape"
    )

    assert page.overlay_visible is False


def test_source_login_overlay_raises_if_still_visible():
    page = FakeOverlayPage(
        dismiss_on_escape=False,
    )

    client = YuanbaoClient(
        page=page,
    )

    with pytest.raises(
            RuntimeError,
            match="登录弹窗仍在遮挡来源入口",
    ):
        client._dismiss_login_overlay_for_sources()
