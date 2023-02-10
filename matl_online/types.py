from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class MATLFlags(Enum):
    EXPLAIN = "e"
    RUN = "r"
    ONLINE = "o"


MATL_DEFAULT_FLAGS: List[MATLFlags] = [
    MATLFlags.ONLINE,
]


@dataclass(frozen=True)
class MATLTaskParameters:
    code: str
    version: str
    inputs: str = ""
    session_id: Optional[str] = None

    @property
    def code_lines(self) -> List[str]:
        return self.code.split("\n")

    @property
    def input_lines(self) -> List[str]:
        if len(self.inputs) == 0:
            return []

        return self.inputs.split("\n")

    @property
    def additional_flags(self) -> List[MATLFlags]:
        return []

    @property
    def flags(self) -> str:
        all_flags = MATL_DEFAULT_FLAGS + self.additional_flags
        return "-" + "".join([flag.value for flag in all_flags])


@dataclass(frozen=True)
class MATLRunTaskParameters(MATLTaskParameters):
    @property
    def additional_flags(self) -> List[MATLFlags]:
        return [
            MATLFlags.RUN,
        ]


@dataclass(frozen=True)
class MATLExplainTaskParameters(MATLTaskParameters):
    @property
    def additional_flags(self) -> List[MATLFlags]:
        return [
            MATLFlags.EXPLAIN,
        ]
