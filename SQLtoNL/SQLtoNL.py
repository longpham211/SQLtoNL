import operator
import sqlparse
import networkx as nx
from networkx.drawing.nx_agraph import write_dot
from Types import *

class SQLtoNL:

    # translator should implement a method "traverse" which given a DiGraph translates it into a NL string
    def __init__(self, translator):
        self.G = nx.DiGraph()
        self.cStr = ""
        self.translator = translator

    def translate(self, sql):
        formatted_sql = sqlparse.format(sql, reindent=False, keyword_case='upper')

        parsed = sqlparse.parse(formatted_sql)
        for pars in parsed:
            if isinstance(pars, sqlparse.sql.Statement):
                self._create_graph(pars)

        self._collapse_joins()
        # self.write_to_dot("test.dot")
        starting_point = self._find_starting_point()

        translated_str = self.translator.traverse(starting_point, self.G)

        return translated_str

    def write_to_dot(self, filename):
        write_dot(self.G, filename)

    def _find_starting_point(self):  # find reference point in graph
        # Find node which has the most membership edges pointing towards it
        membershipEdgeCount = dict()
        if not isinstance(self.G, nx.DiGraph):
            raise ValueError("Bad argument passed, expected DiGraph")
        for ((s, t), attr) in self.G.in_edges.items():
            if str(t)[0] is not "0": continue  # Make sure it is in nested level 0
            isMembershipEdge = False
            if isinstance(attr, dict):
                for (key, val) in attr.items():
                    if val == EdgeType.MEMBERSHIP:
                        isMembershipEdge = True
            if isMembershipEdge:
                if membershipEdgeCount.__contains__(str(t)):
                    membershipEdgeCount[str(t)] += 1
                else:
                    membershipEdgeCount[str(t)] = 1
        if len(membershipEdgeCount) > 0:
            return max(membershipEdgeCount.items(), key=operator.itemgetter(1))[0]

    def _get_pred_type(self, comparison):  # Order is important
        if '<=' in comparison: return PredType.LE
        if '>=' in comparison: return PredType.GE
        if '=' in comparison: return PredType.EQ
        if '<>' in comparison: return PredType.NE
        if '<' in comparison: return PredType.LT
        if '>' in comparison: return PredType.GT
        if 'LIKE' in comparison: return PredType.LIKE

    # Approach:
    # Iterate through all RELATION nodes
    # Iterate all edges from that node which has type:SELECTION
    # Iterate all edges from 'to-node' which has type:PREDICATE
    # Iterate all edges from that node which has type:SELECTION
    # Make sure that there is a path back to starter node
    # Replace the nodes and edges with a simple JOIN type edge
    def _collapse_joins(self):
        for n, attr in self.G.nodes.data('type'):
            if attr != NodeType.RELATION: continue
            for n2, attr in self.G.adj[n].items():
                if attr['type'] != EdgeType.SELECTION: continue
                for n3, e_pred_attr in self.G.adj[n2].items():
                    if e_pred_attr['type'] != EdgeType.PREDICATE: continue  # Should also check for equal
                    for n4, e_sel_attr in self.G.adj[n3].items():
                        if e_sel_attr['type'] != EdgeType.SELECTION: continue
                        # A join-path has been identified, verify that a join-path back to n is present
                        if self.G.get_edge_data(n4, n3).get('type') == EdgeType.SELECTION and \
                                self.G.get_edge_data(n3, n2).get('type') == EdgeType.PREDICATE and \
                                self.G.get_edge_data(n2, n).get('type') == EdgeType.SELECTION:  # remove n2 & n3.
                            self.G.remove_nodes_from({n2, n3})
                            self.G.add_edge(n, n4, label="has", type=EdgeType.JOIN)
                            self.G.add_edge(n4, n, label="has", type=EdgeType.JOIN)
                            self._collapse_joins()
                            return

    def _case_select(self, token_list, i, next, nested):  # todo: add nested functionality to select
        n = str(nested)
        (i, next) = token_list.token_next(i)
        if isinstance(next, sqlparse.sql.IdentifierList):
            for ident in next.get_identifiers():
                if isinstance(ident, sqlparse.sql.Identifier):
                    self.G.add_node(n + ident.get_parent_name(), label=ident.get_parent_name(),
                                    type=NodeType.RELATION, nested=nested)
                    self.G.add_node(n + str(ident), label=ident.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                    self.G.add_edge(n + str(ident), n + ident.get_parent_name(), label="of",
                                    type=EdgeType.MEMBERSHIP)
                elif isinstance(ident, sqlparse.sql.Function):
                    func_node_name = str(ident)
                    for func_token in ident.tokens:
                        if isinstance(func_token, sqlparse.sql.Identifier):
                            self.G.add_node(n + func_node_name, label=func_token.get_name(),
                                            type=NodeType.FUNCTION, nested=nested)
                        elif isinstance(func_token, sqlparse.sql.Parenthesis):
                            for identifier in func_token.tokens:
                                if isinstance(identifier, sqlparse.sql.Identifier):
                                    self.G.add_node(n + str(identifier), label=identifier.get_name(),
                                                    type=NodeType.ATTRIBUTE, nested=nested)
                                    self.G.add_edge(n + func_node_name, n + str(identifier),
                                                    label=EdgeType.TRANSFORMATION,
                                                    type=EdgeType.TRANSFORMATION)
                                    self.G.add_edge(n + str(identifier), n + identifier.get_parent_name(),
                                                    label="of",
                                                    type=EdgeType.MEMBERSHIP)

        elif isinstance(next, sqlparse.sql.Identifier):
            self.G.add_node(n + next.get_parent_name(), label=next.get_parent_name(),
                            type=NodeType.RELATION, nested=nested)
            self.G.add_node(n + str(next), label=next.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
            self.G.add_edge(n + str(next), n + next.get_parent_name(), label="of", type=EdgeType.MEMBERSHIP)
        elif isinstance(next, sqlparse.sql.Function):
            func_node_name = str(next)
            for func_token in next.tokens:
                if isinstance(func_token, sqlparse.sql.Identifier):
                    self.G.add_node(n + func_node_name, label=func_token.get_name(),
                                    type=NodeType.FUNCTION, nested=nested)
                elif isinstance(func_token, sqlparse.sql.Parenthesis):
                    for identifier in func_token.tokens:
                        if isinstance(identifier, sqlparse.sql.Identifier):
                            self.G.add_node(n + str(identifier), label=identifier.get_name(),
                                            type=NodeType.ATTRIBUTE, nested=nested)
                            self.G.add_edge(n + func_node_name, n + str(identifier),
                                            label=EdgeType.TRANSFORMATION,
                                            type=EdgeType.TRANSFORMATION)
                            self.G.add_edge(n + str(identifier), n + identifier.get_parent_name(),
                                            label="of",
                                            type=EdgeType.MEMBERSHIP)
        # elif isinstance(next, sqlparse.sql.Token) and next.value == "*":
        # self.G.add_node(next, label=next.value, type=NodeType.ATTRIBUTE)
        # self.G.add_edge(next, next.get_parent_name(), label=EdgeType.MEMBERSHIP)

        return i, next

    def _case_where(self, token_list, i, next, nested):
        n = str(nested)
        for wt in next.tokens:
            # ADD CASES FOR EXISTS, IN, comp_op ANY & comp_op ALL
            if isinstance(wt, sqlparse.sql.Comparison):
                left = wt.left
                leftNodeId = str(left) + str(hash(left))
                right = wt.right
                rightNodeId = str(right) + str(hash(right))
                pred_type = self._get_pred_type(str(wt))
                if isinstance(left, sqlparse.sql.Identifier):
                    self.G.add_node(n + left.get_parent_name(), label=left.get_parent_name(),
                                    type=NodeType.RELATION, nested=nested)
                    self.G.add_node(n + leftNodeId, label=left.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                    self.G.add_edge(n + left.get_parent_name(), n + leftNodeId, label=EdgeType.SELECTION,
                                    type=EdgeType.SELECTION)
                if isinstance(right, sqlparse.sql.Identifier):
                    self.G.add_node(n + right.get_parent_name(), label=right.get_parent_name(),
                                    type=NodeType.RELATION, nested=nested)
                    self.G.add_node(n + rightNodeId, label=right.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                    self.G.add_edge(n + rightNodeId, n + right.get_parent_name(), label=EdgeType.SELECTION,
                                    type=EdgeType.SELECTION)
                    self.G.add_edge(n + right.get_parent_name(), n + rightNodeId, label=EdgeType.SELECTION,
                                    type=EdgeType.SELECTION)
                    # Add an edge from right to left since this is a join
                    self.G.add_edge(n + rightNodeId, n + leftNodeId, label=pred_type, type=EdgeType.PREDICATE)
                    self.G.add_edge(n + leftNodeId, n + left.get_parent_name(), label=EdgeType.SELECTION,
                                    type=EdgeType.SELECTION)

                else:  # If it is not an identifier it is a literal or nested query
                    if isinstance(right, sqlparse.sql.Parenthesis):  # nested query
                        nested_id = hash(right)
                        self._create_graph(right, nested_id)

                        # Get start of nested query node
                        start_node = self._get_nested_start_node(nested_id)
                        self.G.add_edge(n + leftNodeId, start_node, label=pred_type, type=EdgeType.PREDICATE)
                        continue  # continue the token iteration

                    # Add node for literal
                    self.G.add_node(n + rightNodeId, label=right.value, type=NodeType.VALUE, nested=nested)

                # Add edge for literal or join
                self.G.add_edge(n + leftNodeId, n + rightNodeId, label=pred_type,
                                type=EdgeType.PREDICATE)  # Always add edge from left to right

            elif isinstance(wt, sqlparse.sql.Token) and ("EXISTS" in wt.value or "IN" in wt.value):
                print("EXISTS")
                next.token_index(wt)
                # Find identifier (assume only one) and add node
                wt_idx = next.token_index(wt)
                (idx, iden) = next.token_prev(wt_idx)
                while not isinstance(iden, sqlparse.sql.Identifier):
                    (idx, iden) = next.token_prev(idx)

                (idx, nested_query) = next.token_next(wt_idx)
                while not isinstance(nested_query, sqlparse.sql.Parenthesis):
                    (idx, nested_query) = next.token_prev(idx)

                nested_id = hash(nested_query)
                self._create_graph(nested_query, nested_id)
                # Get start of nested query node
                start_node = self._get_nested_start_node(nested_id)

                # Add identifier node and edge between parent and attribute
                iden_id = str(iden) + str(hash(iden))
                self.G.add_node(n + iden.get_parent_name(), label=iden.get_parent_name(),
                                type=NodeType.RELATION, nested=nested)
                self.G.add_node(n + iden_id, label=iden.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                self.G.add_edge(n + iden.get_parent_name(), n + iden_id, label=EdgeType.SELECTION,
                                type=EdgeType.SELECTION)

                self.G.add_edge(n + iden_id, start_node, label=EdgeType.NESTED_IN, type=EdgeType.NESTED_IN)
                continue  # continue the token iteration

            elif isinstance(wt, sqlparse.sql.Token) and ("ANY" in wt.value or "ALL" in wt.value):
                raise NotImplementedError
                # Find identifier (assume only one) and add node
                # Find comparison operator for correct edge labeling
                # Add ANY/ALL node (make unique)
                # Add edge between identifier and ANY/ALL with comparison operator label
                # Create nested part
                # Add edge from ANY/ALL to start node of nested query

        return i, next

    def _get_nested_start_node(self, nested):
        for node in self.G.nodes:
            if self.G.nodes[node]['nested'] is nested and \
                    self.G.nodes[node]['type'] is NodeType.ATTRIBUTE:
                pred = self.G.pred[node]
                if len(pred) > 0:
                    return list(pred)[0]
                else:
                    return node

    def _case_join(self, token_list, i, next, nested):
        n = str(nested)
        (i, next) = token_list.token_next(i)
        if isinstance(next, sqlparse.sql.Identifier):
            self.G.add_node(n + str(next), label=next, type=NodeType.RELATION, nested=nested)
        (i, next) = token_list.token_next(i)  # Skip ON keyword
        (i, next) = token_list.token_next(i)
        if isinstance(next, sqlparse.sql.Comparison):
            left = next.left
            right = next.right
            pred_type = self._get_pred_type(str(next))
            if isinstance(left, sqlparse.sql.Identifier):
                self.G.add_node(n + left.get_parent_name(), label=left.get_parent_name(),
                                type=NodeType.RELATION, nested=nested)
                self.G.add_node(n + str(left), label=left.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                self.G.add_edge(n + left.get_parent_name(), n + str(left), label=EdgeType.SELECTION,
                                type=EdgeType.SELECTION)
            if isinstance(right, sqlparse.sql.Identifier):
                self.G.add_node(n + right.get_parent_name(), label=right.get_parent_name(),
                                type=NodeType.RELATION, nested=nested)
                self.G.add_node(n + str(right), label=right.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                self.G.add_edge(n + str(right), n + right.get_parent_name(), label=EdgeType.SELECTION,
                                type=EdgeType.SELECTION)
                self.G.add_edge(n + right.get_parent_name(), n + str(right), label=EdgeType.SELECTION,
                                type=EdgeType.SELECTION)
                # Add an edge from right to left since this is a join
                self.G.add_edge(n + str(right), n + str(left), label=pred_type, type=EdgeType.PREDICATE)
                self.G.add_edge(n + str(left), n + left.get_parent_name(), label=EdgeType.SELECTION,
                                type=EdgeType.SELECTION)
            else:  # If it is not an identifier it is a literal todo: make sure of literal type
                self.G.add_node(n + right, label=right, type=NodeType.VALUE, nested=nested)

            self.G.add_edge(n + str(left), n + str(right), label=pred_type,
                            type=EdgeType.PREDICATE)  # Always add edge from left to right
        return i, next

    def _case_group(self, token_list, i, next, nested):
        n = str(nested)
        (i, next) = token_list.token_next(i)
        if isinstance(next, sqlparse.sql.Token) and next.value == "BY":
            (i, next) = token_list.token_next(i)
            if isinstance(next, sqlparse.sql.IdentifierList):
                prev = ""
                for ident in next.get_identifiers():
                    prev = ident.get_parent_name() if prev == "" else prev
                    if isinstance(ident, sqlparse.sql.Identifier):
                        self.G.add_node(n + str(ident), label=ident.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                        self.G.add_edge(n + str(prev), n + str(ident), label=EdgeType.GROUPING, type=EdgeType.GROUPING)
                        prev = ident
            elif isinstance(next, sqlparse.sql.Identifier):
                self.G.add_node(n + str(next), label=next.get_name(), type=NodeType.ATTRIBUTE, nested=nested)
                self.G.add_edge(n + next.get_parent_name(), n + str(next), label=EdgeType.GROUPING,
                                type=EdgeType.GROUPING)
        return i, next

    def _case_having(self, token_list, i, next, nested):  # todo: add nested functionality to having
        n = str(nested)
        (i, next) = token_list.token_next(i)
        if isinstance(next, sqlparse.sql.Comparison):
            left = next.left
            right = next.right
            if isinstance(left, sqlparse.sql.Function):
                func_node_name = ""
                for func_token in left.tokens:
                    if isinstance(func_token, sqlparse.sql.Identifier):
                        func_node_name = str(left)  # use left instead of real function name to make it unique
                        self.G.add_node(n + func_node_name, label=func_token.get_name(),
                                        type=NodeType.FUNCTION, nested=nested)
                    elif isinstance(func_token, sqlparse.sql.Parenthesis):
                        for sub_func_token in func_token.tokens:
                            if isinstance(sub_func_token, sqlparse.sql.Identifier):
                                self.G.add_node(n + str(sub_func_token), label=sub_func_token.get_name(),
                                                type=NodeType.FUNCTION, nested=nested)
                                self.G.add_edge(n + sub_func_token.get_parent_name(), n + str(sub_func_token),
                                                label=EdgeType.HAVING, type=EdgeType.HAVING)
                                self.G.add_edge(n + str(sub_func_token), n + func_node_name,
                                                label=EdgeType.TRANSFORMATION,
                                                type=EdgeType.TRANSFORMATION)

                                # Add edge from function to right side of comparison
                                pred_type = self._get_pred_type(str(next))
                                if isinstance(right, sqlparse.sql.Parenthesis):  # nested query
                                    nested_id = hash(right)
                                    self._create_graph(right, nested_id)
                                    # Get start of nested query node
                                    start_node = self._get_nested_start_node(nested_id)
                                    self.G.add_edge(n + str(func_node_name), start_node, label=pred_type,
                                                    type=EdgeType.PREDICATE)
                                else:  # literal
                                    self.G.add_edge(n + str(func_node_name), n + str(right), label=pred_type,
                                                type=EdgeType.PREDICATE)
                                break
        return i, next

    def _create_graph(self, token_list, nested=0):
        (i, next) = token_list.token_next(-1)
        while next is not None:

            # SELECT statement, take following identifier list and generate nodes + edges
            if isinstance(next, sqlparse.sql.Token) and next.value == "SELECT":
                (i, next) = self._case_select(token_list, i, next, nested)

            elif isinstance(next, sqlparse.sql.Token) and next.value == "FROM":
                n = str(nested)
                (i, next) = token_list.token_next(i)
                if isinstance(next, sqlparse.sql.IdentifierList):
                    for ident in next.get_identifiers():
                        if isinstance(ident, sqlparse.sql.Identifier):
                            self.G.add_node(n + ident.get_name(), label=ident.get_name(), type=NodeType.RELATION,
                                            nested=nested)
                elif isinstance(next, sqlparse.sql.Identifier):
                    self.G.add_node(n + next.get_name(), label=next.get_name(), type=NodeType.RELATION, nested=nested)

            elif isinstance(next, sqlparse.sql.Where):
                (i, next) = self._case_where(token_list, i, next, nested)

            elif isinstance(next, sqlparse.sql.Token) and "JOIN" in next.value:
                (i, next) = self._case_join(token_list, i, next, nested)

            elif isinstance(next, sqlparse.sql.Token) and next.value == "GROUP":
                (i, next) = self._case_group(token_list, i, next, nested)

            elif isinstance(next, sqlparse.sql.Token) and next.value == "HAVING":
                (i, next) = self._case_having(token_list, i, next, nested)

            (i, next) = token_list.token_next(i)
