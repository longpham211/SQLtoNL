import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.cm import revcmap

#
# class EdgeType:
#     MEMBERSHIP, PREDICATE, SELECTION = range(3)
#
#
# class NodeType:
#     RELATION, ATTRIBUTE, VALUE = range(3)
#
#
# G = nx.DiGraph()
# G.add_node("Students", type=NodeType.RELATION, label="students")
# G.add_node("NameStu", type=NodeType.ATTRIBUTE, label="name")
# G.add_node("GPA", type=NodeType.ATTRIBUTE, label="GPA")
# G.add_node("Class", type=NodeType.ATTRIBUTE, label="class")
# G.add_node("Comments", type=NodeType.RELATION, label="comments")
# G.add_node("Text", type=NodeType.ATTRIBUTE, label="description")
# G.add_node("Rating", type=NodeType.ATTRIBUTE, label="rating")
# G.add_node("3", type=NodeType.VALUE, label="3")
# G.add_node("2011", type=NodeType.VALUE, label="2011")
# G.add_node("StudentHistory", type=NodeType.RELATION, label="history")
# G.add_node("Courses", type=NodeType.RELATION, label="courses")
# G.add_node("Title", type=NodeType.ATTRIBUTE, label="title")
# G.add_node("Departments", type=NodeType.RELATION, label="department")
# G.add_node("NameDep", type=NodeType.ATTRIBUTE, label="name")
# G.add_node("CS", type=NodeType.VALUE, label="CS")
# G.add_node("CoursesSched", type=NodeType.RELATION, label="course's schedule")
# G.add_node("Term", type=NodeType.ATTRIBUTE, label="term")
# G.add_node("Spring", type=NodeType.VALUE, label="Spring")
# G.add_node("Instructors", type=NodeType.RELATION, label="instructors")
# G.add_node("NameIns", type=NodeType.ATTRIBUTE, label="name")
#
# G.add_edge("NameStu", "Students", type=EdgeType.MEMBERSHIP, label="of")
# G.add_edge("GPA", "Students", type=EdgeType.MEMBERSHIP, label="of")
# G.add_edge("Students", "StudentHistory", type=EdgeType.SELECTION, label="have taken")
# G.add_edge("StudentHistory", "Students", type=EdgeType.SELECTION)
# G.add_edge("Students", "Class", type=EdgeType.SELECTION)
# G.add_edge("Class", "2011", type=EdgeType.PREDICATE, operator="=")
# G.add_edge("Comments", "Students", type=EdgeType.SELECTION, label="are given by")
# G.add_edge("Students", "Comments", type=EdgeType.SELECTION, label="give")
# G.add_edge("Comments", "Rating", type=EdgeType.SELECTION)
# G.add_edge("Rating", "3", type=EdgeType.PREDICATE, operator=">")
# G.add_edge("Text", "Comments", type=EdgeType.MEMBERSHIP, label="of")
# G.add_edge("StudentHistory", "Courses", type=EdgeType.SELECTION)
# G.add_edge("Courses", "StudentHistory", type=EdgeType.SELECTION, label="taken by")
# G.add_edge("Title", "Courses", type=EdgeType.MEMBERSHIP, label="of")
# G.add_edge("Courses", "Departments", type=EdgeType.SELECTION, label="are offered by")
# G.add_edge("Departments", "Courses", type=EdgeType.SELECTION, label="offer")
# G.add_edge("Departments", "NameDep", type=EdgeType.SELECTION)
# G.add_edge("NameDep", "CS", type=EdgeType.PREDICATE, operator="=")
# G.add_edge("Courses", "CoursesSched", type=EdgeType.SELECTION, label="are taught by")
# G.add_edge("CoursesSched", "Courses", type=EdgeType.SELECTION)
# G.add_edge("CoursesSched", "Instructors", type=EdgeType.SELECTION)
# G.add_edge("Instructors", "CoursesSched", type=EdgeType.SELECTION, label="teach")
# G.add_edge("CoursesSched", "Term", type=EdgeType.SELECTION)
# G.add_edge("Term", "Spring", type=EdgeType.PREDICATE, operator="=")
# G.add_edge("NameIns", "Instructors", type=EdgeType.MEMBERSHIP, label="of")


VAL_SEL = "whose"
COORD_CONJ = "and"
CONJ_NOUN = "that"
CONJ_PROJ = CONJ_SEL = "and"


# node label
def node_label(x):
    return G.nodes[x]['label']


def operator_label(o):
    if o == "=":
        return "is"
    elif o == "<=":
        return "does not exceed"
    elif o == ">":
        return "is greater than"
    elif o == "LIKE":
        return "looks like"


# edge label
def l(x, y):
    # print(G[x][y]['type']==EdgeType.SELECTION)
    if G[x][y]['type'] == EdgeType.SELECTION:
        if not is_relation(y, G):
            return node_label(x) + " " + VAL_SEL + " " + node_label(y)
        else:
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
        if(G[predcessor][node]['type'] == EdgeType.MEMBERSHIP):
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
            result += l(successor, list(G.successors(successor))[0])
    if result != initial:
        return result
    else:
        return ""


def lmv(node):
    return lm(node) + " of " + node_label(node) + " " + lv(node)


# print(lmv("Courses"))
def is_relation(node, G):
    return G.nodes[node]['type'] == NodeType.RELATION


def is_rp(node):
    # return is_relation(node)
    return node in RP_list


RP_list = ["Students", "Instructors", "Comments"]
cStr = ""

# print(l("Students", "Comments"))
# print(node_label("Students"))
#print(lmv("Students"))


def mrp(v, rp, u, G, open, close, path):
    global cStr
    # print()
    # print(v)
    close.append(v)

    if G.has_edge(u, v):
        path.append((u, v))

    # print("path u, v")
    # print(path)

    if is_rp(v):
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
                            if is_rp(p):
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
                if not is_rp(y):
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

    print()


# Because Students node is the subject, therefore, we set it as the v, starting of the recursive function
# Hmmm, I don't know choosing Students itself to become its parent is correct or not, let's see.
# mrp(v, rp, u, G, open, close, path):
mrp("Comments", "Comments", "Comments", G, [], [], [])

print("Find " + cStr)


# print(G.nodes["NameStu"]['label'])
# print(G["NameStu"]["Students"])
# print(G.has_edge("NameStu", "Students"))
# nx.draw(G, with_labels=True, font_weight='bold')
# plt.show()
