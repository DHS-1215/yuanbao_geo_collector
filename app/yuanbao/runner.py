from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.result import (
    YuanbaoCollectionResult,
    utc_now_iso,
)
from app.yuanbao.types import (
    MODEL_MODE_COMPATIBILITY,
    YuanbaoMode,
    YuanbaoModel,
)

from app.yuanbao.geo_contract import (
    build_task_id,
    to_geo_mode,
)
from app.yuanbao.checkpoint import (
    YuanbaoCheckpointStore,
)
from app.yuanbao.screenshot import (
    capture_yuanbao_screenshot,
)


@dataclass(frozen=True)
class YuanbaoQuestion:
    question_id: str
    question: str


@dataclass
class YuanbaoTask:
    question_id: str
    question: str
    model: YuanbaoModel
    mode: YuanbaoMode
    task_id: str = ""


def build_geo_tasks(
        questions: list[YuanbaoQuestion],
        model: YuanbaoModel = YuanbaoModel.HY3,
        modes: tuple[YuanbaoMode, ...] = (
                YuanbaoMode.QUICK,
                YuanbaoMode.EXPERT,
        ),
) -> list[YuanbaoTask]:
    tasks: list[YuanbaoTask] = []

    supported_modes = (
        MODEL_MODE_COMPATIBILITY[model]
    )

    for mode in modes:
        # 同时验证：
        # 1. 是否属于 GEO v1 正式模式
        # 2. 当前模型是否支持该模式
        to_geo_mode(mode)

        if mode not in supported_modes:
            raise ValueError(
                "腾讯元宝不支持该模型/模式组合："
                f"{model.value} + {mode.value}"
            )

    for question in questions:
        for mode in modes:
            tasks.append(
                YuanbaoTask(
                    question_id=question.question_id,
                    question=question.question,
                    model=model,
                    mode=mode,
                )
            )

    return tasks


class YuanbaoSessionRotate(
        RuntimeError
):
    """Current Chrome session reached rotation boundary."""


