# To view graph use https://dreampuf.github.io/GraphvizOnline/

from collections import defaultdict
import operator
import sqlparse
import networkx as nx
from networkx.drawing.nx_agraph import write_dot


class EdgeType:
    MEMBERSHIP = 'µ'
    PREDICATE = 'θ'
    SELECTION = 'σ'
    FUNCTION = 'f'
    TRANSFORMATION = 'r'
    ORDER = 'o'
    GROUPING = 'γ'
    HAVING = 'h'
    JOIN = 'j'


class NodeType:
    RELATION, ATTRIBUTE, VALUE = range(3)


class PredType:
    EQ = '='
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    LIKE = 'LIKE'


def _find_starting_point(graph):  # find reference point in graph
    # Find node which has the most membership edges pointing towards it
    membershipEdgeCount = dict()
    if not isinstance(graph, nx.DiGraph):
        raise ValueError("Bad argument passed, expected DiGraph")
    for ((s, t), attr) in graph.in_edges.items():
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


def _get_pred_type(comparison):  # Order is important
    if '<=' in comparison: return PredType.LE
    if '>=' in comparison: return PredType.GE
    if '=' in comparison: return PredType.EQ
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
def _collapse_joins(graph):
    for n, attr in graph.nodes.data('type'):
        if attr != NodeType.RELATION: continue
        for n2, attr in G.adj[n].items():
            if attr['type'] != EdgeType.SELECTION: continue
            for n3, e_pred_attr in G.adj[n2].items():
                if e_pred_attr['type'] != EdgeType.PREDICATE: continue  # Should also check for equal
                for n4, e_sel_attr in G.adj[n3].items():
                    if e_sel_attr['type'] != EdgeType.SELECTION: continue
                    # A join-path has been identified, verify that a join-path back to n is present
                    if G.get_edge_data(n4, n3).get('type') == EdgeType.SELECTION and \
                            G.get_edge_data(n3, n2).get('type') == EdgeType.PREDICATE and \
                            G.get_edge_data(n2, n).get('type') == EdgeType.SELECTION:  # remove n2 & n3.
                        G.remove_nodes_from({n2, n3})
                        G.add_edge(n, n4, label="has", type=EdgeType.JOIN)
                        G.add_edge(n4, n, label="has", type=EdgeType.JOIN)
                        _collapse_joins(graph)
                        return


G = nx.DiGraph()

query1 = 'SELECT * from table1, table2 where table1.id = 1 and table1.col1 = ' \
         'table2.col1 '

query2 = """SELECT Orders.OrderID, Customers.CustomerName, Orders.OrderDate
            FROM Orders
            INNER JOIN Customers ON Orders.CustomerID=Customers.CustomerID"""

query3 = """select students.name, students.GPA, comments.text, instructors.name, comments.text
from 
students, comments,
studenthistory, courses, departments,
coursesched, instructors,
where
students.suid = comments.suid and
students.suid = studenthistory.suid and studenthistory.courseid = courses.courseid and
courses.depid = departments.depid and
courses.courseid = coursesched.courseid and coursesched.instrid = instructors.instrid and
students.class = 2011 and comments.rating > 3 and
coursesched.term = 'spring' and departments.name = 'CS'"""

query4 = """select studenthistory.year, studenthistory.term, max(studenthistory.grade)
from studenthistory
group by
studenthistory.year, studenthistory.term having avg(studenthistory.grade) > 3"""

geo_query_1 = """SELECT state.capital FROM state,border_info WHERE border_info.border=state.state_name AND 
border_info.state_name='texas'; """

geo_query_2 = """SELECT river.river_name FROM river WHERE river.test = 'TEST';"""

sql1 = sqlparse.format(geo_query_2,
                       reindent=False, keyword_case='upper')

