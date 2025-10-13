from abc import ABC, abstractmethod


class Tool(ABC):
    """
    Abstract base class for all tools. Contributors should inherit from this class
    and implement the required methods.
    """
    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Execute the tool's main logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the tool.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @property
    def description(self) -> str:
        """
        Optional: Return a description of the tool.
        """
        return ""

    def as_langchain_tool(self):
        """
        Return a langchain_core.tools.tool-wrapped function for this tool instance.
        Requires langchain_core.tools.tool to be installed/importable.
        """
        try:
            from langchain_core.tools import tool as lc_tool
        except ImportError:
            raise ImportError("langchain_core.tools.tool is required to use as_langchain_tool.")
        
        # Create a wrapper function with proper name and description
        def tool_func(*args, **kwargs):
            return self.run(*args, **kwargs)
        
        tool_func.__name__ = self.name
        tool_func.__doc__ = getattr(self, 'description', '')
        
        return lc_tool(tool_func)
