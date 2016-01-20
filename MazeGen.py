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

def format_location(coordinate, dx=0.0, dy=0.0, dz=0.0):
    """Turn coordinates into 3D."""
    num_coordinates = len(coordinate)
    if num_coordinates == 1:
        return (coordinate[0], dy, dz)
    elif num_coordinates == 2:
        return (coordinate[0], coordinate[1], dz)
    else:
        return tuple(coordinate[:3])
        
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

def recursive_pathfind(start, end, node_list, path=[], reverse=True, last_id=None):
    path = path + [start]
    
    #Path complete
    if start == end:
        return path
        
    #Search parents
    if reverse:
        parent = node_list[start].parent
        if parent is not None:
            found_path = recursive_pathfind(parent, end, node_list, path=path, reverse=True, last_id=start)
            if found_path is not None:
                return found_path
                
    #Search children
    for node_id in node_list[start].children:
        if node_id != last_id:
            found_path = recursive_pathfind(node_id, end, node_list, path=path, reverse=False, last_id=start)
            if found_path is not None:
                return found_path
    return None

def draw_path(node_list):
    curve_points = [format_location(node.location) for node in node_list]
    pm.curve(p=curve_points, d=5)


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
            pm.addAttr(new_cube, sn='gen_id', ln='GenerationID', min=0, at='long')
            pm.setAttr('{}.gen_id'.format(new_cube), id)
    
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
            if len(curves) > 1:
                converted_coordinates = [format_location(coordinate) for coordinate in curves]
                pm.curve(p=converted_coordinates, d=1)
        

generation = GenerationCore(3)

max_nodes = 1000
min_nodes = 0
max_fails = 500
max_length = 20

start_size = 0.5
size_reduction = 0.98
min_size = 0.01

bounds = ((-1, -1, -1), (4, 4, 4))
#bounds = None



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

start = 0
end = generation.nodes[-1].id
node_list = [generation.nodes[node_id] for node_id in recursive_pathfind(start, end, generation.nodes)]
draw_path(node_list)