parsed = sqlparse.parse(sql1)
for pars in parsed:
    if isinstance(pars, sqlparse.sql.Statement):
        i = -1
        (i, next) = pars.token_next(i)
        while next is not None:

            # SELECT statement, take following identifier list and generate nodes + edges
            if isinstance(next, sqlparse.sql.Token) and next.value == "SELECT":
                (i, next) = pars.token_next(i)
                if isinstance(next, sqlparse.sql.IdentifierList):
                    for ident in next.get_identifiers():
                        if isinstance(ident, sqlparse.sql.Identifier):
                            G.add_node(ident.get_parent_name(), label=ident.get_parent_name(), type=NodeType.RELATION)
                            G.add_node(ident, label=ident.get_name(), type=NodeType.ATTRIBUTE)
                            G.add_edge(ident, ident.get_parent_name(), label="of", type=EdgeType.MEMBERSHIP)
                        elif isinstance(ident, sqlparse.sql.Function):
                            func_node_name = str(ident)
                            for func_token in ident.tokens:
                                if isinstance(func_token, sqlparse.sql.Identifier):
                                    G.add_node(func_node_name, label=func_token.get_name(), type=NodeType.ATTRIBUTE)
                                elif isinstance(func_token, sqlparse.sql.Parenthesis):
                                    for identifier in func_token.tokens:
                                        if isinstance(identifier, sqlparse.sql.Identifier):
                                            G.add_node(identifier, label=identifier.get_name(), type=NodeType.ATTRIBUTE)
                                            G.add_edge(func_node_name, identifier, label=EdgeType.TRANSFORMATION,
                                                       type=EdgeType.TRANSFORMATION)
                                            G.add_edge(identifier, identifier.get_parent_name(), label="of",
                                                       type=EdgeType.MEMBERSHIP)

                elif isinstance(next, sqlparse.sql.Identifier):
                    G.add_node(next.get_parent_name(), label=next.get_parent_name(), type=NodeType.RELATION)
                    G.add_node(next, label=next.get_name(), type=NodeType.ATTRIBUTE)
                    G.add_edge(next, next.get_parent_name(), label="of", type=EdgeType.MEMBERSHIP)
                # elif isinstance(next, sqlparse.sql.Token) and next.value == "*":
                # G.add_node(next, label=next.value, type=NodeType.ATTRIBUTE)
                # G.add_edge(next, next.get_parent_name(), label=EdgeType.MEMBERSHIP)

            if isinstance(next, sqlparse.sql.Token) and next.value == "FROM":
                (i, next) = pars.token_next(i)
                if isinstance(next, sqlparse.sql.IdentifierList):
                    for ident in next.get_identifiers():
                        if isinstance(ident, sqlparse.sql.Identifier):
                            G.add_node(ident.get_name(), label=ident.get_name(), type=NodeType.RELATION)

            if isinstance(next, sqlparse.sql.Where):
                for wt in next.tokens:
                    if isinstance(wt, sqlparse.sql.Comparison):
                        left = wt.left
                        leftNodeId = str(left) + str(hash(left))
                        right = wt.right
                        rightNodeId = str(right) + str(hash(right))
                        pred_type = _get_pred_type(str(wt))
                        if isinstance(left, sqlparse.sql.Identifier):
                            G.add_node(left.get_parent_name(), label=left.get_parent_name(), type=NodeType.RELATION)
                            G.add_node(leftNodeId, label=left.get_name(), type=NodeType.ATTRIBUTE)
                            G.add_edge(left.get_parent_name(), leftNodeId, label=EdgeType.SELECTION,
                                       type=EdgeType.SELECTION)
                        if isinstance(right, sqlparse.sql.Identifier):
                            G.add_node(right.get_parent_name(), label=right.get_parent_name(), type=NodeType.RELATION)
                            G.add_node(rightNodeId, label=right.get_name(), type=NodeType.ATTRIBUTE)
                            G.add_edge(rightNodeId, right.get_parent_name(), label=EdgeType.SELECTION,
                                       type=EdgeType.SELECTION)
                            G.add_edge(right.get_parent_name(), rightNodeId, label=EdgeType.SELECTION,
                                       type=EdgeType.SELECTION)
                            # Add an edge from right to left since this is a join
                            G.add_edge(rightNodeId, leftNodeId, label=pred_type, type=EdgeType.PREDICATE)
                            G.add_edge(leftNodeId, left.get_parent_name(), label=EdgeType.SELECTION,
                                       type=EdgeType.SELECTION)
                        else:  # If it is not an identifier it is a literal todo: make sure of literal type
                            G.add_node(rightNodeId, label=right.value, type=NodeType.VALUE)

                        G.add_edge(leftNodeId, rightNodeId, label=pred_type,
                                   type=EdgeType.PREDICATE)  # Always add edge from left to right

            if isinstance(next,
                          sqlparse.sql.Token) and "JOIN" in next.value:  # todo: diffientiate between different joins
                (i, next) = pars.token_next(i)
                if isinstance(next, sqlparse.sql.Identifier):
                    G.add_node(next, label=next, type=NodeType.RELATION)
                (i, next) = pars.token_next(i)  # Skip ON keyword
                (i, next) = pars.token_next(i)
                if isinstance(next, sqlparse.sql.Comparison):
                    left = next.left
                    right = next.right
                    pred_type = _get_pred_type(str(next))
                    if isinstance(left, sqlparse.sql.Identifier):
                        G.add_node(left.get_parent_name(), label=left.get_parent_name(), type=NodeType.RELATION)
                        G.add_node(left, label=left.get_name(), type=NodeType.ATTRIBUTE)
                        G.add_edge(left.get_parent_name(), left, label=EdgeType.SELECTION, type=EdgeType.SELECTION)
                    if isinstance(right, sqlparse.sql.Identifier):
                        G.add_node(right.get_parent_name(), label=right.get_parent_name(), type=NodeType.RELATION)
                        G.add_node(right, label=right.get_name(), type=NodeType.ATTRIBUTE)
                        G.add_edge(right, right.get_parent_name(), label=EdgeType.SELECTION, type=EdgeType.SELECTION)
                        G.add_edge(right.get_parent_name(), right, label=EdgeType.SELECTION, type=EdgeType.SELECTION)
                        # Add an edge from right to left since this is a join
                        G.add_edge(right, left, label=pred_type, type=EdgeType.PREDICATE)
                        G.add_edge(left, left.get_parent_name(), label=EdgeType.SELECTION, type=EdgeType.SELECTION)
                    else:  # If it is not an identifier it is a literal todo: make sure of literal type
                        G.add_node(right, label=right, type=NodeType.VALUE)

                    G.add_edge(left, right, label=pred_type,
                               type=EdgeType.PREDICATE)  # Always add edge from left to right

            if isinstance(next, sqlparse.sql.Token) and next.value == "GROUP":
                (i, next) = pars.token_next(i)
                if isinstance(next, sqlparse.sql.Token) and next.value == "BY":
                    (i, next) = pars.token_next(i)
                    if isinstance(next, sqlparse.sql.IdentifierList):
                        prev = ""
                        for ident in next.get_identifiers():
                            prev = ident.get_parent_name() if prev == "" else prev
                            if isinstance(ident, sqlparse.sql.Identifier):
                                G.add_node(ident, label=ident.get_name(), type=NodeType.ATTRIBUTE)
                                G.add_edge(prev, ident, label=EdgeType.GROUPING, type=EdgeType.GROUPING)
                                prev = ident
                    elif isinstance(next, sqlparse.sql.Identifier):
                        G.add_node(next, label=next.get_name(), type=NodeType.ATTRIBUTE)
                        G.add_edge(next.get_parent_name(), next, label=EdgeType.GROUPING, type=EdgeType.GROUPING)

            if isinstance(next, sqlparse.sql.Token) and next.value == "HAVING":
                (i, next) = pars.token_next(i)
                if isinstance(next, sqlparse.sql.Comparison):
                    left = next.left
                    right = next.right
                    if isinstance(left, sqlparse.sql.Function):
                        func_node_name = ""
                        for func_token in left.tokens:
                            if isinstance(func_token, sqlparse.sql.Identifier):
                                func_node_name = str(left)  # use left instead of real function name to make it unique
                                G.add_node(func_node_name, label=func_token.get_name(), type=NodeType.ATTRIBUTE)
                            elif isinstance(func_token, sqlparse.sql.Parenthesis):
                                for sub_func_token in func_token.tokens:
                                    if isinstance(sub_func_token, sqlparse.sql.Identifier):
                                        G.add_node(sub_func_token, label=sub_func_token.get_name(),
                                                   type=NodeType.ATTRIBUTE)
                                        G.add_edge(sub_func_token.get_parent_name(), sub_func_token,
                                                   label=EdgeType.HAVING, type=EdgeType.HAVING)
                                        G.add_edge(sub_func_token, func_node_name, label=EdgeType.TRANSFORMATION,
                                                   type=EdgeType.TRANSFORMATION)

                                        # Add edge from function to literal
                                        pred_type = _get_pred_type(str(next))
                                        G.add_edge(func_node_name, right, label=pred_type, type=EdgeType.PREDICATE)

            (i, next) = pars.token_next(i)

