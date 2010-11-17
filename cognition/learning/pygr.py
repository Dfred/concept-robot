# pygr.py
#
# graph visualisation module
# based on the Yapgvb software package
# http://code.google.com/p/yapgvb/

import yapgvb

def make_graph(san):
    """ creates a graph using graphviz
        data format = ([node_success_rate, node_number, activation], links)
                       e.g. ([0.8, 0, 0.5], [[1, 0.6], [2, 0.6], [5, 0.4]]])
        data, word_labels
    """
    node_data = []
    for i in san.nodes:
        node_data.append([i.tag, i.activation])
    
#    # filter for successful nodes
#    data = []
#    low_treshold = []
#    for i in data2[0]:
#        if i[0] > 0.1: # success threshold
#            data.append(i[1:4])
#        else:
#            low_treshold.append(i[1:4])

    graph = yapgvb.Digraph("my_graph")
    graph.bgcolor = "lightgrey"

    for i in node_data:
        node = graph.add_node()
        node.style = "filled"
        node.label = i[0]
        node.color = "black"
        node.fillcolor = str(0.7 - (i[1]/2)) + " 1.000 1.000"
        
    nodes = list(graph.nodes)
    
    for i in node_data:
        links = san.get_links(i[0], 0.5)
        node_head = get_node(nodes, i[0])
        for j in links:
            head = node_head
            tail = get_node(nodes, j[0])
            edge = tail - head
            edge.color = "blue"
            edge.weight = j[1]
            edge.fontsize = 10
            edge.label = str(j[1])

    graph.layout(yapgvb.engines.dot)
    graph.render("output.png")
    
    
def get_node(nodes_list, node_tag):
    """ returns node based on given tag
    """
    for i in nodes_list:
        if i.label == node_tag:
            return i