class YuanbaoBatchRunner:

    def __init__(
            self,
            client: YuanbaoClient,
            batch_id: str,
            product: str,
            checkpoint_store: (
                    YuanbaoCheckpointStore
                    | None
            ) = None,
    ):
        self.client = client
        self.config = client.config
        self.batch_id = batch_id
        self.product = product

        self.checkpoint_store = (
            checkpoint_store
        )

        self.started_at = ""
        self.finished_at = ""

        # Count only questions actually collected
        # in the current Chrome session.
        # Checkpoint-only skips do not count.
        self.session_questions_completed = 0

        self._session_touched_question_ids: set[
            str
        ] = set()

    def prepare_task_identity(
            self,
            task: YuanbaoTask,
    ) -> str:

        mode_code = to_geo_mode(
            task.mode
        )

        task.task_id = build_task_id(
            batch_id=self.batch_id,
            question_id=task.question_id,
            mode_code=mode_code,
        )

        return mode_code

    def run_task(
            self,
            task: YuanbaoTask,
    ) -> YuanbaoCollectionResult:

        mode_code = (
            self.prepare_task_identity(
                task
            )
        )

        result = self.client.collect(
            question=task.question,
            model=task.model,
            mode=task.mode,
        )

        result.question_id = (
            task.question_id
        )

        result.task_id = (
            task.task_id
        )

        result.mode_code = (
            mode_code
        )

        result.batch_id = (
            self.batch_id
        )

        result.product = (
            self.product
        )

        result.platform = "yuanbao"

        return result

    def run_task_with_retry(
            self,
            task: YuanbaoTask,
    ) -> YuanbaoCollectionResult:

        ordinary_retries_used = 0
        risk_retries_used = 0
        attempt = 0

        last_result: (
                YuanbaoCollectionResult
                | None
        ) = None

        while True:
            attempt += 1

            try:
                result = self.run_task(
                    task
                )

            except Exception as e:
                # 最后一层 runner 兜底。
                # KeyboardInterrupt 属于 BaseException，
                # 不会在这里被吞掉。
                mode_code = (
                    self.prepare_task_identity(
                        task
                    )
                )

                page = getattr(
                    self.client,
                    "page",
                    None,
                )

                conversation_url = getattr(
                    page,
                    "url",
                    "",
                )

                result = YuanbaoCollectionResult(
                    question=task.question,
                    answer="",
                    model=task.model.value,
                    mode=task.mode.value,
                    conversation_url=(
                        conversation_url
                    ),
                    sources=[],
                    status="failed",
                    error=(
                        "Runner 未捕获异常："
                        f"{e}"
                    ),
                    task_id=task.task_id,
                    question_id=(
                        task.question_id
                    ),
                    mode_code=mode_code,
                    batch_id=self.batch_id,
                    product=self.product,
                    platform="yuanbao",
                    acquisition_status="failed",
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

            last_result = result

            succeeded = (
                    result.status == "success"
                    and result.is_complete
            )

            if succeeded:
                if attempt > 1:
                    print(
                        f"[RETRY] 第 {attempt} "
                        "次尝试成功"
                    )

                return result

            error_message = (
                    result.error
                    or "采集结果不完整"
            )

            is_quota_exhausted = (
                    result.acquisition_status
                    == "quota_exhausted"
            )

            if is_quota_exhausted:
                print()
                print(
                    "=" * 60
                )
                print(
                    "[ACCOUNT SWITCH REQUIRED]"
                )
                print()
                print(
                    "检测到当前腾讯元宝账号"
                    "额度 / 使用次数已耗尽。"
                )
                print()
                print(
                    "请在当前 Chrome 中人工操作："
                )
                print(
                    "1. 退出当前腾讯元宝账号"
                )
                print(
                    "2. 登录新的可用账号"
                )
                print(
                    "3. 确认腾讯元宝页面可以正常使用"
                )
                print()
                print(
                    "完成后回到此窗口："
                )
                print(
                    "输入 R  → 检查并重新执行当前任务"
                )
                print(
                    "输入 Q  → 退出程序并保留 Checkpoint"
                )
                print(
                    "=" * 60
                )

                while True:
                    try:
                        choice = input(
                            "\n[ACCOUNT SWITCH] "
                            "请输入 R 或 Q："
                        ).strip().upper()

                    except EOFError:
                        choice = "Q"

                    if choice == "Q":
                        print()
                        print(
                            "[ACCOUNT SWITCH] "
                            "用户选择退出。"
                        )
                        print(
                            "[CHECKPOINT] "
                            "当前批次将保留，"
                            "下次启动可继续。"
                        )

                        # run() 外层已经会对
                        # BaseException / SystemExit
                        # 做 interrupted 收尾。
                        raise SystemExit(2)

                    if choice != "R":
                        print(
                            "[ACCOUNT SWITCH] "
                            "无效输入，请输入 R 或 Q"
                        )
                        continue

                    readiness = getattr(
                        self.client,
                        "is_ready_after_account_switch",
                        None,
                    )

                    if readiness is not None:
                        try:
                            ready = bool(
                                readiness()
                            )

                        except Exception as e:
                            print(
                                "[ACCOUNT SWITCH] "
                                "页面恢复检查异常："
                                f"{e}"
                            )

                            ready = False

                        if not ready:
                            print()
                            print(
                                "[ACCOUNT SWITCH] "
                                "当前页面尚未恢复。"
                            )
                            print(
                                "请完成账号登录，"
                                "然后再次输入 R。"
                            )

                            continue

                    print()
                    print(
                        "[ACCOUNT SWITCH] "
                        "页面已恢复。"
                    )
                    print(
                        "[ACCOUNT SWITCH] "
                        "重新执行当前任务..."
                    )

                    # 新账号重新开始时，
                    # 清空当前任务此前消耗的
                    # 普通重试 / 风控重试额度。
                    ordinary_retries_used = 0
                    risk_retries_used = 0

                    break

                # 回到 while True 顶部，
                # 重新 run_task(task)。
                continue

            is_risk_control = (
                    result.acquisition_status
                    == "risk_control"
            )

            if is_risk_control:
                print(
                    "[RISK CONTROL] "
                    f"检测到风控：{error_message}"
                )

                max_risk_retries = max(
                    0,
                    getattr(
                        self.config,
                        "risk_control_retry_max",
                        1,
                    ),
                )

                if (
                        risk_retries_used
                        >= max_risk_retries
                ):
                    print(
                        "[RISK CONTROL] "
                        "已达到最大恢复次数，"
                        "停止继续撞击页面"
                    )

                    return result

                risk_retries_used += 1

                delay = random.uniform(
                    getattr(
                        self.config,
                        "risk_control_delay_min",
                        60.0,
                    ),
                    getattr(
                        self.config,
                        "risk_control_delay_max",
                        120.0,
                    ),
                )

                print(
                    "[RISK CONTROL] "
                    f"进入冷却 {delay:.1f}s"
                )

                print(
                    "[RISK CONTROL] "
                    f"冷却后进行第 "
                    f"{risk_retries_used}/"
                    f"{max_risk_retries} "
                    "次恢复尝试"
                )

                time.sleep(
                    delay
                )

                recovery = getattr(
                    self.client,
                    "recover_after_risk_control",
                    None,
                )

                if recovery is not None:
                    try:
                        recovered = bool(
                            recovery()
                        )

                    except Exception as e:
                        print(
                            "[RISK CONTROL] "
                            "页面恢复检查异常："
                            f"{e}"
                        )

                        recovered = False

                    if not recovered:
                        print(
                            "[RISK CONTROL] "
                            "页面仍未恢复，"
                            "停止当前任务继续请求"
                        )

                        return result

                    print(
                        "[RISK CONTROL] "
                        "页面状态已恢复，"
                        "准备重新执行当前任务"
                    )

                continue

            print(
                f"[RETRY] 第 {attempt} "
                f"次尝试失败："
                f"{error_message}"
            )

            max_ordinary_retries = max(
                0,
                self.config.task_retry_max,
            )

            if (
                    ordinary_retries_used
                    >= max_ordinary_retries
            ):
                print(
                    "[RETRY] "
                    "已达到最大普通重试次数，"
                    "当前任务保留为 failed"
                )

                return result

            ordinary_retries_used += 1

            delay = random.uniform(
                self.config.task_retry_delay_min,
                self.config.task_retry_delay_max,
            )

            print(
                f"[RETRY] 等待 "
                f"{delay:.1f}s 后重试"
            )

            print(
                f"[RETRY] 准备进行第 "
                f"{ordinary_retries_used}/"
                f"{max_ordinary_retries} "
                "次普通重试"
            )

            time.sleep(
                delay
            )

        assert last_result is not None

    def _capture_task_screenshot(
            self,
            task: YuanbaoTask,
            result: YuanbaoCollectionResult,
    ) -> None:
        page = getattr(
            self.client,
            "page",
            None,
        )

        # Lightweight fake clients used by unit tests
        # may expose a page-like object without
        # Playwright screenshot support.
        screenshot_method = getattr(
            page,
            "screenshot",
            None,
        )

        if not callable(
                screenshot_method
        ):
            return

        output_path = (
                Path("output")
                / "screenshots"
                / self.batch_id
                / f"{task.task_id}.png"
        ).resolve()

        screenshot = (
            capture_yuanbao_screenshot(
                page,
                output_path,
            )
        )

        result.screenshot_path = str(
            screenshot.path.resolve()
        )

        result.screenshot_sha256 = (
            screenshot.sha256
        )

        result.screenshot_size_bytes = (
            screenshot.size_bytes
        )

        result.screenshot_width = (
            screenshot.width
        )

        result.screenshot_height = (
            screenshot.height
        )

        print(
            "[SCREENSHOT]",
            result.screenshot_path,
        )

    def _maybe_rotate_session(
            self,
            *,
            tasks: list[YuanbaoTask],
            index: int,
            task: YuanbaoTask,
            results: list[
                YuanbaoCollectionResult
            ],
    ) -> None:
        limit = max(
            0,
            int(
                getattr(
                    self.config,
                    "questions_per_session",
                    0,
                )
            ),
        )

        if limit <= 0:
            return

        # quick / expert tasks for one question
        # are adjacent. Only evaluate the boundary
        # after the final task of that question.
        is_last_task_for_question = (
                index == len(tasks) - 1
                or
                tasks[index + 1].question_id
                != task.question_id
        )

        if not is_last_task_for_question:
            return

        # A question fully loaded from Checkpoint
        # does not consume the current session quota.
        if (
                task.question_id
                not in
                self._session_touched_question_ids
        ):
            return

        question_results = [
            result
            for result in results
            if (
                    result.question_id
                    == task.question_id
            )
        ]

        question_complete = (
                bool(question_results)
                and
                all(
                    result.status == "success"
                    and result.is_complete
                    for result in question_results
                )
        )

        if not question_complete:
            return

        self.session_questions_completed += 1

        self._session_touched_question_ids.discard(
            task.question_id
        )

        print(
            "[SESSION] "
            "Completed questions in this session: "
            f"{self.session_questions_completed}/"
            f"{limit}"
        )

        if (
                self.session_questions_completed
                < limit
        ):
            return

        # If this is already the final task in the batch,
        # complete normally instead of opening an empty
        # extra Chrome session.
        if index >= len(tasks) - 1:
            return

        print()
        print("=" * 60)
        print("[SESSION ROTATE REQUIRED]")
        print(
            f"Current Chrome session completed "
            f"{limit} full questions."
        )
        print(
            "Checkpoint has been saved."
        )
        print(
            "A new Chrome session is required."
        )
        print("=" * 60)

        raise YuanbaoSessionRotate(
            f"Session completed {limit} full questions"
        )

    def run(
            self,
            tasks: list[YuanbaoTask],
    ) -> list[YuanbaoCollectionResult]:

        results: list[
            YuanbaoCollectionResult
        ] = []

        self.session_questions_completed = 0
        self._session_touched_question_ids.clear()

        if self.checkpoint_store:
            self.started_at = (
                self.checkpoint_store
                .initialize(
                    product=self.product,
                    planned_count=len(tasks),
                )
            )

        else:
            self.started_at = (
                utc_now_iso()
            )

        try:
            for index, task in enumerate(
                    tasks
            ):
                print(
                    "=" * 80
                )

                print(
                    f"[TASK "
                    f"{index + 1}/"
                    f"{len(tasks)}]"
                )

                print(
                    task.question
                )

                self.prepare_task_identity(
                    task
                )

                cached_result = None

                if self.checkpoint_store:
                    cached_result = (
                        self.checkpoint_store
                        .load_result(
                            task.task_id
                        )
                    )

                if (
                        cached_result
                        is not None
                        and
                        cached_result.status
                        == "success"
                        and
                        cached_result.is_complete
                ):
                    print(
                        "[CHECKPOINT] "
                        "已有成功结果，跳过"
                    )

                    print(
                        f"STATUS: "
                        f"{cached_result.status}"
                    )

                    results.append(
                        cached_result
                    )

                    self._maybe_rotate_session(
                        tasks=tasks,
                        index=index,
                        task=task,
                        results=results,
                    )

                    continue

                result = (
                    self.run_task_with_retry(
                        task
                    )
                )

                if (
                        result.status == "success"
                        and result.is_complete
                ):
                    try:
                        self._capture_task_screenshot(
                            task,
                            result,
                        )

                    except Exception as exc:
                        result.status = "failed"

                        result.error = (
                            "Screenshot capture failed: "
                            f"{exc}"
                        )

                        result.validation_status = (
                            "SCREENSHOT_FAILED"
                        )

                        result.is_complete = False

                        print(
                            "[SCREENSHOT ERROR]",
                            str(exc),
                        )

                results.append(
                    result
                )

                if self.checkpoint_store:
                    self.checkpoint_store.save_result(
                        result
                    )

                    print(
                        "[CHECKPOINT] "
                        "结果已保存"
                    )

                print(
                    f"STATUS: {result.status}"
                )

                if (
                        result.status == "failed"
                        and result.error
                ):
                    print(
                        f"ERROR: {result.error}"
                    )

                if (
                        result.status == "success"
                        and result.is_complete
                ):
                    (
                        self
                        ._session_touched_question_ids
                        .add(
                            task.question_id
                        )
                    )

                self._maybe_rotate_session(
                    tasks=tasks,
                    index=index,
                    task=task,
                    results=results,
                )

                if index < len(tasks) - 1:
                    time.sleep(
                        random.uniform(
                            self.config.task_delay_min,
                            self.config.task_delay_max,
                        )
                    )

            self.finished_at = (
                utc_now_iso()
            )

            if self.checkpoint_store:
                self.checkpoint_store.mark_completed(
                    results=results,
                    finished_at=(
                        self.finished_at
                    ),
                )

            return results

        except BaseException:
            self.finished_at = (
                utc_now_iso()
            )

            if self.checkpoint_store:
                (
                    self.checkpoint_store
                    .mark_interrupted(
                        finished_at=(
                            self.finished_at
                        )
                    )
                )

            raise
