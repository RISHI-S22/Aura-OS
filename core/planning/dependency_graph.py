from typing import Dict, List, Set

class DependencyGraph:
    """Validates and sequences DAG subtask dependencies with cycle detection."""

    def __init__(self):
        self.adj: Dict[str, List[str]] = {}

    def add_node(self, node_id: str, deps: List[str]):
        self.adj[node_id] = deps

    def has_cycle(self) -> bool:
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.adj.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in list(self.adj.keys()):
            if node not in visited and dfs(node):
                return True
        return False

    def topological_sort(self) -> List[str]:
        if self.has_cycle():
            raise ValueError("Cyclic dependency detected in task graph")
        visited: Set[str] = set()
        order: List[str] = []

        def visit(node: str):
            if node not in visited:
                visited.add(node)
                for dep in self.adj.get(node, []):
                    visit(dep)
                order.append(node)

        for node in self.adj:
            visit(node)
        return order