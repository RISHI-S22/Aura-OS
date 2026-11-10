from typing import List, Dict, Set

class DependencyGraph:
    """Validates and sequences DAG subtask dependencies."""
    def __init__(self):
        self.adj = {}

    def add_node(self, node_id: str, deps: List[str]):
        self.adj[node_id] = deps

    def topological_sort(self) -> List[str]:
        visited = set()
        order = []
        for node in self.adj:
            self._visit(node, visited, order)
        return order

    def _visit(self, node: str, visited: Set[str], order: List[str]):
        if node not in visited:
            visited.add(node)
            for dep in self.adj.get(node, []):
                self._visit(dep, visited, order)
            order.append(node)
