"""
This module implements a cell interaction graph class, used to keep track of all 
cells containing formulas within a workbook and their dependencies. This class 
is used by the evaluator to detect circular references and by the workbook to
update cells when their dependencies change.
"""
from collections import defaultdict
from typing import Tuple
from copy import deepcopy
from .regexp import replace_names

class CellInteractionGraph():
    """
    This class represents a graph of cells containing formulas and their
    dependencies. The graph maps strings of cell locations to lists of strings
    of cell locations. The graph is directed, and the edges represent
    dependencies.
    """

    def __init__(self):
        """
        Initializes a new cell interaction graph with no cells.
        """
        self.graph = {}

    def set_cell(self, cell: Tuple[str, str]) -> None:
        """
        Adds a cell to the graph. The cell should be a Formula Cell.
        """
        self.graph[cell] = []

    def add_dependency(self, cell: Tuple[str, str], dependency: Tuple[str, str]) -> None:
        """
        Adds a dependency to a cell in the graph. The cell should be a
        Formula Cell.
        """
        self.graph[cell].append(dependency)

    def remove_dependency(self, cell: Tuple[str, str], dependency: Tuple[str, str]) -> None:
        """
        Adds a dependency to a cell in the graph. The cell should be a
        Formula Cell.
        """
        self.graph[cell].remove(dependency)

    def remove_cell(self, cell: Tuple[str]) -> None:
        """
        Removes a cell from the graph. The cell should be a Formula Cell.
        Also needs to remove the cell from any other cells' dependencies.
        """
        self.graph.pop(cell)

    def get_dependencies(self, cell: Tuple[str, str]) -> list[str]:
        """
        Returns the dependencies of a cell in the graph. The cell should be a
        Formula Cell.
        """
        if cell not in self.graph:
            return []
        return self.graph[cell]

    def get_cells(self) -> list[Tuple[str, str]]:
        """
        Returns all formula cells in the graph.
        """
        return self.graph.keys()

    def tarjan(self) -> tuple[list[Tuple[str, str]], set[Tuple[str, str]]]:
        """
        Returns a topological ordering of the cells in the graph using Tarjan's
        algorithm for finding strongly connected components. Also returns a set
        of all cells that are part of a cycle.
        """
        ids = defaultdict(lambda : -1) #id of -1 -> never seen a node before
        lowlinks = defaultdict(int)
        on_stack = {}
        stack = []
        call_stack = []
        node_id = 0
        scc_count = 0
        scc_nodes = set()
        nodes_in_cycle = set() # track first nodes in topological order
        order = []
        for node in self.graph:
            if ids[node] == -1: #unvisited node
                call_stack.append([node, 0])
                while call_stack:
                    node, child_idx = call_stack.pop()
                    neighbors = self.get_dependencies(node)
                    num_neighbors = len(neighbors)
                    if child_idx == 0:#if the child index is 0, this is the
                                      #first time we are seeing this node
                        #add it to the stack
                        stack.append(node)
                        on_stack[node] = True
                        #assign the node an id
                        ids[node] = node_id
                        #we initialize the lowlink value as the node id
                        lowlinks[node] = node_id
                        #increment id
                        node_id += 1
                    elif child_idx > 0:
                        #if the child index is greater than 0, are backtracking
                        #from a previous recursion. Specifically, the child we
                        #just came back from was the child in the list at
                        #child_idx - 1, because in that recursive call, we
                        #incremented child_idx before pushing it onto the call
                        #stack.
                        child = neighbors[child_idx - 1]
                        #when we backtrack, we min lowlinks of the parent and
                        #child as per tarjans algo
                        lowlinks[node] = min(lowlinks[node],lowlinks[child])
                    while (child_idx < num_neighbors and
                           ids[neighbors[child_idx]] != -1):
                        #if the child is already on the stack, this is a loop, so
                        #min the curr lowlink of the node and the lowlink of the
                        #seen child to get the new lowlink of the node, this is
                        #where backtracking begins
                        seen = neighbors[child_idx]
                        if on_stack[seen]:
                            nodes_in_cycle.add(node)
                            lowlinks[node] = min(lowlinks[node], lowlinks[seen])
                        child_idx += 1

                    #only want to do this if there are still children left that
                    #we haven't seen
                    if child_idx < num_neighbors:
                        child = neighbors[child_idx]
                        #For the below lines, the next thing we want to DFS on is
                        #the child, so we push it to the stack after we push the
                        #same node back on, but with a pointer to the next child
                        #for keeping track.
                        call_stack.append((node,child_idx+1))
                        call_stack.append((child,0))
                        continue #skip the rest of the function, we want to go
                                 #straight to recursing on the child

                    #we only pop off from the stack once we've backtracked all
                    #the way to the beginning of a connected component do not
                    #confuse this stack with the call stack
                    if lowlinks[node] == ids[node]:
                        scc = []
                        while True:
                            popped = stack.pop()
                            on_stack[popped] = False
                            #lowlinks[popped] = ids[node]
                            scc.append(popped)
                            if popped == node:
                                break
                        if len(scc) > 1 or popped in self.get_dependencies(popped):
                            #again, we only want sccs with more than one node or
                            #sccs with a self loop
                            for node in scc:
                                scc_nodes.add(node)
                            scc_count += 1
                    #add the node to the order after its children have been
                    #processed, resulting in a post order traversal this will
                    #only get called when the continue above is not executed,
                    #meaning there are no more children that haven't been
                    #processed
                    order.append(node)

        return order, nodes_in_cycle, scc_nodes

    def rename_sheet(self, wb, old_name: str, new_name: str) -> None:
        """
        Iterates over the cells in the reference graph in order to
         - Rename any cell in the renamed old_sheet to the new_sheet
         - Find any formulas that reference the renamed old_sheet and update
           the reference to the new_sheet
        """
        new_graph = deepcopy(self.graph)
        for (sheet, cell) in self.graph:
            # If the cell is in the old sheet, rename it in the graph
            if sheet == old_name.lower():
                new_graph[(new_name.lower(), cell)] = new_graph.pop((sheet, cell))
                sheet = new_name.lower()
            # If the cell references the old sheet, update the reference and the
            # formula in the cell
            for dependency in new_graph[(sheet, cell)]:
                if dependency[0] == old_name.lower():
                    new_graph[(sheet, cell)].remove(dependency)
                    new_graph[(sheet, cell)].append((new_name.lower(),
                                                          dependency[1]))
                    # Update the formula in the cell
                    cell_obj = wb.get_sheet(sheet).get_cell(cell)
                    cell_obj.set_content(replace_names(cell_obj.get_content(),
                                                         old_name, new_name))
        # Use the new graph as the reference graph
        self.graph = new_graph
