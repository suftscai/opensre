"""Tool registry for managing and discovering available SRE tools."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from opensre.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available SRE tools.

    Provides tool registration, discovery, and execution capabilities.
    Tools are registered by name and can be looked up or listed at runtime.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance in the registry.

        Args:
            tool: An instantiated BaseTool subclass to register.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        name = tool.name
        if name in self._tools:
            raise ValueError(
                f"Tool '{name}' is already registered. "
                "Use replace=True to override an existing tool."
            )
        logger.debug("Registering tool: %s", name)
        self._tools[name] = tool

    def register_class(self, tool_cls: Type[BaseTool], **kwargs) -> None:
        """Instantiate and register a tool class.

        Args:
            tool_cls: A BaseTool subclass (not instance) to instantiate.
            **kwargs: Additional keyword arguments passed to the tool constructor.
        """
        instance = tool_cls(**kwargs)
        self.register(instance)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry by name.

        Args:
            name: The tool name to remove.

        Raises:
            KeyError: If no tool with the given name exists.
        """
        if name not in self._tools:
            raise KeyError(f"No tool named '{name}' found in registry.")
        logger.debug("Unregistering tool: %s", name)
        del self._tools[name]

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name.

        Args:
            name: The registered name of the tool.

        Returns:
            The tool instance, or None if not found.
        """
        return self._tools.get(name)

    def list_available(self) -> List[str]:
        """Return names of all tools that report themselves as available.

        Returns:
            Sorted list of available tool names.
        """
        return sorted(
            name for name, tool in self._tools.items() if tool.is_available()
        )

    def list_all(self) -> List[str]:
        """Return names of all registered tools regardless of availability.

        Returns:
            Sorted list of all registered tool names.
        """
        return sorted(self._tools.keys())

    def run(self, name: str, **params) -> ToolResult:
        """Execute a registered tool by name.

        Args:
            name: The name of the tool to run.
            **params: Parameters forwarded to the tool's run method.

        Returns:
            ToolResult from the tool execution.

        Raises:
            KeyError: If the tool is not registered.
            RuntimeError: If the tool is not currently available.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' is not registered.")
        if not tool.is_available():
            raise RuntimeError(
                f"Tool '{name}' is registered but not available in the current environment."
            )
        logger.info("Running tool '%s' with params: %s", name, params)
        return tool.run(**params)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Module-level default registry instance
default_registry = ToolRegistry()
