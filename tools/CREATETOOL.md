# Contributing New Tools to SenpAI Main Agent

This guide explains how to add your own custom tools to the agent using the factory pattern.

## 1. Tool Structure
All user-contributed tools should be placed in the `senpai-main-agent/tools/libs/` directory as a separate Python file (e.g., `my_tool.py`).

## 2. Tool Interface
Each tool must inherit from the `Tool` base class and use the `@ToolFactory.register_tool` decorator. Example:

```python
from tools.tool_interface import Tool
from tools.tool_factory import ToolFactory

@ToolFactory.register_tool
class MyTool(Tool):
    @property
    def name(self):
        return "my_tool"

    @property
    def description(self):
        return "A short description of what this tool does."

    def run(self, arg1, arg2):
        # Tool logic here
        return f"Result: {arg1}, {arg2}"
```

## 3. Registration
The decorator automatically registers your tool with the factory. No manual registration is needed.

## 4. Usage in Agent
All registered tools are automatically discovered and made available to the agent. You do not need to modify the main agent code.

## 5. Testing Your Tool
You can create an instance for testing:

```python
from tools.tool_factory import ToolFactory
my_tool = ToolFactory.create_tool("MyTool")
print(my_tool.run("foo", "bar"))
```

## 6. Naming
- The class name (e.g., `MyTool`) must be unique.
- The `name` property is what the agent will use to refer to the tool.

## 7. Example
See `calculator_tool.py` and `zundamon_joke_tool.py` in `tools/libs/` for reference implementations.

---

For questions, open an issue or contact the maintainers.