write_dot(G, "QueryGraphFull.dot")

_collapse_joins(G)

# print(_find_rf(G))
write_dot(G, "QueryGraph.dot")
# p_str = ""
# f_str = ""
# w_str = ""
# p_str, f_str, w_str = bst(G, [], [], _find_rf(G), p_str, f_str, w_str)
# print('Return results only for ' + w_str)
# plt.show()


VAL_SEL = "whose"
COORD_CONJ = "and"
CONJ_NOUN = "that"
CONJ_PROJ = CONJ_SEL = "and"


# node label
def node_label(x):
    return G.nodes[x]['label']


def operator_label(o):
    if o == PredType.EQ:
        return "is"
    elif o == PredType.LE:
        return "does not exceed"
    elif o == PredType.GT:
        return "is greater than"
    elif o == PredType.GE:
        return "is not smaller than"
    elif o == PredType.LT:
        return "is less than"
    elif o == PredType.LIKE:
        return "looks like"


# edge label
def l(x, y):
    # print(G[x][y]['type']==EdgeType.SELECTION)
    if G[x][y]['type'] == EdgeType.SELECTION:
        # if not is_relation(y, G):
        return node_label(x) + " " + VAL_SEL + " " + node_label(y)
    elif G[x][y]['type'] == EdgeType.JOIN:
        try:
            return G[x][y]['label']
        except KeyError:
            return ""
    elif G[x][y]['type'] == EdgeType.PREDICATE:
        return node_label(x) + " " + operator_label(G[x][y]['label']) + " " + node_label(y)
    elif G[x][y]['type'] == EdgeType.MEMBERSHIP:
        return " the " + node_label(x) + " of " + node_label(y)


