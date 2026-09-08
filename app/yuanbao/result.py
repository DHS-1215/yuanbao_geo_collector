from dataclasses import dataclass, field

from app.yuanbao.source import YuanbaoSource


@dataclass
class YuanbaoCollectionResult:
    question: str

    answer: str

    model: str

    mode: str

    conversation_url: str

    sources: list[YuanbaoSource] = field(
        default_factory=list
    )

    status: str = "success"

    error: str = ""

    task_id: str = ""

    question_id: str = ""

    mode_code: str = ""

    batch_id: str = ""

    product: str = ""

    platform: str = "yuanbao"
