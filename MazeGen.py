from __future__ import division
import random
import pymel.core as py

class Node:
    def __init__(self, id, location, size, distance=0, parent=None, children=None):
        self.id = id
        self.location = tuple(location)
        self.size = size
        self.parent = parent
        self.distance = distance
        self.children = children if children else []
    def __repr__(self):
        return 'Node(id={x.id}, distance={x.distance}, location={x.location}, size={x.size}, parent={x.parent}, children={x.children}'.format(x=self)
    def update_parent(self, parent, node_list):
        self.parent = parent
        self.distance = node_list[parent].distance + 1

class GenerationCore:
    def __init__(self, dimensions, nodes=[]):
        self.nodes = nodes
        self.dimensions = dimensions
        self.range = range(dimensions)
        self.directions = self._possible_directions()
        
    def _possible_directions(self):
        directions = []
        for i in self.range:
            for j in (-1, 1):
                directions.append([j if i == n else 0 for n in self.range])
        return directions

def collision_check(gc_instance, location, size, bounds=None):
    if bounds:
        for i in gc_instance.range:
            if not bounds[0][i] + size <= location[i] <= bounds[1][i] - size:
                return True
    for node in gc_instance.nodes:
        size_total = size + node.size
        distance = [abs(a - b) for a, b in zip(location, node.location)]
        if max(distance) > size_total:
            continue
        distance_total = sum(pow(i, 2) for i in distance)
        if distance_total < pow(size_total, 2):
            return True
    return False
    
class MayaDraw:
    def __init__(self, gc_instance):
        self._gc = gc_instance
        self._cubes = {}
    
    def cubes(self):
        for node in self._gc.nodes:
            size = node.size * 1.98
            new_cube = pm.polyCube(w=size, h=size, d=size)[0]
            pm.move(new_cube, node.location)
            id = node.id
            if id in self._cubes:
                pm.delete(id)
            self._cubes[node.id] = new_cube
    
    def curves(self):
        curve_list = []
        for i, node in enumerate(self._gc.nodes):
            
            if node.id not in self._gc.nodes[i-1].children:
                try:
                    start_point = [self._gc.nodes[self._gc.nodes[i].parent].location]
                except TypeError:
                    start_point = []
                curve_list.append(start_point)
                
            curve_list[-1].append(node.location)
            
        for curves in curve_list:
            if self._gc.dimensions == 2:
                curves_3d = [(i[0], i[1], 0.0) for i in curves]
            else:
                curves_3d = [tuple(i[:3]) for i in curves]
            if len(curves) > 1:
                pm.curve(p=curves_3d, d=1)
        

generation = GenerationCore(2)

max_nodes = 10
min_nodes = 0
max_fails = 500
max_length = 1

start_size = 0.5
size_reduction = 0.9
min_size = 0.01

#bounds = ((-1, -1, -1), (10, 10, 10))
bounds = None



max_retries = generation.dimensions * 2
start_location = [0.0 for i in generation.range]


total_nodes = failed_nodes = current_length = current_retries = 0

generation.nodes.append(Node(0, start_location, start_size))
while (total_nodes + failed_nodes < max_nodes 
       or total_nodes < min_nodes and failed_nodes < max_fails):
    
    if current_retries >= max_retries:
        current_length = max_length
        current_retries = 0
        failed_nodes += 1
    if current_length >= max_length:
        node_id = random.randint(0, total_nodes)
        current_length = 0
    else:
        node_id = total_nodes
    
    node_start = generation.nodes[node_id]
    
    new_direction = random.choice(generation.directions)
    
    new_size = node_start.size * size_reduction
    if new_size < min_size:
        current_retries = max_retries
        failed_nodes += 1
        continue
    new_location = tuple(a + b * node_start.size * 2 for a, b in zip(node_start.location, new_direction))
    
    
    if collision_check(generation, new_location, new_size, bounds):
        current_retries += 1
        continue
    
    total_nodes += 1
    current_length += 1
    new_id = generation.nodes[-1].id + 1
    new_node = Node(new_id, new_location, new_size)
    new_node.update_parent(node_id, generation.nodes)
    node_start.children.append(new_id)
    generation.nodes.append(new_node)


md = MayaDraw(generation)
md.cubes()

