from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type


class MATLFlags(Enum):
    EXPLAIN = "e"
    RUN = "r"
    ONLINE = "o"


MATL_DEFAULT_FLAGS: List[MATLFlags] = [
    MATLFlags.ONLINE,
]


@dataclass(frozen=True)
class MATLTaskParameters:
    kind: ClassVar[str] = "default"

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict for passing to celery tasks."""
        return {"kind": self.kind, **asdict(self)}

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MATLTaskParameters":
        """Reconstruct the parameters produced by to_dict."""
        fields = dict(data)
        parameter_type = TASK_PARAMETER_TYPES[fields.pop("kind")]
        return parameter_type(**fields)


@dataclass(frozen=True)
class MATLRunTaskParameters(MATLTaskParameters):
    kind: ClassVar[str] = "run"

    @property
    def additional_flags(self) -> List[MATLFlags]:
        return [
            MATLFlags.RUN,
        ]


@dataclass(frozen=True)
class MATLExplainTaskParameters(MATLTaskParameters):
    kind: ClassVar[str] = "explain"

    @property
    def additional_flags(self) -> List[MATLFlags]:
        return [
            MATLFlags.EXPLAIN,
        ]


TASK_PARAMETER_TYPES: Dict[str, Type[MATLTaskParameters]] = {
    parameter_type.kind: parameter_type
    for parameter_type in (
        MATLTaskParameters,
        MATLRunTaskParameters,
        MATLExplainTaskParameters,
    )
}
