from core.tools.tool_interface import Tool
from core.tools.tool_factory import ToolFactory
import math
import operator

@ToolFactory.register_tool
class CalculatorTool(Tool):
    
    def __init__(self):
        """Initialize the CalculatorTool."""
        super().__init__()
    
    @property
    def name(self):
        return "calculator"

    @property
    def description(self):
        return "数式の計算結果を返す (例: '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)')"

    def run(self, expression: str) -> str:
        try:
            safe_dict = {
                "__builtins__": {},
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow,
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "log": math.log, "log10": math.log10, "exp": math.exp,
                "pi": math.pi, "e": math.e,
                "ceil": math.ceil, "floor": math.floor,
                "degrees": math.degrees, "radians": math.radians,
                "add": operator.add, "sub": operator.sub,
                "mul": operator.mul, "truediv": operator.truediv,
            }
            result = eval(expression, safe_dict)
            return str(result)
        except ZeroDivisionError:
            return "エラー: ゼロ除算"
        except ValueError as e:
            return f"エラー: 無効な値 - {str(e)}"
        except SyntaxError:
            return "エラー: 無効な数式"
        except Exception as e:
            return f"エラー: {str(e)}"
