
import random
from pymote.algorithm import NodeAlgorithm
from pymote.message import Message

class PTConstruction(NodeAlgorithm):

    def initiator(self, node, message):

        if message.header == NodeAlgorithm.INI:
            node.memory['Termination_counter'] = 0
            node.memory['Source'] = True
            node.memory['Dft_source'] = True
            node.memory['Visited_status'] = True
            node.memory['My_distance'] = 0
            node.memory['Ackcount'] = len(node.memory[self.neighborsKey])
            node.memory['Children'] = []                                  
            node.memory[self.routingTableKey] = {}                        
            node.send(Message(header='Notify',
                              destination=node.memory[self.neighborsKey]))

        if message.header == 'Ack':
            node.memory['Ackcount'] -= 1
            if node.memory['Ackcount'] == 0:
                node.memory['Iteration'] = 1

                # Trazenje najkraceg linka
                link_length = float('inf')
                for unvisited_neighbour in node.memory[self.neighborsKey]:
                    current = node.memory[self.weightKey][unvisited_neighbour]
                    if current < link_length:
                        link_length = current
                        y = unvisited_neighbour

                path_length = link_length
                node.memory['Children'].append(y)
                node.memory['Termination_counter'] += 1

                node.send(Message(header='Expand',
                                  data=(node.memory['Iteration'], path_length),
                                  destination=y))     
                node.memory['Unvisited'] = node.memory[self.neighborsKey][:]        
                node.memory['Unvisited'].remove(y)
                node.status = 'ACTIVE'

    def idle(self, node, message):

        if message.header == 'Notify':
            node.memory['Termination_counter'] = 0
            node.memory['Unvisited'] = node.memory[self.neighborsKey][:]
            node.memory['Unvisited'].remove(message.source)
            node.memory['Source'] = False
            node.memory['Dft_source'] = False
            node.memory[self.routingTableKey] = {} 
            node.send(Message(header='Ack',
                              destination=message.source,))
            node.status = 'AWAKE'

    def awake(self, node, message):

        if message.header == 'Expand':
            # u message.data[1] se nalazi 'My_distance' od cvora koji je poslao poruku
            node.memory['My_distance'] = message.data[1]
            node.memory['Parent'] = message.source
            node.memory['Children'] = []                       

            if len(node.memory[self.neighborsKey]) > 1:
                destination_nodes = node.memory[self.neighborsKey][:]
                destination_nodes.remove(message.source) 
                node.send(Message(destination=destination_nodes,
                                  header='Notify'))
                number_of_neighbors = len(node.memory[self.neighborsKey])
                node.memory['Ackcount'] = number_of_neighbors - 1
                node.status = 'WAITING_FOR_ACK'
            else:
                node.send(Message(destination=node.memory['Parent'],
                                  header='Iteration_Completed',
                                  data=node))
                node.status = 'ACTIVE'

        if message.header == 'Notify':
            node.memory['Unvisited'].remove(message.source)
            node.send(Message(destination=message.source,
                              header='Ack'))

    def waiting_for_ack(self, node, message):

        if message.header == 'Ack':
            node.memory['Ackcount'] -= 1
            if node.memory['Ackcount'] == 0:
                node.send(Message(destination=node.memory['Parent'],
                                  header='Iteration_Completed',
                                  data=node))  
                node.status = 'ACTIVE'  

    def active(self, node, message):       

        if message.header == 'Iteration_Completed':
            if not node.memory['Source']:
                node.send(Message(destination=node.memory['Parent'],
                                  header='Iteration_Completed',
                                  data=message.data))
            else:
                node.memory[self.routingTableKey][message.data] = message.source
                node.memory['Iteration'] += 1
                node.send(Message(destination=node.memory['Children'],
                                  header='Start_Iteration',
                                  data = node.memory['Iteration']))  
                self.compute_local_minimum(node, message)
                node.memory['Childcount'] = 0
                node.status = 'COMPUTING'

        if message.header == 'Start_Iteration':
            # u message.data se nalazi poslani 'Iteration'
            node.memory['Iteration'] = message.data
            self.compute_local_minimum(node, message)

            if len(node.memory['Children']) == 0:
                node.send(Message(destination=node.memory['Parent'],
                                  header='MinValue',
                                  data = node.memory['Minpath']))
            else:
                node.send(Message(destination=node.memory['Children'],
                                  header='Start_Iteration',
                                  data = node.memory['Iteration']))
                node.memory['Childcount'] = 0
                node.status = 'COMPUTING' 

        if message.header == 'Expand':
            node.send(Message(destination=node.memory['Exit'],
                              header='Expand',
                              data = (node.memory['Iteration'], message.data[1])))  
            if node.memory['Exit'] == node.memory['Mychoice'] not in node.memory['Children']:
                node.memory['Children'].append(node.memory['Mychoice'])   
                node.memory['Unvisited'].remove(node.memory['Mychoice'])
                node.memory['Termination_counter'] += 1  
           
        if message.header == 'Notify':
            node.memory['Unvisited'].remove(message.source)
            node.send(Message(destination=message.source,
                              header='Ack')) 

        if message.header == 'Terminate':            
            node.send(Message(destination=node.memory['Children'],
                              header='Terminate'))
            node.status='DONE' 

            # Ako si list, pocni slat Termination_complete
            if len(node.memory['Children']) == 0:
                node.send(Message(destination=node.memory['Parent'],
                                  header='Termination_complete'))
                if node.memory['Visited_status'] == True:
                    node.status = 'VISITED'
                else:
                    node.status = 'DFT_IDLE'

    def computing(self, node, message):
 
        if message.header == 'MinValue':
            if message.data < node.memory['Minpath']:
                node.memory['Minpath'] = message.data
                node.memory['Exit'] = message.source
                node.memory['Mychoice'] = message.source

            node.memory['Childcount'] += 1
            if node.memory['Childcount'] == len(node.memory['Children']):
                if not node.memory['Source']:
                    node.send(Message(destination=node.memory['Parent'],
                                      header='MinValue',
                                      data = node.memory['Minpath']))
                    node.status = 'ACTIVE'
                else:                   
                    self.check_for_termination(node, message)

    def done(self, node, message):

        if message.header == 'Token_location':
            if node.memory['Dft_source'] == True:
                node.memory['DFT_done_counter'] -= 1
                if node.memory['DFT_done_counter'] > 1:
                    node.send(Message(destination=node.memory['Token_exit'],
                                      header='Start_DFT'))  
            node.status = 'VISITED'
                   
        if message.header == 'Termination_complete':
            node.memory['Termination_counter'] -= 1
            if node.memory['Termination_counter'] == 0:
                if node.memory['Source'] == True:
                    node.memory['Source'] == False
                    node.status = 'VISITED'

                    if node.memory['Dft_source'] == True:
                        node.memory['DFT_done_counter'] = len(node.memory[self.routingTableKey])
                        node.memory["DFT_parent"] = None
                        node.memory["DFT_unvisited"] = list(node.memory[self.neighborsKey])
                        self.visit(node)
                    else:
                        node.send(Message(destination=node.memory['DFT_parent'],
                                          header='Token_location'))  
                else:
                    node.send(Message(destination=node.memory['Parent'],
                                      header='Termination_complete'))

                    if node.memory['Visited_status'] == True: 
                        node.status = 'VISITED'    
                    else:
                        node.status = 'DFT_IDLE'  

    # Procedures
    def check_for_termination(self, node, message):
        
        if node.memory['Minpath'] == float('inf'):
            node.send(Message(destination=node.memory['Children'],
                              header='Terminate')) 
            node.status = 'DONE'
        else:
            node.send(Message(destination=node.memory['Exit'],
                              header='Expand',
                              data=(node.memory['Iteration'], node.memory['Minpath']))) 

            if node.memory['Exit'] == node.memory['Mychoice'] not in node.memory['Children']:
                node.memory['Children'].append(node.memory['Mychoice']) 
                node.memory['Unvisited'].remove(node.memory['Mychoice'])
                node.memory['Termination_counter'] += 1 
            node.status = 'ACTIVE'           

    def compute_local_minimum(self, node, message):

        if len(node.memory['Unvisited']) == 0:
            node.memory['Minpath'] = float('inf')
        else:
            # Trazenje najkraceg linka
            link_length = float('inf')
            for unvisited_neighbour in node.memory['Unvisited']:
                current = node.memory[self.weightKey][unvisited_neighbour]
                if current < link_length:
                    link_length = current
                    y = unvisited_neighbour
            node.memory['Minpath'] = node.memory['My_distance'] + link_length
            node.memory['Mychoice'] = node.memory['Exit'] = y

    STATUS = {
        'INITIATOR': initiator,
        'IDLE': idle,
        'AWAKE': awake,
        'WAITING_FOR_ACK': waiting_for_ack,
        'ACTIVE': active,
        'COMPUTING': computing,
        'DONE': done
    }