# print(G["StudentHistory"]["Students"]['type'])


# https://openproceedings.org/2008/conf/edbt/SimitsisAKI08.pdf
# DEFINITION: lM(v), which creates a phrase containing information of all template labels
# involving the membership edges of v (if any)
#
# Maybe there are the better ways to define it, but now, I just use this way (implemented by myself)
# to define lM
def lm(node):
    initial = returnResult = "the "
    for predcessor in G.predecessors(node):
        if (G[predcessor][node]['type'] == EdgeType.MEMBERSHIP):
            returnResult += node_label(predcessor) + ", "

    if initial != returnResult:
        returnResult = returnResult[:-2]
        return returnResult
    else:
        return ""


# lV (v), which creates a phrase containing information of all template labels involving
# the paths starting from v and ending to its values (if any)
#
# Similarly, it's my personal defined function
def lv(node):
    initial = result = VAL_SEL + " "
    for successor in G.successors(node):
        # TODO check this, because this dummy graph connects relations directly (not through the IDs attribute), then it might work
        if G[node][successor]['type'] == EdgeType.SELECTION and G.nodes[successor]['type'] == NodeType.ATTRIBUTE:
            # TODO for case Rating > 3 or rating < 1, it might not work
            result += l(successor, list(G.successors(successor))[0]) + " and "
    if result != initial:
        result = result[:-5]
        return result
    else:
        return ""


