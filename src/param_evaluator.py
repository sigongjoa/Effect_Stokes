import math
import re
import sys

class ParamEvaluator:
    def __init__(self, allowed_functions=None, allowed_constants=None):
        self.allowed_functions = allowed_functions if allowed_functions is not None else {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "exp": math.exp, "log": math.log,
            "abs": abs, "min": min, "max": max,
            "pow": math.pow, # For t**2 or pow(t, 2)
        }
        self.allowed_constants = allowed_constants if allowed_constants is not None else {
            "pi": math.pi, "e": math.e,
        }

    def _is_safe_expression(self, expression):
        # First, check for dangerous keywords
        if any(keyword in expression for keyword in ['import', 'os', 'sys', 'subprocess', 'eval', 'exec', 'lambda', '__', 'getattr', 'setattr']):
            return False, f"Potentially dangerous keyword found in expression: {expression}"
        return True, None

    def evaluate(self, expression, t=0):
        if not isinstance(expression, str):
            return expression # Return as is if not a string (e.g., a fixed number)

        is_safe, error_msg = self._is_safe_expression(expression)
        if not is_safe:
            raise ValueError(f"Unsafe expression: {error_msg}")

        # Prepare the environment for evaluation
        env = {"t": t}
        env.update(self.allowed_functions)
        env.update(self.allowed_constants)

        try:
            # Use a limited global and local scope for safety
            # This is still using eval, but with a heavily restricted environment
            # The _is_safe_expression check is the primary line of defense.
            result = eval(expression, {"__builtins__": {}}, env)
            return result
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}' at t={t}: {e}")

# Example Usage:
if __name__ == "__main__":
    evaluator = ParamEvaluator()

    # Test cases for fixed values
    print(f"Fixed value 10: {evaluator.evaluate(10)}")
    print(f"Fixed value 0.5: {evaluator.evaluate(0.5)}")

    # Test cases for time-dependent expressions
    print(f"sin(t) at t=0: {evaluator.evaluate('sin(t)', t=0)}")
    print(f"sin(t) at t=pi/2: {evaluator.evaluate('sin(t)', t=math.pi/2)}")
    print(f"0.02 + 0.01 * sin(t * 0.1) at t=0: {evaluator.evaluate('0.02 + 0.01 * sin(t * 0.1)', t=0)}")
    print(f"0.02 + 0.01 * sin(t * 0.1) at t=10: {evaluator.evaluate('0.02 + 0.01 * sin(t * 0.1)', t=10)}")
    print(f"0.4 + 0.1 * (t / 60) at t=0: {evaluator.evaluate('0.4 + 0.1 * (t / 60)', t=0)}")
    print(f"0.4 + 0.1 * (t / 60) at t=30: {evaluator.evaluate('0.4 + 0.1 * (t / 60)', t=30)}")
    print(f"1.2 * exp(-t / 30) at t=0: {evaluator.evaluate('1.2 * exp(-t / 30)', t=0)}")
    print(f"1.2 * exp(-t / 30) at t=30: {evaluator.evaluate('1.2 * exp(-t / 30)', t=30)}")
    print(f"2.0 * (1 - (t / 60)) at t=0: {evaluator.evaluate('2.0 * (1 - (t / 60))', t=0)}")
    print(f"2.0 * (1 - (t / 60)) at t=60: {evaluator.evaluate('2.0 * (1 - (t / 60))', t=60)}")
    print(f"t**2 + pi at t=2: {evaluator.evaluate('t**2 + pi', t=2)}")
    print(f"pow(t, 3) at t=2: {evaluator.evaluate('pow(t, 3)', t=2)}")

    # Test cases for invalid/unsafe expressions
    try:
        evaluator.evaluate("import os; os.system('ls')")
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        evaluator.evaluate("2 + my_evil_function(t)")
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        evaluator.evaluate("2 + t / 0")
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        evaluator.evaluate("2 + t * (")
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        evaluator.evaluate("2 + t * [")
    except ValueError as e:
        print(f"Caught expected error: {e}")