class PTAll(PTConstruction):

    required_params = ()
    default_params = {
        'neighborsKey': 'Neighbors',
        'routingTableKey': 'routingTable',
        'weightKey': 'weight',
    }

    def initializer(self):

        # set weights
        for node in self.network.nodes():
            node.memory[self.weightKey] = dict()
        for u, v, data in self.network.edges(data=True):
            u.memory[self.weightKey][v] = data[self.weightKey]
            v.memory[self.weightKey][u] = data[self.weightKey]
        # set statuses and neighbors
        for node in self.network.nodes():
            node.memory['Visited_status'] = False
            sensor_readings = node.compositeSensor.read()
            node.memory[self.neighborsKey] = sensor_readings['Neighbors']
            node.status = 'IDLE'
        ini_node = random.choice(self.network.nodes())
        #ini_node = self.network.nodes()[4]
        ini_node.status = 'INITIATOR'

        # send Spontaneously
        self.network.outbox.insert(0, Message(header=NodeAlgorithm.INI,
                                              destination=ini_node))

    def dft_initiator(self, node, message):
        if message.header == NodeAlgorithm.INI:
            node.memory["DFT_parent"] = None
            node.memory["DFT_unvisited"] = list(node.memory[self.neighborsKey])
            node.memory['Visited_status'] = True
            self.visit(node)

    def dft_idle(self, node, message):

        if message.header == 'Token':
            self.reset_node_memory(node, message)
            node.memory['Visited_status'] = True
            node.memory['Token_status'] = True
            node.memory['Source'] = True
            node.memory["DFT_parent"] = message.source
            node.memory["DFT_unvisited"] = list(node.memory[self.neighborsKey])
            node.memory["DFT_unvisited"].remove(node.memory["DFT_parent"])
            node.send(Message(header='Notify',
                              destination=node.memory[self.neighborsKey],))
            node.status = 'INITIATOR'

        elif message.header == 'Notify':
            self.reset_node_memory(node, message)
            node.memory['Unvisited'].remove(message.source)
            node.memory['Source'] = False
            node.send(Message(header='Ack',
                              destination=message.source,))
            node.status = 'AWAKE'

    def visited(self, node, message):

        if message.header == 'Token':
            node.memory["DFT_unvisited"].remove(message.source)
            node.send(Message(header='Backedge',
                              destination=message.source))
        if message.header == 'Return':
            self.visit(node)
        if message.header == 'Backedge':
            self.visit(node)
        if message.header == 'Notify':
            self.reset_node_memory(node, message)
            node.memory['Unvisited'].remove(message.source)
            node.memory['Source'] = False
            node.send(Message(header='Ack',
                              destination=message.source,))
            node.status = 'AWAKE'

        if message.header == 'Start_DFT':
            if node.memory['Token_status'] == True:
                self.visit(node)
            else:
                node.send(Message(header='Start_DFT',
                                  destination=node.memory['Token_exit'],))  

        if message.header == 'Token_location':
            if node.memory['Dft_source'] == False:
                node.memory['Token_exit'] = message.source
                node.send(Message(destination=node.memory['DFT_parent'],
                                  header='Token_location'))  
            else:
                node.memory['DFT_done_counter'] -= 1
                if node.memory['DFT_done_counter'] == 0:
                    node.send(Message(destination=node.memory[self.neighborsKey],
                                      header='Algorithm_complete'))
                    node.status = 'DFT_DONE'         
                else:
                    node.send(Message(destination=node.memory['Token_exit'],
                                      header='Start_DFT')) 

        if message.header == 'Algorithm_complete':                 
            node.send(Message(destination=node.memory[self.neighborsKey],
                              header='Algorithm_complete')) 
            node.status = 'DFT_DONE' 

    def dft_done(self, node, message):
        pass

    def visit(self, node):
        if len(node.memory["DFT_unvisited"]) == 0:
            if node.memory["DFT_parent"] is not None:
                node.send(Message(header='Return',
                                  destination=node.memory["DFT_parent"]))
            node.status = "DFT_IDLE"
        else:
            next_unvisited = node.memory["DFT_unvisited"].pop()
            node.memory['Token_status'] = False
            node.memory['Token_exit'] = next_unvisited
            node.send(Message(header='Token',
                              destination=next_unvisited))
            node.status = "VISITED"

    def reset_node_memory(self, node, message):
        node.memory['Termination_counter'] = 0
        node.memory['My_distance'] = 0
        node.memory['Unvisited'] = node.memory[self.neighborsKey][:]
        node.memory['Ackcount'] = len(node.memory[self.neighborsKey])
        node.memory['Children'] = []

    STATUS = {
        'DFT_INITIATOR': dft_initiator,
        'DFT_IDLE': dft_idle,
        'DFT_DONE': dft_done,
        'VISITED': visited,
        'INITIATOR': PTConstruction.STATUS.get('INITIATOR'),
        'IDLE': PTConstruction.STATUS.get('IDLE'),
        'AWAKE': PTConstruction.STATUS.get('AWAKE'),
        'WAITING_FOR_ACK': PTConstruction.STATUS.get('WAITING_FOR_ACK'),
        'ACTIVE': PTConstruction.STATUS.get('ACTIVE'),
        'COMPUTING': PTConstruction.STATUS.get('COMPUTING'),
        'DONE': PTConstruction.STATUS.get('DONE'),
    }