from Types import *
import networkx as nx
import re


class MRPGraphTranslator:
    VAL_SEL = "whose"
    COORD_CONJ = "and"
    CONJ_NOUN = "that"
    CONJ_PROJ = CONJ_SEL = "and"

    def __init__(self):
        self.cStr = ""
        self.G = nx.DiGraph()

    def traverse(self, starting_point, G):
        self.G = G
        self._mrp(starting_point, starting_point, starting_point, [], [], [])
        self.cStr = re.sub(' +',' ', self.cStr)
        self.cStr = re.sub(' +,',',', self.cStr)
        return "Find " + self.cStr

    # node label
    def _node_label(self, x):
        try:
            return self.G.nodes[x]['label']
        except KeyError:
            return str(x + " - no label")

    def _operator_label(self, o):
        if o == PredType.EQ:
            return "is"
        elif o == PredType.NE:
            return "is not equal"
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
    def _l(self, x, y):
        # print(G[x][y]['type']==EdgeType.SELECTION)
        if self.G[x][y]['type'] == EdgeType.SELECTION:
            # if not is_relation(y, G):
            return self._node_label(x) + " " + self.VAL_SEL + " " + self._node_label(y)
        elif self.G[x][y]['type'] == EdgeType.JOIN:
            try:
                return self.G[x][y]['label']
            except KeyError:
                return ""
        elif self.G[x][y]['type'] == EdgeType.PREDICATE:
            return self._node_label(x) + " " + self._operator_label(self.G[x][y]['label']) + " " + self._node_label(y)
        elif self.G[x][y]['type'] == EdgeType.MEMBERSHIP:
            return " the " + self._node_label(x) + " of " + self._node_label(y)
        elif self.G[x][y]['type'] == EdgeType.NESTED_IN:
            return " " + self._node_label(x) + " in " + self._node_label(y)

    # https://openproceedings.org/2008/conf/edbt/SimitsisAKI08.pdf
    # DEFINITION: lM(v), which creates a phrase containing information of all template labels
    # involving the membership edges of v (if any)
    #
    # Maybe there are the better ways to define it, but now, I just use this way (implemented by myself)
    # to define lM
    def _lm(self, node):
        initial = returnResult = "the "
        for predcessor in self.G.predecessors(node):
            if self.G[predcessor][node]['type'] == EdgeType.MEMBERSHIP:
                returnResult += self._node_label(predcessor) + ", "

        if initial != returnResult:
            returnResult = returnResult[:-2]
            return returnResult
        else:
            return ""

    # lV (v), which creates a phrase containing information of all template labels involving
    # the paths starting from v and ending to its values (if any)
    #
    # Similarly, it's my personal defined function
    def _lv(self, node):
        initial = result = self.VAL_SEL + " "
        for successor in self.G.successors(node):
            # TODO check this, because this dummy graph connects relations directly (not through the IDs attribute), then it might work
            if self.G[node][successor]['type'] == EdgeType.SELECTION and self.G.nodes[successor][
                'type'] == NodeType.ATTRIBUTE:
                # TODO for case Rating > 3 or rating < 1, it might not work
                result += self._l(successor, list(self.G.successors(successor))[0]) + " and "
        if result != initial:
            result = result[:-5]
            return result
        else:
            return ""

    def _lmv(self, node):
        return self._lm(node) + " of " + self._node_label(node) + " " + self._lv(node)

    # print(lmv("Courses"))
    def _is_relation(self, node):
        return self.G.nodes[node]['type'] == NodeType.RELATION

    def _is_rp(self, node):
        return self._is_relation(node)

    def _mrp(self, v, rp, u, open, close, path):
        # print()
        # print(v)
        close.append(v)

        if self.G.has_edge(u, v):
            path.append((u, v))

        # print("path u, v")
        # print(path)

        if self._is_rp(v):
            pr = rp
            rp = v
            checkMembershipEdgeExist = False
            for a in self.G.predecessors(v):
                if self.G[a][v]['type'] == EdgeType.MEMBERSHIP:
                    if len(self.cStr) != 0:
                        self.cStr += ", and also "
                    self.cStr += self._lmv(rp)
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
                                if self._is_rp(p):
                                    self.cStr += " that " + self._l(y, x) + " these " + self._node_label(
                                        p) + " " + self._lv(x)
                                    path.remove((p, q))
                                    break
                            # print(y + "->" + x)
                            # cStr += l(y, x) + " " + lv(x) + " "
                            # print("test1")
                            # print(cStr)
                        elif x == pr:
                            self.cStr += " that " + self._l(y, x) + " these " + self._node_label(x)
                            # print("test2")
                            # print(cStr)
                    # we need to break because lmv concatenates all membership edges and predicate edges already
                    checkMembershipEdgeExist = True
                    break

            if not checkMembershipEdgeExist:
                self.cStr += ", these " + self._node_label(pr)
                # print("test3")
                # print(cStr)
                while len(path) != 0:
                    (x, y) = path.pop(0)
                    # print("test3.5")
                    # print(x + ", " + y)
                    if not self._is_rp(y):
                        self.cStr += " " + self._l(x, y) + " " + self._lv(y)
                    else:
                        self.cStr += " " + self._l(x, y) + " " + self._node_label(y) + " " + self._lv(y)
                    # print("test4")
                    # print(cStr)
            path = []
        # foreach stuff which I think it's wrong
        for a in self.G.successors(v):
            if a not in close and self._is_relation(a):
                # print(a)
                open.append((a, rp, v))
        # print("open v, rp, u")
        # print(open)

        if len(open) != 0:
            (v, rp, u) = open.pop()
            # print(u + "->" + v)
            self._mrp(v, rp, u, open, close, path)
