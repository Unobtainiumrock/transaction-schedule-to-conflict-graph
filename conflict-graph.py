import sys
import networkx as nx
import re
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Set

#  python3 conflic-graph.py "R1(A) R2(B) W1(A) R2(A) R1(B) W2(A) W1(B)"
#  python3 conflic-graph.py "R1(A) R2(A) R1(B) R2(B) R3(B) W1(A) W2(B)"
#  python3 conflic-graph.py "R1(A) W2(A) W3(A) W2(B) W3(B) W3(C) W1(C)"

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
        G[node1][node2]['label'] += '; ' + new_info
    else:
        G.add_edge(node1, node2, label=new_info)

def find_and_label_conflicts(G: nx.DiGraph, schedule: List[Tuple[int, str, int, str]]) -> None:
    transaction_conflicts: Dict[str, List[Tuple[str, int, str, int]]] = {}
    last_write: Dict[str, int] = {}
    last_read: Dict[str, List[int]] = {}

    for time, op, tx, data in schedule:
        if data not in transaction_conflicts:
            transaction_conflicts[data] = []

        if op == 'W':
            # Write-Write conflict
            if data in last_write and last_write[data] != tx:
                transaction_conflicts[data].append(('W', last_write[data], 'W', tx))
            last_write[data] = tx
            # Read-Write conflict
            if data in last_read:
                for reader in last_read[data]:
                    if reader != tx:
                        transaction_conflicts[data].append(('R', reader, 'W', tx))
        elif op == 'R':
            if data not in last_read:
                last_read[data] = []
            last_read[data].append(tx)
            # Write-Read conflict
            if data in last_write and last_write[data] != tx:
                transaction_conflicts[data].append(('W', last_write[data], 'R', tx))

    # Labeling conflicts
    for data, transactions in transaction_conflicts.items():
        for transaction in transactions:
            op1, tx1, op2, tx2 = transaction
            label: str = f"{op1}{tx1}({data}),{op2}{tx2}({data})"
            print(f"Conflict: {transaction}", f"Label: {label}")
            update_edge_label(G, tx1, tx2, label)

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

    find_and_label_conflicts(G, schedule)

    # Plotting stuff
    plt.figure(figsize=(7,7))
    pos: Dict[int, Tuple[float, float]] = nx.circular_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, arrowstyle='->', arrowsize=20, font_size=12, font_weight='bold', connectionstyle='arc3, rad=0.1')
    edge_labels: Dict[Tuple[int, int], str] = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=10)
    plt.title("Conflict Graph")
    plt.show()

if __name__ == "__main__":
    main()


