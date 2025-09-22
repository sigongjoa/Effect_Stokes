import pytest
from src.param_evaluator import ParamEvaluator
import math
import re

@pytest.fixture
def evaluator():
    return ParamEvaluator()

def test_fixed_values(evaluator):
    assert evaluator.evaluate(10) == 10
    assert evaluator.evaluate(0.5) == 0.5
    assert evaluator.evaluate("10") == 10
    assert evaluator.evaluate("0.5") == 0.5

def test_time_dependent_expressions(evaluator):
    # Test sin(t)
    assert evaluator.evaluate('sin(t)', t=0) == math.sin(0)
    assert evaluator.evaluate('sin(t)', t=math.pi/2) == pytest.approx(math.sin(math.pi/2))

    # Test complex expression
    expr = '0.02 + 0.01 * sin(t * 0.1)'
    assert evaluator.evaluate(expr, t=0) == pytest.approx(0.02 + 0.01 * math.sin(0 * 0.1))
    assert evaluator.evaluate(expr, t=10) == pytest.approx(0.02 + 0.01 * math.sin(10 * 0.1))

    # Test another complex expression
    expr2 = '0.4 + 0.1 * (t / 60)'
    assert evaluator.evaluate(expr2, t=0) == pytest.approx(0.4 + 0.1 * (0 / 60))
    assert evaluator.evaluate(expr2, t=30) == pytest.approx(0.4 + 0.1 * (30 / 60))

    # Test exp and t**2
    expr3 = '1.2 * exp(-t / 30)'
    assert evaluator.evaluate(expr3, t=0) == pytest.approx(1.2 * math.exp(-0 / 30))
    assert evaluator.evaluate(expr3, t=30) == pytest.approx(1.2 * math.exp(-30 / 30))
    assert evaluator.evaluate('t**2 + pi', t=2) == pytest.approx(2**2 + math.pi)
    assert evaluator.evaluate('pow(t, 3)', t=2) == pytest.approx(math.pow(2, 3))

def test_disallowed_keywords(evaluator):
    with pytest.raises(ValueError, match="Unsafe expression: Potentially dangerous keyword found in expression: import os"):
        evaluator.evaluate("import os; os.system('ls')")
    with pytest.raises(ValueError, match="Unsafe expression: Potentially dangerous keyword found in expression: __"):
        evaluator.evaluate("__import__('os')")

def test_invalid_mathematical_expressions(evaluator):
    with pytest.raises(ValueError, match=re.escape("Error evaluating expression '2 + t / 0' at t=0: division by zero")):
        evaluator.evaluate("2 + t / 0", t=0)
    with pytest.raises(ValueError, match=re.escape("Error evaluating expression '2 + t * (' at t=0: '(' was never closed (<string>, line 1)")):
        evaluator.evaluate("2 + t * (", t=0)
    with pytest.raises(ValueError, match=re.escape("Error evaluating expression '2 + t * [' at t=0: '[' was never closed (<string>, line 1)")):
        evaluator.evaluate("2 + t * [", t=0)

def test_unknown_function_or_constant(evaluator):
    with pytest.raises(ValueError, match=re.escape("Error evaluating expression '2 + my_evil_function(t)' at t=0: name 'my_evil_function' is not defined")):
        evaluator.evaluate("2 + my_evil_function(t)", t=0)
    with pytest.raises(ValueError, match=re.escape("Error evaluating expression '2 + unknown_const' at t=0: name 'unknown_const' is not defined")):
        evaluator.evaluate("2 + unknown_const", t=0)

def test_list_evaluation(evaluator):
    # ParamEvaluator is not designed to evaluate lists of expressions directly
    # It evaluates a single expression string.
    # This test ensures it returns non-string lists as is.
    assert evaluator.evaluate([1, 2, 3]) == [1, 2, 3]
    assert evaluator.evaluate(["sin(t)", 2, "cos(t)"], t=0) == ["sin(t)", 2, "cos(t)"]
