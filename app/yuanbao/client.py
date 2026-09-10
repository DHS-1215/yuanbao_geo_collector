from __future__ import annotations

import random
import time

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from .config import YuanbaoConfig

from app.yuanbao.selectors import (
    ANSWER_SELECTOR,
    INPUT_SELECTOR,
    MODEL_MENU_SELECTOR,
    MODEL_SWITCH_SELECTOR,
    MODE_OPTION_SELECTOR,
    NEW_CHAT_SELECTOR,
    QUESTION_SELECTOR,
    REFERENCE_CLOSE_SELECTOR,
    REFERENCE_DRAWER_SELECTOR,
    REFERENCE_ITEM_SELECTOR,
    SEND_SELECTOR,
    SOURCE_TOOL_SELECTOR,
)

from app.yuanbao.types import (
    MODEL_MODE_COMPATIBILITY,
    YuanbaoMode,
    YuanbaoModel,
)

from app.yuanbao.result import (
    YuanbaoCollectionResult,
    utc_now_iso,
)

from app.yuanbao.source import YuanbaoSource

from app.yuanbao.extractor import YuanbaoSourceExtractor

from app.yuanbao.risk_control import (
    find_risk_control_marker,
)

from app.yuanbao.selectors import (
    REFERENCE_CARD_SELECTOR,
    REFERENCE_CLOSE_SELECTOR,
    REFERENCE_DESC_SELECTOR,
    REFERENCE_DRAWER_SELECTOR,
    REFERENCE_ITEM_SELECTOR,
    REFERENCE_SOURCE_SELECTOR,
    REFERENCE_TITLE_SELECTOR,
    SOURCE_TOOL_SELECTOR,
)


