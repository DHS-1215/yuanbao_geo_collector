from dataclasses import dataclass


@dataclass
class YuanbaoConfig:

    cdp_url: str = "http://127.0.0.1:9222"

    answer_timeout: int = 120

    action_delay_min: float = 1.0

    action_delay_max: float = 2.5

    task_delay_min: float = 3.0

    task_delay_max: float = 6.0