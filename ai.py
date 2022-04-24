from __future__ import absolute_import, division, print_function
import copy, random
from distutils.log import error
from json.encoder import INFINITY
from game import Game

MOVES = {0: 'up', 1: 'left', 2: 'down', 3: 'right'}
MAX_PLAYER, CHANCE_PLAYER = 0, 1 

WEIGHTS =   [   # from this, we want the biggest number in the top left, and second biggest to the right, etc
                            16, 15, 14, 13,
                            9, 10, 11, 12,
                            8,  7,  6,  5,
                            1,  2,  3,  4
                        ]
WEIGHTS = [4**weight for weight in WEIGHTS]

# referenced: http://cs229.stanford.edu/proj2016/report/NieHouAn-AIPlays2048-report.pdf

# Tree node. To be used to construct a game tree. 
class Node: 
    # Recommended: do not modify this __init__ function
    def __init__(self, state, player_type):
        self.state = (copy.deepcopy(state[0]), state[1])

        # to store a list of (direction, node) tuples
        self.children = []

        self.player_type = player_type

    # returns whether this is a terminal state (i.e., no children)
    def is_terminal(self):
        #TODO: complete this
        return len(self.children) == 0 

# AI agent. Determine the next move.
class AI:
    # Recommended: do not modify this __init__ function
    def __init__(self, root_state, search_depth=3): 
        self.root = Node(root_state, MAX_PLAYER)
        self.search_depth = search_depth
        self.simulator = Game(*root_state)

    # (Hint) Useful functions: 
    # self.simulator.current_state, self.simulator.set_state, self.simulator.move

    # TODO: build a game tree from the current node up to the given depth
    def build_tree(self, node = None, depth = 0):
        if(node == None):
            return
        # base case: depth is 0, we simply return
        if (depth == 0):
            return 
        # recursive case 1: the current node is a chance player -> then the next state will be randomly chosen
        # we recurse on the 'subtrees' with depth-1 and add those subtrees as children to our current node
        # finally we return our node with its added children
        elif node.player_type == CHANCE_PLAYER: # we are evaluating this node as chance player; its children are determined by chance 
            # initialize board and score from the initial node's state
            self.simulator.set_state(node.state[0], node.state[1])
            empty_tiles = self.simulator.get_open_tiles()
            
            # what are the children of this node? all of the empty tiles could become a '2' in the next state
            for tile in empty_tiles:
                # reset simulator state at the beginning of checking each child
                self.simulator.set_state(node.state[0], node.state[1])
                
                # get the new boardstate
                (i, j) = tile
                boardstate = self.simulator.tile_matrix #DEEPCOPY
                boardstate[i][j] = 2
                # get the new score
                simscore = self.simulator.score #DEEPCOPY
                state = (boardstate, simscore)
                #create child node
                child = Node(state , MAX_PLAYER) 
                # evaluate the child subtree
                self.build_tree(node=child, depth=depth-1)
                node.children.append(child)
        
        # recursive case 2:  the current node is a max player -> the next state will be based on the max players actions
        # we will recurse on the chance subtrees with depth-1 and add those subtrees as children to the current node
        # the next states would be based on the 
        elif node.player_type == MAX_PLAYER:
            self.simulator.set_state(node.state[0], node.state[1])
            # how do we find the next state of the max player 
            
            for direction in MOVES:
                # reset to parent state for every iteration
                self.simulator.set_state(node.state[0], node.state[1])
                # try to move 
                if self.simulator.move(direction):
                    # if possible set child's state to the moved state
                    state = self.simulator.current_state() # DEEPCOPY
                    child = Node(state, CHANCE_PLAYER)
                    self.build_tree(node=child, depth=depth-1)
                    node.children.append(child)

                else: 
                    #its not possible, our state score should be 
                    state = (self.simulator.current_state()[0], -1*INFINITY)
                    child = Node(state, CHANCE_PLAYER)
                    node.children.append(child)

        

    # TODO: expectimax calculation.
    # Return a (best direction, expectimax value) tuple if node is a MAX_PLAYER
    # Return a (None, expectimax value) tuple if node is a CHANCE_PLAYER
    def expectimax(self, node = None):
        # TODO: delete this random choice but make sure the return type of the function is the same
        # return random.randint(0, 3), 0
        if node.is_terminal(): 
            return (None , node.state[1])
        elif node.player_type == MAX_PLAYER:
            value = -1*INFINITY
            oldValue = value
            idx = -1
            for i, child in enumerate(node.children): # sometimes move children arent actually there ie their directions could be 0,2,3 or 1,2 etc
                value = max(value, self.expectimax(child)[1])
                idx = i if not (value == oldValue) else idx
                oldValue = value
                # else do nothing
            return (idx, value)
        elif node.player_type == CHANCE_PLAYER:
            value = 0
            probability = 1/len(node.children)
            for child in node.children:
                value += self.expectimax(child)[1]*probability
            return (None, value)
        else:
            print('error!')
            error

    # Return decision at the root
    def compute_decision(self):
        self.build_tree(self.root, self.search_depth)
        direction, _ = self.expectimax(self.root)
        return direction

    # TODO (optional): implement method for extra credits
    def compute_decision_ec(self):
        self.build_tree(self.root, self.search_depth + 1)
        # print('built tree')
        direction, _ = self.expectimax_ec(self.root)
        # print('minmaxed...')
        # print(direction)
        return direction

    def get_adjacent_values(self, i, j):
        grid_bounds = (len(self.simulator.tile_matrix), len(self.simulator.tile_matrix[0]))
        print("ADJ INDECES")
        adj_indecies = [ (i+direction[0], j+direction[1]) for direction in [(0,1), (1,0), (0,-1), (-1,0)] 
            if ((i+direction[0] > -1) and (i+direction[0] < grid_bounds[0]) and (j+direction[1] > -1) and (j+direction[1] < grid_bounds[1])) ]
        
        vals = [ self.simulator.tile_matrix[index[0]][index[1]] for index in adj_indecies]
        return vals
 
    def find_max_tile(self):
        val = -1
        for arr in self.simulator.tile_matrix:
            for num in arr:
                val = max(val, num)
        return val


    def expectimax_ec(self, node = None):
        if node.is_terminal():
            # print(weights)
            i = 0
            location_bias = 0
            for arr in self.simulator.tile_matrix:
                for val in arr:
                    location_bias = val * WEIGHTS[i]
                    i+=1
            # empty_bias = 0
            empty_bias = len(self.simulator.get_open_tiles())*1000
            return (None , node.state[1] + location_bias + empty_bias)
        elif node.player_type == MAX_PLAYER:
            value = -1*INFINITY
            oldValue = value
            idx = -1
            for i, child in enumerate(node.children): 
                value = max(value, self.expectimax_ec(child)[1])
                idx = i if not (value == oldValue) else idx
                oldValue = value
                # else do nothing
            return (idx, value)
        elif node.player_type == CHANCE_PLAYER:
            value = 0
            probability = 1/len(node.children)
            for child in node.children:
                value += self.expectimax_ec(child)[1]*probability
            return (None, value)
        else:
            print('error!')
            error



    def build_tree_ec(self, node = None, depth = 0):
        if(node == None):
            return
        # base case: depth is 0, we simply return
        if (depth == 0):
            return 
        # recursive case 1: the current node is a chance player -> then the next state will be randomly chosen
        # we recurse on the 'subtrees' with depth-1 and add those subtrees as children to our current node
        # finally we return our node with its added children
        elif node.player_type == CHANCE_PLAYER: # we are evaluating this node as chance player; its children are determined by chance 
            # initialize board and score from the initial node's state
            self.simulator.set_state(node.state[0], node.state[1])
            empty_tiles = self.simulator.get_open_tiles()
            
            # what are the children of this node? all of the empty tiles could become a '2' in the next state
            for tile in empty_tiles:
                # reset simulator state at the beginning of checking each child
                self.simulator.set_state(node.state[0], node.state[1])
                
                # get the new boardstate
                (i, j) = tile
                boardstate = self.simulator.tile_matrix #DEEPCOPY
                boardstate[i][j] = 2
                # get the new score
                simscore = self.simulator.score #DEEPCOPY
                state = (boardstate, simscore)
                #create child node
                child = Node(state , MAX_PLAYER) 
                # evaluate the child subtree
                self.build_tree(node=child, depth=depth-1)
                node.children.append(child)
        
        # recursive case 2:  the current node is a max player -> the next state will be based on the max players actions
        # we will recurse on the chance subtrees with depth-1 and add those subtrees as children to the current node
        # the next states would be based on the 
        elif node.player_type == MAX_PLAYER:
            self.simulator.set_state(node.state[0], node.state[1])
            # how do we find the next state of the max player 
            
            for direction in MOVES:
                # reset to parent state for every iteration
                self.simulator.set_state(node.state[0], node.state[1])
                # try to move 
                if self.simulator.move(direction):
                    # if possible set child's state to the moved state
                    state = self.simulator.current_state() # DEEPCOPY
                    child = Node(state, CHANCE_PLAYER)
                    self.build_tree(node=child, depth=depth-1)
                    node.children.append(child)

                else: 
                    #its not possible, our state score should be 
                    state = (self.simulator.current_state()[0], -1*INFINITY)
                    child = Node(state, CHANCE_PLAYER)
                    node.children.append(child)