class YuanbaoClient:
    def __init__(
            self,
            page: Page,
            answer_timeout_seconds: float = 60.0,
            config: YuanbaoConfig | None = None,
    ) -> None:
        self.page = page
        self.answer_timeout_seconds = answer_timeout_seconds
        self.config = config or YuanbaoConfig()

    def ask(self, question: str) -> str:
        question = question.strip()

        if not question:
            raise ValueError("question 不能为空")

        before_answer_count = self._answer_count()

        self._fill_question(question)
        self._send()

        answer = self._wait_for_new_answer_complete(
            before_answer_count=before_answer_count,
        )

        return answer

    def detect_risk_control(
            self,
            error_message: str = "",
    ) -> str | None:

        marker = find_risk_control_marker(
            error_message
        )

        if marker:
            return marker

        try:
            body_text = (
                self.page
                .locator("body")
                .inner_text(
                    timeout=1000
                )
            )

        except Exception:
            return None

        return find_risk_control_marker(
            body_text
        )

    def recover_after_risk_control(
            self,
    ) -> bool:
        """
        风控冷却结束后的页面恢复检查。

        这里只做正常页面恢复：
        1. 检查页面是否仍可用
        2. 清理残留菜单 / 信源抽屉
        3. 检查是否仍存在明确风控提示
        4. 检查输入框
        5. 必要时最多刷新页面一次

        不处理验证码，也不绕过平台限制。
        """

        if self.page.is_closed():
            return False

        # 先尽量清理残留 UI。
        try:
            self._close_sources()
        except Exception:
            pass

        try:
            self._close_profile_menu()
        except Exception:
            pass

        # 风控提示如果仍然存在，
        # 当前页面就不应该继续发送请求。
        risk_marker = (
            self.detect_risk_control()
        )

        if risk_marker:
            print(
                "[RISK CONTROL] "
                "冷却后页面仍存在风控提示："
                f"{risk_marker}"
            )

            return False

        if self._input_is_ready():
            return True

        print(
            "[RISK CONTROL] "
            "输入区域尚未恢复，"
            "尝试刷新页面一次"
        )

        try:
            self.page.reload(
                wait_until="domcontentloaded",
                timeout=10000,
            )

        except Exception as e:
            print(
                "[RISK CONTROL] "
                f"页面刷新失败：{e}"
            )

            return False

        try:
            self.page.wait_for_timeout(
                1000
            )

        except Exception:
            return False

        # 刷新后重新检查风控，
        # 避免页面虽然能打开，
        # 但仍然处于限制状态。
        risk_marker = (
            self.detect_risk_control()
        )

        if risk_marker:
            print(
                "[RISK CONTROL] "
                "页面刷新后仍存在风控提示："
                f"{risk_marker}"
            )

            return False

        return self._input_is_ready()

    def _input_is_ready(
            self,
    ) -> bool:

        try:
            editor = self.page.locator(
                INPUT_SELECTOR
            ).first

            if editor.count() == 0:
                return False

            return editor.is_visible()

        except Exception:
            return False

    def collect(
            self,
            question: str,
            model: YuanbaoModel,
            mode: YuanbaoMode,
    ) -> YuanbaoCollectionResult:

        try:
            self.new_chat()

            self.set_profile(
                model=model,
                mode=mode,
            )

            answer = self.ask(
                question
            )


        except Exception as e:

            error_message = str(e)

            risk_marker = (

                self.detect_risk_control(

                    error_message

                )

            )

            acquisition_status = (

                "risk_control"

                if risk_marker

                else "failed"

            )

            if risk_marker:

                risk_message = (

                    f"检测到腾讯元宝风控："

                    f"{risk_marker}"

                )

                if error_message:

                    error_message = (

                        f"{error_message} | "

                        f"{risk_message}"

                    )

                else:

                    error_message = (

                        risk_message

                    )

            return YuanbaoCollectionResult(

                question=question,

                answer="",

                model=model.value,

                mode=mode.value,

                conversation_url=self.page.url,

                sources=[],

                status="failed",

                error=error_message,

                acquisition_status=(

                    acquisition_status

                ),

                validation_status=(

                    "NOT_APPLICABLE"

                ),

                is_complete=False,

                source_collection_status=(

                    "failed"

                ),

                source_count_raw=0,

                collected_at=utc_now_iso(),

            )

        source_collection_status = "success"
        source_error = ""

        try:
            sources = self.get_sources()

        except Exception as e:
            sources = []
            source_collection_status = "failed"
            source_error = str(e)

        return YuanbaoCollectionResult(
            question=question,
            answer=answer,
            model=model.value,
            mode=mode.value,
            conversation_url=self.page.url,
            sources=sources,
            status="success",
            acquisition_status="success",
            validation_status="NOT_APPLICABLE",
            is_complete=bool(
                answer.strip()
            ),
            source_collection_status=(
                source_collection_status
            ),
            source_count_raw=len(
                sources
            ),
            source_error=source_error,
            collected_at=utc_now_iso(),
        )

    def _fill_question(
            self,
            question: str,
    ) -> None:

        self._close_profile_menu()

        editor = self.page.locator(
            INPUT_SELECTOR
        ).first

        editor.wait_for(
            state="visible",
            timeout=5000,
        )

        editor.click(
            force=True
        )

        editor.fill(
            question
        )

    def _send(self) -> None:
        send_button = self.page.locator(
            SEND_SELECTOR
        ).first

        send_button.wait_for(
            state="visible",
            timeout=5000,
        )

        send_button.click()
        self._random_action_delay()

    def _answer_count(self) -> int:
        return self.page.locator(
            ANSWER_SELECTOR
        ).count()

    def _wait_for_new_answer_complete(
            self,
            before_answer_count: int,
    ) -> str:
        deadline = (
                time.monotonic()
                + self.answer_timeout_seconds
        )

        clarification_handled = False

        while time.monotonic() < deadline:

            # 检测元宝动态澄清卡
            if not clarification_handled:
                skip_all = self.page.get_by_text(
                    "跳过所有",
                    exact=False,
                )

                for index in range(
                        skip_all.count()
                ):
                    item = skip_all.nth(index)

                    if not item.is_visible():
                        continue

                    print(
                        "[CLARIFICATION] 检测到澄清卡"
                    )

                    print(
                        "[CLARIFICATION] "
                        + item.inner_text().strip()
                    )

                    # 保留一次真实 DOM，方便后续排查
                    try:
                        html = item.evaluate(
                            "(el) => el.outerHTML"
                        )

                        parent_html = item.evaluate(
                            "(el) => "
                            "el.parentElement "
                            "? el.parentElement.outerHTML "
                            ": ''"
                        )

                        print(
                            f"[CLARIFICATION DOM] {html}"
                        )

                        print(
                            "[CLARIFICATION PARENT DOM] "
                            f"{parent_html}"
                        )

                    except Exception:
                        pass

                    # 自动跳过全部澄清问题
                    item.click(
                        force=True,
                        timeout=2000,
                    )

                    print(
                        "[CLARIFICATION] 已自动跳过"
                    )

                    clarification_handled = True

                    self.page.wait_for_timeout(
                        500
                    )

                    break

                if clarification_handled:
                    continue

            answers = self.page.locator(
                ANSWER_SELECTOR
            )

            current_count = answers.count()

            if current_count > before_answer_count:
                latest_answer = answers.last

                class_name = (
                        latest_answer.get_attribute(
                            "class"
                        )
                        or ""
                )

                # 澄清流程出现时，发送按钮可能暂时消失。
                send_button = self.page.locator(
                    SEND_SELECTOR
                ).first

                send_aria = None

                if send_button.count() > 0:
                    try:
                        send_aria = (
                            send_button.get_attribute(
                                "aria-label",
                                timeout=500,
                            )
                        )
                    except PlaywrightTimeoutError:
                        send_aria = None

                answer_done = (
                        "hyc-content-md-done"
                        in class_name
                )

                send_restored = (
                        send_aria == "发送"
                )

                if answer_done and send_restored:
                    text = (
                        latest_answer
                        .inner_text()
                        .strip()
                    )

                    if text:
                        return text

            self.page.wait_for_timeout(
                500
            )

        raise TimeoutError(
            "等待腾讯元宝回答完成超时"
        )

    def new_chat(self) -> None:
        new_chat_button = self.page.locator(
            NEW_CHAT_SELECTOR,
            has_text="新对话",
        ).first

        new_chat_button.wait_for(
            state="visible",
            timeout=5000,
        )

        new_chat_button.click()
        self._random_action_delay()
        deadline = time.monotonic() + 10.0

        while time.monotonic() < deadline:
            question_count = self.page.locator(
                QUESTION_SELECTOR
            ).count()

            answer_count = self.page.locator(
                ANSWER_SELECTOR
            ).count()

            editor = self.page.locator(
                INPUT_SELECTOR
            ).first

            editor_visible = (
                    editor.count() > 0
                    and editor.is_visible()
            )

            if (
                    question_count == 0
                    and answer_count == 0
                    and editor_visible
            ):
                return

            self.page.wait_for_timeout(200)

        raise TimeoutError(
            "等待腾讯元宝进入新对话超时"
        )

    def _open_main_menu(self) -> None:
        trigger = self.page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        trigger.wait_for(
            state="visible",
            timeout=5000,
        )

        if (
                trigger.get_attribute("aria-expanded")
                != "true"
        ):
            trigger.click()
            self.page.wait_for_timeout(200)

    def _open_model_menu(self) -> None:
        self._open_main_menu()

        entry = self.page.locator(
            MODEL_MENU_SELECTOR
        ).first

        entry.wait_for(
            state="visible",
            timeout=5000,
        )

        if (
                entry.get_attribute("aria-expanded")
                != "true"
        ):
            entry.click()
            self.page.wait_for_timeout(200)

    def _find_radio(
            self,
            name: str,
    ):
        radios = self.page.locator(
            MODE_OPTION_SELECTOR
        )

        for index in range(radios.count()):
            item = radios.nth(index)

            if not item.is_visible():
                continue

            text = item.inner_text().strip()

            if not text:
                continue

            first_line = (
                text.splitlines()[0].strip()
            )

            if first_line == name:
                return item

        return None

    def set_model(
            self,
            model: YuanbaoModel,
    ) -> None:
        self._open_model_menu()

        option = self._find_radio(
            model.value
        )

        if option is None:
            raise RuntimeError(
                f"没有找到腾讯元宝模型：{model.value}"
            )

        if (
                option.get_attribute("aria-checked")
                != "true"
        ):
            option.click()
            self.page.wait_for_timeout(400)

        self._open_model_menu()

        option = self._find_radio(
            model.value
        )

        if (
                option is None
                or option.get_attribute("aria-checked")
                != "true"
        ):
            raise RuntimeError(
                f"腾讯元宝模型切换失败：{model.value}"
            )

    def set_mode(
            self,
            mode: YuanbaoMode,
    ) -> None:
        self._open_main_menu()

        option = self._find_radio(
            mode.value
        )

        if option is None:
            raise RuntimeError(
                f"当前模型不支持模式：{mode.value}"
            )

        if (
                option.get_attribute("aria-checked")
                != "true"
        ):
            option.click()
            self.page.wait_for_timeout(400)

        self._open_main_menu()

        option = self._find_radio(
            mode.value
        )

        if (
                option is None
                or option.get_attribute("aria-checked")
                != "true"
        ):
            raise RuntimeError(
                f"腾讯元宝模式切换失败：{mode.value}"
            )

    def set_profile(
            self,
            model: YuanbaoModel,
            mode: YuanbaoMode,
    ) -> None:
        supported_modes = (
            MODEL_MODE_COMPATIBILITY[model]
        )

        if mode not in supported_modes:
            raise ValueError(
                "腾讯元宝不支持该模型/模式组合："
                f"{model.value} + {mode.value}"
            )

        try:
            # 模型切换可能自动修改模式
            self.set_model(model)

            # 最后显式固定最终模式
            self.set_mode(mode)

        finally:
            self._close_profile_menu()

    def _close_profile_menu(self) -> None:
        trigger = self.page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        for _ in range(3):
            expanded = trigger.get_attribute(
                "aria-expanded"
            )

            if expanded != "true":
                return

            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(150)

        if (
                trigger.get_attribute("aria-expanded")
                == "true"
        ):
            raise RuntimeError(
                "腾讯元宝模型/模式菜单关闭失败"
            )

    def _open_sources(self) -> bool:
        tools = self.page.locator(
            SOURCE_TOOL_SELECTOR
        )

        visible_tool = None

        for index in range(tools.count()):
            item = tools.nth(index)

            if item.is_visible():
                visible_tool = item
                break

        if visible_tool is None:
            return False

        visible_tool.click()

        drawer = self.page.locator(
            REFERENCE_DRAWER_SELECTOR
        ).first

        drawer.wait_for(
            state="visible",
            timeout=5000,
        )

        # Drawer 出现不代表引用卡片已经渲染完成。
        # 继续等待至少一条正式引用来源。
        first_item = self.page.locator(
            REFERENCE_ITEM_SELECTOR
        ).first

        first_item.wait_for(
            state="visible",
            timeout=5000,
        )

        return True

    def _close_sources(self) -> None:
        close_button = self.page.locator(
            REFERENCE_CLOSE_SELECTOR
        )

        if (
                close_button.count() > 0
                and close_button.first.is_visible()
        ):
            close_button.first.click()

            self.page.wait_for_timeout(200)

    def get_sources(
            self,
    ) -> list[YuanbaoSource]:
        opened = self._open_sources()

        if not opened:
            return []

        try:
            extractor = YuanbaoSourceExtractor(
                page=self.page,
            )

            return extractor.extract()

        finally:
            self._close_sources()

    def _random_action_delay(
            self,
    ):
        time.sleep(
            random.uniform(
                self.config.action_delay_min,
                self.config.action_delay_max,
            )
        )
