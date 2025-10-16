from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Tool(ABC):
    """
    Abstract base class for all tools. Contributors should inherit from this class
    and implement the required methods.
    """
    _context: Dict[str, Any]= {}
    
    def __init__(self):
        """Initialize the tool with empty context."""
        self._context: Dict[str, Any] = {}
    
    @classmethod
    def set_context(cls, context: Dict[str, Any]) -> None:
        """
        Set context information for the tool.
        
        Args:
            context: Dictionary containing context information like memory_id, actor_id, session_id, etc.
        """
        cls._context.update(context)
    
    @classmethod
    def get_context(cls, key: str, default: Any = None) -> Any:
        """
        Get a value from the tool context.
        
        Args:
            key: The context key to retrieve
            default: Default value if key is not found
            
        Returns:
            The context value or default
        """
        return cls._context.get(key, default)
    
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
