import pytest
from core.planning.dependency_graph import DependencyGraph

def test_valid_dag_order():
    g = DependencyGraph()
    g.add_node("task_1", [])
    g.add_node("task_2", ["task_1"])
    order = g.topological_sort()
    assert order.index("task_1") < order.index("task_2")

def test_cycle_detection():
    g = DependencyGraph()
    g.add_node("task_1", ["task_2"])
    g.add_node("task_2", ["task_1"])
    assert g.has_cycle() is True
    with pytest.raises(ValueError):
        g.topological_sort()