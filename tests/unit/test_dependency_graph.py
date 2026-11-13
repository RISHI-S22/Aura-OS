import pytest
from core.planning.dependency_graph import DependencyGraph

def test_topological_order():
    graph = DependencyGraph()
    graph.add_node("t1", [])
    graph.add_node("t2", ["t1"])
    graph.add_node("t3", ["t2"])
    assert graph.topological_sort() == ["t1", "t2", "t3"]

def test_cycle_raises_error():
    graph = DependencyGraph()
    graph.add_node("t1", ["t2"])
    graph.add_node("t2", ["t1"])
    with pytest.raises(ValueError):
        graph.topological_sort()