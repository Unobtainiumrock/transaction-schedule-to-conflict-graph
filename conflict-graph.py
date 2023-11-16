import sys
import networkx as nx
import re
import matplotlib.pyplot as plt
from matplotlib.table import Table
from typing import List, Tuple, Dict, Set

#  python3 conflict-graph.py "R1(A) R2(B) W1(A) R2(A) R1(B) W2(A) W1(B)"
#  python3 conflict-graph.py "R1(A) R2(A) R1(B) R2(B) R3(B) W1(A) W2(B)"
#  python3 conflict-graph.py "R1(A) W2(A) W3(A) W2(B) W3(B) W3(C) W1(C)"

PATTERN: re.Pattern = re.compile(r'([RW])(\d+)\((\w+)\)')

def parse_operations(raw_ops: List[str]) -> List[Tuple[int, str, int, str]]:
    parsed_schedule: List[Tuple[int, str, int, str]] = []
    for i, operation in enumerate(raw_ops, start=1):
        match: re.Match = PATTERN.match(operation)
        if match:
            action, transaction_id, item = match.groups()
            parsed_schedule.append((i, action, int(transaction_id), item))
    return parsed_schedule

def update_edge_label(G: nx.DiGraph, node1: int, node2: int, new_info: str) -> None:
    if G.has_edge(node1, node2):
        current_label = G[node1][node2].get('label', '')
        G[node1][node2]['label'] = current_label + '; ' + new_info if current_label else new_info
    else:
        G.add_edge(node1, node2, label=new_info)

def find_and_label_conflicts(schedule: List[Tuple[int, str, int, str]]) -> Tuple[Dict[Tuple[int, int], str], List[Tuple[int, int]]]:
    transaction_conflicts: Dict[Tuple[int, int], List[str]] = {}
    conflict_edges: List[Tuple[int, int]] = []
    last_write: Dict[str, int] = {}
    last_read: Dict[str, List[int]] = {}

    for time, op, tx, data in schedule:
        if op == 'W':
            # Write-Write conflict
            if data in last_write and last_write[data] != tx:
                print(f"Conflict: ('W', {last_write[data]}, 'W', {tx}) Label: W{last_write[data]}({data}),W{tx}({data})")
                conflict_key = (last_write[data], tx)
                transaction_conflicts.setdefault(conflict_key, []).append(f"W{last_write[data]}({data}),W{tx}({data})")
            last_write[data] = tx
            # Read-Write conflict
            if data in last_read:
                for reader in last_read[data]:
                    if reader != tx:
                        print(f"Conflict: ('R', {reader}, 'W', {tx}) Label: R{reader}({data}),W{tx}({data})")
                        conflict_key = (reader, tx)
                        transaction_conflicts.setdefault(conflict_key, []).append(f"R{reader}({data}),W{tx}({data})")
        elif op == 'R':
            if data not in last_read:
                last_read[data] = []
            last_read[data].append(tx)
            # Write-Read conflict
            if data in last_write and last_write[data] != tx:
                print(f"Conflict: ('W', {last_write[data]}, 'R', {tx}) Label: W{last_write[data]}({data}),R{tx}({data})")
                conflict_key = (last_write[data], tx)

    for key in transaction_conflicts:
        transaction_conflicts[key] = '; '.join(transaction_conflicts[key])
    
    conflict_edges = list(transaction_conflicts.keys())

    return transaction_conflicts, conflict_edges


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 conflict-graph.py 'R1(A) R2(B) W1(A) ...'")
        sys.exit(1)

    raw_schedule = sys.argv[1].split()
    schedule = parse_operations(raw_schedule)
    print(f"Parsed schedule: {schedule}")

    G: nx.DiGraph = nx.DiGraph()
    nodes: Set[int] = {t[2] for t in schedule}
    G.add_nodes_from(nodes)

    conflicts, edges = find_and_label_conflicts(schedule)

    G.add_edges_from(edges)

    ######################################################## Ploting Stuff ########################################################
    # Assuming each row in the table needs 0.05 normalized figure units in height
    row_height = 0.05
    num_rows = len(edges)
    table_height = num_rows * row_height
    table_padding = 0.05

    title_space = 0.1
    text_space = 0.1

    total_figure_height = 0.5 + title_space + text_space + table_height + table_padding

    plt.figure(figsize=(8, total_figure_height * 10))  # The 10 is a scaling factor for display units
    bottom_adjustment = table_height + table_padding + text_space
 
    plt.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=bottom_adjustment)
    plt.axis('off')

    # Conflict Graph
    pos = nx.circular_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, arrowstyle='->', arrowsize=20, font_size=12, font_weight='bold', connectionstyle='arc3, rad=0.1')

    plt.title("Conflict Graph", pad=10)

    # Raw Transaction Schedule
    plt.text(0.5, table_height / 2, f"Raw Transaction Schedule: {' '.join(raw_schedule)}", 
         ha='center', va='center', transform=plt.gcf().transFigure, fontsize=10, wrap=True)

    # Table
    cell_text = [[f"{edge}", conflict] for edge, conflict in conflicts.items()]
    table = plt.table(cellText=cell_text, colLabels=["Edge", "Conflicts"], loc='bottom', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.8)

    plt.show()


if __name__ == "__main__":
    main()


