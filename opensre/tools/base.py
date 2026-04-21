"""Base tool interface for opensre integrations.

All tools must inherit from BaseTool and implement the required methods
as defined in .cursor/rules/tools.mdc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Encapsulates the result of a tool execution."""

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


class BaseTool(ABC):
    """Abstract base class for all opensre tools.

    Subclasses must implement:
        - my_tool_name (class attribute)
        - is_available()
        - extract_params()
        - run()

    Example::

        class MyTool(BaseTool):
            my_tool_name = "my_tool"

            def is_available(self) -> bool:
                return shutil.which("my_tool") is not None

            def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
                return {"target": raw["target"]}

            def run(self, params: dict[str, Any]) -> ToolResult:
                ...
    """

    #: Unique snake_case identifier for this tool (required by tools.mdc)
    my_tool_name: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "my_tool_name", ""):
            raise TypeError(
                f"{cls.__name__} must define a non-empty 'my_tool_name' class attribute"
            )

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the underlying tool/binary/service is reachable."""

    @abstractmethod
    def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Validate and extract typed parameters from a raw input dict.

        Args:
            raw: Unvalidated input from the caller or graph node.

        Returns:
            A cleaned parameter dict ready to pass to :meth:`run`.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """

    @abstractmethod
    def run(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            params: Validated parameters produced by :meth:`extract_params`.

        Returns:
            A :class:`ToolResult` describing the outcome.
        """

    def execute(self, raw: dict[str, Any]) -> ToolResult:
        """High-level entry point: validate availability, extract params, run.

        Args:
            raw: Raw input dict from the caller.

        Returns:
            A :class:`ToolResult`. On failure, ``success`` is False and
            ``error`` contains a human-readable message.
        """
        if not self.is_available():
            return ToolResult(
                success=False,
                error=f"Tool '{self.my_tool_name}' is not available in this environment",
            )
        try:
            params = self.extract_params(raw)
            return self.run(params)
        except ValueError as exc:
            # ValueError typically means bad input from the caller, so surface it clearly.
            return ToolResult(success=False, error=f"Parameter error: {exc}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=f"Unexpected error: {exc}")
