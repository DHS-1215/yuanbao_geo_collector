from dataclasses import dataclass


@dataclass(frozen=True)
class YuanbaoSource:
    index: int
    source: str
    title: str
    description: str
    url: str
    domain: str = ""