def lmv(node):
    return lm(node) + " of " + node_label(node) + " " + lv(node)


# print(lmv("Courses"))
def is_relation(node, G):
    return G.nodes[node]['type'] == NodeType.RELATION


def is_rp(node, G):
    return is_relation(node, G)
    # return node in RP_list


cStr = ""


# print(l("Students", "Comments"))
# print(node_label("Students"))
# print(lmv("Students"))


def mrp(v, rp, u, G, open, close, path):
    global cStr
    # print()
    # print(v)
    close.append(v)

    if G.has_edge(u, v):
        path.append((u, v))

    # print("path u, v")
    # print(path)

    if is_rp(v, G):
        pr = rp
        rp = v
        checkMembershipEdgeExist = False
        for a in G.predecessors(v):
            if G[a][v]['type'] == EdgeType.MEMBERSHIP:
                if len(cStr) != 0:
                    cStr += ", and also "
                cStr += lmv(rp)
                # print("test0")

                # print(cStr)
                # if len(path) != 0:
                #     (x, y) = path.pop()
                #     cStr += l(y, x) + " " + node_label(pr) + " " + lv(x)
                #     print(cStr)
                while len(path) != 0:
                    (x, y) = path.pop()
                    # if x != pr:
                    #     cStr += l(y, x) + " " + lv(x)
                    #     print(cStr)
                    #
                    # "and also the title of courses  taken by   these students
                    # , and also the name of instructor teach whose term is Spring"
                    # Look, "teach" is l(y,x) while "whose term is Spring" is lv(x),
                    # we want something like: teach these courses whose term is Spring.
                    # these course can be taken from x == pr.
                    # So I think for x != pr, we can find the previous element, until we find the tuple which has
                    # the first element as rp and take "these" + node_label() of this rp node out.

                    if x != pr:
                        for (p, q) in reversed(path):
                            if is_rp(p, G):
                                cStr += " that " + l(y, x) + " these " + node_label(p) + " " + lv(x)
                                path.remove((p, q))
                                break
                        # print(y + "->" + x)
                        # cStr += l(y, x) + " " + lv(x) + " "
                        # print("test1")
                        # print(cStr)
                    elif x == pr:
                        cStr += " that " + l(y, x) + " these " + node_label(x)
                        # print("test2")
                        # print(cStr)
                # we need to break because lmv concatenates all membership edges and predicate edges already
                checkMembershipEdgeExist = True
                break

        if not checkMembershipEdgeExist:
            cStr += ", these " + node_label(pr)
            # print("test3")
            # print(cStr)
            while len(path) != 0:
                (x, y) = path.pop(0)
                # print("test3.5")
                # print(x + ", " + y)
                if not is_rp(y, G):
                    cStr += " " + l(x, y) + " " + lv(y)
                else:
                    cStr += " " + l(x, y) + " " + node_label(y) + " " + lv(y)
                # print("test4")
                # print(cStr)
        path = []
    # foreach stuff which I think it's wrong
    for a in G.successors(v):
        if a not in close and is_relation(a, G):
            # print(a)
            open.append((a, rp, v))
    # print("open v, rp, u")
    # print(open)

    if len(open) != 0:
        (v, rp, u) = open.pop()
        # print(u + "->" + v)
        mrp(v, rp, u, G, open, close, path)


starting_point = _find_starting_point(G)

mrp(starting_point, starting_point, starting_point, G, [], [], [])
print("Find " + cStr)
