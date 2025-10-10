from typing import Type
from .tool_interface import Tool


class ToolFactory:
    """
    Factory for registering and creating tool instances.
    """
    _registry = {}

    @classmethod
    def register_tool(cls, tool_cls: Type[Tool]):
        cls._registry[tool_cls.__name__] = tool_cls
        return tool_cls

    @classmethod
    def create_tool(cls, name: str, *args, **kwargs) -> Tool:
        if name not in cls._registry:
            raise ValueError(f"Tool '{name}' is not registered.")
        return cls._registry[name](*args, **kwargs)

    @classmethod
    def list_tools(cls):
        return list(cls._registry.keys())
