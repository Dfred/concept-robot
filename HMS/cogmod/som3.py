
import random as ran
from math import sqrt, log, exp
import time
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import inout

# params
h_nodes = 4
v_nodes = 4
vector_size = 3
initial_weights = 0.5
num_iterations = 2000
initial_learning_rate = 0.1
train_uniform = True
training_data = [ [1.0, 0.0, 0.0], 
                  [0.0, 1.0, 0.0], 
                  [0.0, 0.0, 1.0], 
                  [0.0, 0.5, 0.5], 
                  [0.5, 0.5, 0.0], 
                  [1.0, 0.0, 1.0]]

n_soms = 0

draw = "colour"     # "colour", "grid" or "umatrix"



class Som(QThread):
    """ node class
    """
    
    def __init__(self, h_nodes, v_nodes, vector_size, parent = None):
        """ initiate variables 
        """
        QThread.__init__(self, parent)
        self.nodes = []
        self.initialise(h_nodes, v_nodes, vector_size)
        self.radius_constant = max(h_nodes, v_nodes)/2.0
        self.time_constant = num_iterations/log(self.radius_constant)
        self.iteration_counter = 0
        
    def __del__(self):
        self.wait()
                
    def initialise(self, h_nodes, v_nodes, vector_size):
        count1 = 0
        while count1 < h_nodes:
            count2 = 0
            while count2 < v_nodes:
                self.nodes.append(node(count1, count2, vector_size))
                count2 += 1
            count1 +=1
            
    def run(self):
        while self.iteration_counter < num_iterations:
            #generate training data
            if train_uniform:
                count = 0
                training_vector = []
                while count < vector_size:
                    training_vector.append(ran.random())
                    count += 1
            else:
                training_vector = training_data[ran.randint(0,5)]
                
            winner = self.find_winner(training_vector)

            
            #adjust other nodes
            learning_rate = initial_learning_rate * exp(-1.0*(self.iteration_counter/self.time_constant))
            neighbourhood = self.calc_neighbourhood()
            for i in self.nodes:
                dist_to_winner = self.calc_distance([winner[1], winner[2]], [i.x_pos, i.y_pos])
                if dist_to_winner < neighbourhood:
                    self.ajust_weights(i, training_vector, learning_rate, dist_to_winner, neighbourhood)

            self.iteration_counter += 1
            
#            self.emit(SIGNAL("update()"))
#            time.sleep(0.02)

#            if self.iteration_counter > 90:
#                pass
        print "done"
        
        
    def find_winner(self, training_vector):
        winner = [10000,0,0]
        for i in self.nodes:
            dist = self.calc_distance(training_vector, i.weights)
            if dist < winner[0]:
                winner = [dist, i.x_pos, i.y_pos]
        return winner
            
            
    def get_node_weights(self, tag):
        """returns the node weights, based on a given tag that corresponds to the nodes position
        """
        x_pos = tag[-2]
        y_pos = tag[-1]
        for i in self.nodes:
            if i.x_pos == int(x_pos) and i.y_pos == int(y_pos):
                return i.weights
            
            
    def ajust_weights(self, node, training_vector, learning_rate, dist_to_winner, neighbourhood):
        dist_influence = exp(-1.0*(dist_to_winner**2/2*(neighbourhood**2)))
        pos = 0
        for i in node.weights:
            #node.weights[pos] = node.weights[pos] +  learning_rate * (training_vector[pos] - node.weights[pos] ) * dist_influence
            node.weights[pos] = node.weights[pos] +  learning_rate * (training_vector[pos] - node.weights[pos] )
            pos += 1
        
        
    def calc_distance(self, vector1, vector2):
        tot = 0
        pos = 0
        for i in vector1:
            tot += (vector1[pos] - vector2[pos])**2
            pos += 1
        return sqrt(tot)
    
    
    def calc_neighbourhood(self):
        return self.radius_constant * exp(-1.0*(self.iteration_counter/self.time_constant))
    

    def get_neighbours(self, node):
        """returns the neighbours of a given node
        """
        node_x = node.x_pos
        node_y = node.y_pos
        neighbours = []
        for i in self.nodes:
            if i.x_pos == node_x - 1 and i.y_pos == node_y:
                neighbours.append(i)
            if i.x_pos == node_x + 1 and i.y_pos == node_y:
                neighbours.append(i)
            if i.x_pos == node_x and i.y_pos == node_y + 1:
                neighbours.append(i)
            if i.x_pos == node_x and i.y_pos == node_y - 1:
                neighbours.append(i)
        return neighbours


    def calculate_UMatrix(self, node, neighbours):
        uheight = 0
        for i in neighbours:
            uheight += (self.calc_distance(node.weights, i.weights))
        return uheight/4.0
    
    
    def safe_som(self, name):
        out = []
        for i in self.nodes:
            out.append(i.weights)
        inout.write_out("som" + name, out)



class node():
    """ node class
    """
    def __init__(self, x_pos, y_pos, vector_size):
        """ initiate variables 
        """
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.weights = []
        self.set_initial_weigths(vector_size)
        
    def set_initial_weigths(self, vector_size):
        count = 0
        while count < vector_size:
            self.weights.append(ran.random()*initial_weights)
            #self.weights.append(ran.random()/2 + .25)
            count += 1
        

