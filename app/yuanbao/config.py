from dataclasses import dataclass


@dataclass
class YuanbaoConfig:
    cdp_url: str = "http://127.0.0.1:9222"

    answer_timeout: int = 120

    action_delay_min: float = 1.0

    action_delay_max: float = 2.5

    task_delay_min: float = 3.0

    task_delay_max: float = 6.0

    # 单任务普通失败自动重试次数。
    # 2 表示首次执行失败后，
    # 最多再重试 2 次，总计最多 3 次尝试。
    task_retry_max: int = 2

    task_retry_delay_min: float = 4.0

    task_retry_delay_max: float = 8.0

    # 明确检测到风控后，不进行短间隔普通重试。
    # 默认冷却 60~120 秒，只恢复尝试 1 次。
    risk_control_retry_max: int = 1

    risk_control_delay_min: float = 60.0

    risk_control_delay_max: float = 120.0
