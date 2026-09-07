from enum import StrEnum
from dataclasses import dataclass, field


class YuanbaoMode(StrEnum):
    QUICK = "快速回答"
    THINKING = "深度思考"
    EXPERT = "专家模式"


class YuanbaoModel(StrEnum):
    HY3 = "Hy3"
    DEEPSEEK = "DeepSeek"
    HY4_PREVIEW = "Hy4 preview"


MODEL_MODE_COMPATIBILITY = {
    YuanbaoModel.HY3: {
        YuanbaoMode.QUICK,
        YuanbaoMode.THINKING,
        YuanbaoMode.EXPERT,
    },
    YuanbaoModel.DEEPSEEK: {
        YuanbaoMode.QUICK,
        YuanbaoMode.THINKING,
    },
    YuanbaoModel.HY4_PREVIEW: {
        YuanbaoMode.EXPERT,
    },
}


@dataclass
class YuanbaoSource:
    title: str = ""
    url: str = ""
    domain: str = ""


@dataclass
class YuanbaoResult:
    question: str

    answer: str

    model: str

    mode: str

    url: str

    sources: list[YuanbaoSource] = field(default_factory=list)

    status: str = "success"

    error: str = ""