class GUI(QMainWindow):
    """ main window
    """
    def __init__(self):
        QMainWindow.__init__(self)
        
        self.setGeometry(300, 100, 1200, 600)
        self.setWindowTitle('GUI')
        self.concept_widget = DrawWidget(self)
        self.concept_widget.setStyleSheet("QWidget { background-color: lightgrey }")
        self.setCentralWidget(self.concept_widget)
        self.statusbar = QStatusBar()
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        
        self.som = Som(h_nodes, v_nodes, vector_size)
        self.connect(self.som, SIGNAL("update()"), self.update)  
        self.som.start()
        
    def update(self):
        self.concept_widget.update()
        if self.som.iteration_counter < num_iterations:
            self.statusBar().showMessage("Iteration " + str(self.som.iteration_counter))
        else:
            self.statusBar().showMessage("Iteration " + str(self.som.iteration_counter) + ", done!")
        
        
        
class DrawWidget(QLabel):
    def __init__(self, parent):
        QLabel.__init__(self, parent)
        self.parent = parent

    def paintEvent(self, event):
        self.color = QColor(255,255,255,255)
        self.x_offset = 150
        self.y_offset = 50
        self.size = 850
        paint = QPainter()
        paint.begin(self)
        paint.setBrush(self.color)
        
        # draw surrounding box
        rect_size = (400, 400)
        paint.drawRect(self.x_offset, self.y_offset, rect_size[0], rect_size[1])
        cell_size = rect_size[0]/h_nodes
        
        if draw == "colour":
            for i in self.parent.som.nodes:
                color = QColor(i.weights[0]*255, i.weights[1]*255, i.weights[2]*255, 255)
                paint.setBrush(color)
                paint.drawRect(self.x_offset + i.x_pos*cell_size,  self.y_offset + i.y_pos*cell_size, cell_size, cell_size)
                
        #if draw == "umatrix":
            for i in self.parent.som.nodes:
                neighbours = self.parent.som.get_neighbours(i)
                uheight = self.parent.som.calculate_UMatrix(i, neighbours)
                paint.setBrush((QColor(uheight*255, uheight*255, uheight*255, 255)))
                paint.drawRect(self.x_offset + 500 + i.x_pos*cell_size,  self.y_offset + i.y_pos*cell_size, cell_size, cell_size)
        
        if draw == "grid":
            for i in self.parent.som.nodes:
                #color = QColor(i.weights[0]*255, i.weights[1]*255, i.weights[2]*255, 255)
                paint.setBrush((QColor(255,0,0,255)))
                paint.drawEllipse(self.x_offset + (395 * i.weights[0]), self.y_offset + (395 * i.weights[1]), 5, 5)
                
            paint.setBrush((QColor(0,0,0,255)))
            
            for i in range(0, h_nodes-1):
                for j in range(0, v_nodes-1):
                    x1 = self.x_offset + (400 * self.parent.som.nodes[i*h_nodes+j].weights[0])
                    y1 = self.y_offset + (400 * self.parent.som.nodes[i*h_nodes+j].weights[1])
                    x2 = self.x_offset + (400 * self.parent.som.nodes[(i+1)*h_nodes+j].weights[0])
                    y2 = self.y_offset + (400 * self.parent.som.nodes[(i+1)*h_nodes+j].weights[1])
                    paint.drawLine(x1, y1, x2, y2)
                    
                    x2 = self.x_offset + (400 * self.parent.som.nodes[i*h_nodes+j+1].weights[0])
                    y2 = self.y_offset + (400 * self.parent.som.nodes[i*h_nodes+j+1].weights[1])
                    paint.drawLine(x1, y1, x2, y2)
                    
            for i in range(0, h_nodes-1):
                    x1 = self.x_offset + (400 * self.parent.som.nodes[i*h_nodes+h_nodes-1].weights[0])
                    y1 = self.y_offset + (400 * self.parent.som.nodes[i*h_nodes+h_nodes-1].weights[1])
                    x2 = self.x_offset + (400 * self.parent.som.nodes[(i+1)*h_nodes+h_nodes-1].weights[0])
                    y2 = self.y_offset + (400 * self.parent.som.nodes[(i+1)*h_nodes+h_nodes-1].weights[1])
                    paint.drawLine(x1, y1, x2, y2)
                    
                    x1 = self.x_offset + (400 * self.parent.som.nodes[(h_nodes-1)*h_nodes+i].weights[0])
                    y1 = self.y_offset + (400 * self.parent.som.nodes[(h_nodes-1)*h_nodes+i].weights[1])
                    x2 = self.x_offset + (400 * self.parent.som.nodes[(h_nodes-1)*h_nodes+i+1].weights[0])
                    y2 = self.y_offset + (400 * self.parent.som.nodes[(h_nodes-1)*h_nodes+i+1].weights[1])
                    paint.drawLine(x1, y1, x2, y2)

        paint.end()



if __name__ == "__main__":
#    app = QApplication(sys.argv)
#    myapp = GUI()
#    myapp.show()
#    sys.exit(app.exec_())
    while n_soms < 10:
        som = Som(4,4,3)
        som.run()
        som.safe_som(str(n_soms))
        n_soms += 1
    
    
