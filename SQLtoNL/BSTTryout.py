from collections import defaultdict

# import sqlparse
import networkx as nx

# Declare global variables here
G = nx.DiGraph()
f_str = ""
p_str = ""
w_str = ""
VAL_SEL = " whose "
COORD_CONJ = "and "
CONJ_NOUN = " that "
CONJ_PROJ = "and"
CONJ_SEL = "and "
Rs = ['student history', 'courses schedule']
Rp = ['students', 'comments', 'courses', 'departments', 'instructors']
Rq = 'courses'


class EdgeType:
    MEMBERSHIP, PREDICATE, SELECTION, FUNCTION, TRANSFORMATION, ORDER, GROUPING, HAVING = range(8)


class NodeType:
    RELATION, ATTRIBUTE, VALUE = range(3)


def add_nodes():
    '''
    Add nodes to directed graph G
    @return:
    '''
    global G
    G.add_node('students', type=NodeType.RELATION, label='students');
    G.add_node('comments', type=NodeType.RELATION, label='comments');
    G.add_node('departments', type=NodeType.RELATION, label='departments');
    G.add_node('student history', type=NodeType.RELATION, label='student history');
    G.add_node('courses', type=NodeType.RELATION, label='courses');
    G.add_node('courses schedule', type=NodeType.RELATION, label='courses schedule');
    G.add_node('instructors', type=NodeType.RELATION, label='instructors');
    G.add_node('student name', type=NodeType.ATTRIBUTE, label='name');
    G.add_node('GPA', type=NodeType.ATTRIBUTE, label='GPA');
    G.add_node('description', type=NodeType.ATTRIBUTE, label='description');
    G.add_node('rating', type=NodeType.ATTRIBUTE, label='rating');
    G.add_node(3, type=NodeType.VALUE, label='3');
    G.add_node('class', type=NodeType.ATTRIBUTE, label='class');
    G.add_node(2011, type=NodeType.VALUE, label='2011');
    G.add_node('title', type=NodeType.ATTRIBUTE, label='title');
    G.add_node('department name', type=NodeType.ATTRIBUTE, label='name')
    G.add_node('CS', type=NodeType.VALUE, label='CS');
    G.add_node('term', type=NodeType.ATTRIBUTE, label='term');
    G.add_node('Spring', type=NodeType.VALUE, label='Spring');
    G.add_node('instructors name', type=NodeType.ATTRIBUTE, label="name");


def add_edges():
    '''
    Add edges to directed graph G
    @return:
    '''
    global G
    G.add_edge('student name', 'students', type=EdgeType.MEMBERSHIP, label='of');
    G.add_edge('GPA', 'students', type=EdgeType.MEMBERSHIP, label='of');
    G.add_edge('students', 'comments', type=EdgeType.PREDICATE, label='gave');
    G.add_edge('comments', 'students', type=EdgeType.PREDICATE, label='are given by');
    G.add_edge('description', 'comments', type=EdgeType.MEMBERSHIP, label='of');
    G.add_edge('comments', 'rating', type=EdgeType.SELECTION);
    G.add_edge('rating', 3, type=EdgeType.PREDICATE, label='is greater than');
    G.add_edge('students', 'student history', type=EdgeType.PREDICATE, label='have taken');
    G.add_edge('student history', 'students', type=EdgeType.PREDICATE);
    G.add_edge('students', 'class', type=EdgeType.SELECTION);
    G.add_edge('class', 2011, type=EdgeType.PREDICATE, label='is');
    G.add_edge('student history', 'courses', type=EdgeType.PREDICATE);
    G.add_edge('courses', 'student history', type=EdgeType.PREDICATE, label="are taken by");
    G.add_edge('title', 'courses', type=EdgeType.MEMBERSHIP, label="of");
    G.add_edge('courses', 'courses schedule', type=EdgeType.PREDICATE, label="are taught by");
    G.add_edge('courses schedule', 'courses', type=EdgeType.PREDICATE);
    G.add_edge('courses', 'departments', type=EdgeType.PREDICATE, label="are offered by");
    G.add_edge('departments', 'courses', type=EdgeType.PREDICATE, label="offer");
    G.add_edge('departments', 'department name', type=EdgeType.SELECTION);
    G.add_edge('department name', 'CS', type=EdgeType.PREDICATE, label="is");
    G.add_edge('courses schedule', 'instructors', type=EdgeType.PREDICATE);
    G.add_edge('instructors', 'courses schedule', type=EdgeType.PREDICATE, label="teach");
    G.add_edge('instructors name', 'instructors', type=EdgeType.MEMBERSHIP, label="of");
    G.add_edge('courses schedule', 'term', type=EdgeType.SELECTION);
    G.add_edge('term', 'Spring', type=EdgeType.PREDICATE, label='is');


def make_lbl(clause, label, const):
    '''
    Make label helper function
    @param clause:
    @param label:
    @param const:
    @return:
    '''
    if clause == "":
        clause = label
    else:
        clause = clause + const + label
    return clause


def bst(open, close, v, joined_node_counter, replaced_node_counter):
    '''
    BST graph traversal
    @param replaced_node_counter:
    @param joined_node_counter:
    @param open:
    @param close:
    @param v:
    @return:
    '''
    global G
    global f_str
    global p_str
    global w_str
    sel_edges = 0
    children = []
    close.append(v)
    if v not in Rs:
        if joined_node_counter == 0:
            f_str += ' ' + G.node[v]['label']
        else:
            replaced_node_counter += 1
            f_str = f_str.replace('node_' + str(replaced_node_counter), G.node[v]['label'])
    for t in G.successors(v):
        for t0 in G.successors(t):
            if G.node[t0]['type'] == NodeType.VALUE:
                str1 = G.node[v]['label'] + VAL_SEL + G.node[t]['label'] + ' ' + G[t][t0]['label'] + ' ' + \
                       G.node[t0]['label'] + ' '
                w_str = make_lbl(w_str, str1, CONJ_SEL)
            if (t not in close) and (G.node[t0]['type'] != NodeType.VALUE):
                if G[v][t]['type'] == EdgeType.SELECTION:
                    sel_edges = sel_edges + 1
                children.append(t)
                if 'label' in G[v][t] and G[v][t]['label'] not in f_str:
                    joined_node_counter += 1
                    f_str = f_str + ' ' + G[v][t]['label'] + ' node_' + str(joined_node_counter)
    while len(children) > 0:
        tv = children.pop()
        sel_edges = sel_edges - 1
        if sel_edges > 0:
            G.node[tv]['label'] = G.node[tv]['label'] + COORD_CONJ
        elif sel_edges == 0:
            G.node[tv]['label'] = G.node[tv]['label'] + CONJ_NOUN
        if tv not in open:
            open.append(tv)
    for t_in in G.predecessors(v):
        if ('label' in G[t_in][v]) and (G[t_in][v]['type'] == EdgeType.MEMBERSHIP):
            children.append((G.node[t_in]['label'], G[t_in][v]['label']))
    str2 = ""
    while len(children) != 0:
        tuples = children.pop()
        str2 = str2 + " the " + tuples[0] + " " + tuples[1] + " " + G.node[v]['label']
        #if len(children) != 0:
        str2 += ", "
    if str2 != "":
        p_str = make_lbl(p_str, str2, CONJ_PROJ)
    if len(open) != 0:
        v = open.pop()
        bst(open, close, v, joined_node_counter, replaced_node_counter)


# BST traversal example
add_nodes()
add_edges()
bst([], [], Rq, 0, 0)
print('Find' + p_str + 'for' + f_str + '.')
print('Return results only for ' + w_str)
