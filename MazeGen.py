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
        self.tree = None
    def __repr__(self):
        return 'Node(id={x.id}, distance={x.distance}, location={x.location}, size={x.size}, parent={x.parent}, children={x.children}'.format(x=self)
    def update_parent(self, parent, node_list):
        self.parent = parent
        self.distance = node_list[parent].distance + 1

def format_location(coordinate, dx=0.0, dy=0.0, dz=0.0):
    """Turn coordinates into 3D."""
    num_coordinates = len(coordinate)
    if num_coordinates == 1:
        return (coordinate[0], dy, dz)
    elif num_coordinates == 2:
        return (coordinate[0], coordinate[1], dz)
    else:
        return tuple(coordinate[:3])
        
def collision_check(gc_instance, node_ids, location, size, bounds=None):
    if bounds:
        for i in gc_instance.range:
            if not bounds[0][i] + size <= location[i] <= bounds[1][i] - size:
                return True
    
    for node_id in node_ids:
        node = gc_instance.nodes[node_id]
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
            pm.move(new_cube, format_location(node.location))
            id = node.id
            if id in self._cubes:
                pm.delete(id)
            self._cubes[node.id] = new_cube
            pm.addAttr(new_cube, sn='gen_id', ln='GenerationID', min=0, at='long')
            pm.setAttr('{}.gen_id'.format(new_cube), id)
            if self._gc.dimensions > 3:
                visible_key = node.location[3]
                time_gap = max(1.5, node.size)
                pm.setKeyframe(new_cube, attribute='visibility', value=0, time=visible_key - time_gap)
                pm.setKeyframe(new_cube, attribute='visibility', value=1, time=visible_key)
                pm.setKeyframe(new_cube, attribute='visibility', value=0, time=visible_key + time_gap)

    
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



class CoordinateToSegment:
    def __init__(self, dimensions, tree_data):
        self.td = tree_data
        self.dimensions = dimensions
        self._range = range(dimensions)
        n = 0
        self.paths = {}
        for path in self._paths():
            self.paths[tuple(path)] = n
            n += 1

    def convert(self, coordinates, point_size):
        """Convert a coordinate into segments."""
        if len(coordinates) != self.dimensions:
            raise ValueError('invalid coordinate size')
        segments = []
        for i in self._range:
            segments.append(self._find_segment(coordinates[i], point_size))
        min_len = min(len(i) for i in segments)
        segments = [tuple(i[:min_len]) for i in segments]
        path = [self.paths[i] for i in zip(*segments)]
        return path

    def reverse(self, segment):
        """Undo conversion for debugging."""
        segments = [k for i in segment for k, v in self.paths.iteritems() if v == i]
        joined_segments = []
        for i in range(self.dimensions):
            joined_segments.append([j[i] for j in segments])
        totals = []
        for coordinate in joined_segments:
            n = self.td.size - 1
            total = 0
            for i in coordinate:
                total += 2 ** n * i
                n -= 1
            totals.append(total)
        print totals
            
    def _paths(self, current_path=None, current_level=0):
        """Generate a list of paths in the current dimension."""
        if current_path is None:
            current_path = []
        n = (-1, 1)
        if current_level == self.dimensions:
            return [current_path]
        return_path = []
        for i in n:
             return_path += self._paths(current_path + [i], current_level + 1)
        return return_path

    def _find_segment(self, coordinate, point_size):
        """Convert a number into the correct segment."""
        total = 0
        path = []
        coordinate_min, coordinate_max = sorted((coordinate - point_size,
                                                 coordinate + point_size))
        for i in range(self.td.size - self.td.min):
            current_range = 2 ** (self.td.size - i - 1)
            if coordinate == total or coordinate_min < total < coordinate_max:
                return path
            elif coordinate_max < total:
                total -= current_range
                path.append(-1)
            elif coordinate_min > total:
                total += current_range
                path.append(1)
            else:
                raise ValueError('problem with coordinate conversion')
        return path

def get_recursive_items(tree, items=None):
    if items is None:
        items = []
    try:
        for branch in tree:
            items += get_recursive_items(branch)
    except TypeError:
        items += tree
    return items

class TreeData:

    def __init__(self, gc_instance, start_size, min_size=None):
        self._gc = gc_instance
        self._conversion = CoordinateToSegment(self._gc.dimensions, self)
        if min_size is None:
            min_size = start_size
        self.size = start_size
        self.min = min_size
        self._branch_length = range(len(self._conversion.paths) + 1)
        self.data = [[] for i in self._branch_length]
    
    def adjust_size(self, coordinate):
        start_size = self.size
        highest_coord = max(coordinate)
        lowest_coord = min(coordinate)
        max_range = 2 ** self.size
        while max_range < highest_coord or -max_range > lowest_coord:
            self.size += 1
            max_range = 2 ** self.size
        if self.size - start_size:
            self.recalculate()
    
    def recalculate(self):
        """Recalculate the path to every point."""
        self.data = [[] for i in self._branch_length]
        for node in self._gc.nodes:
            path = self.calculate(node.location, node.size)
            self.add(node, path)
    
    def add(self, node, path):
        """Add a node to the tree."""
        node.tree = path
        self._recursive_branch(path)[0][-1].append(node.id)

    def calculate(self, location, size):
        """Calculate the path to a point with location and size."""
        self.adjust_size(location)
        path = self._conversion.convert(location, size)
        return path
        
    def near(self, path):
        """Find all nodes below a recursive path, used in conjunction with calculate."""
        branch, nodes = self._recursive_branch(path)
        nearby_nodes = get_recursive_items(branch)
        return nearby_nodes + nodes
    
    def _recursive_branch(self, path):
        branch = self.data
        nodes = []
        for branch_id in path:
            nodes += branch[-1]
            if not branch[branch_id]:
                branch[branch_id] = [[] for i in self._branch_length]
            branch = branch[branch_id]
        return branch, nodes
        
class GenerationCore:
    def __init__(self, dimensions):
        self.nodes = []
        self.dimensions = dimensions
        self.range = range(dimensions)
        self.directions = self._possible_directions()
    
    def _possible_directions(self):
        """Build a list of every direction the maze can move in."""
        directions = []
        for i in self.range:
            for j in (-1, 1):
                directions.append([j if i == n else 0 for n in self.range])
        return directions
        
    
    def generate(self, max_nodes=None, max_length=None, size=0.5, multiplier=0.99, location=None, bounds=None, min_nodes=None, max_fails=500, min_size=None, max_retries=None):
        
        self.nodes = []
        
        #Sort out number of nodes
        if max_nodes is None:
            if min_nodes is None:
                raise ValueError('either maximum or minimum nodes should be specified')
            max_nodes = min_nodes
        if min_nodes is None:
            min_nodes = 0
        #Take off 1 since total_nodes starts at -1
        max_nodes -= 1
        min_nodes -= 1
        
        #Find out how small the tree needs to go
        if min_size is None:
            min_size = size / 20
        min_size = max(0.001, min_size)
        min_size_exp = 0
        while pow(2, min_size_exp) > min_size:
            min_size_exp -= 1
        
        #Make the tree cover everything without wasting space
        tree = TreeData(self, 0, min_size_exp)
        
        #Make up other values if not specified
        if max_length is None:
            max_length = max_nodes // 5
        if max_retries is None:
            max_retries = self.dimensions
        
        #Check the bounds are in the correct format
        if bounds is not None:
            if len(bounds) != 2:
                raise ValueError('bounding box should contain 2 values')
            for item in bounds:
                if len(item) != self.dimensions:
                    raise ValueError('incorrect bounding box size')
        
        #Check the location is in the correct format
        if location is None:
            location = [0.0 for i in generation.range]
        elif len(location) != self.dimensions:
            raise ValueError('invalid coordinates for starting location')
        
        #General range checks
        multiplier = max(0.001, multiplier)
        min_nodes = max(-1, min_nodes)
        max_nodes = max(min_nodes, max_nodes)
        max_length = max(1, max_length)
        size = max(0.001, size)
        
        #Start generation
        failed_nodes = current_retries = 0
        current_length = total_nodes = -1
        while total_nodes + failed_nodes < max_nodes or total_nodes < min_nodes and failed_nodes < max_fails:
                
            #End the branch if too many fails
            if current_retries >= max_retries:
                current_length = max_length
                current_retries = 0
                failed_nodes += 1
                
            #End the branch if too long
            if current_length >= max_length:
                node_id = random.randint(0, total_nodes)
                current_length = 0
            else:
                node_id = total_nodes
            
            try:
                node_start = self.nodes[node_id]
                
            except IndexError:
                #Fix for the initial node
                new_size = size
                new_location = location
                new_id = 0
                
            else:
                #Get the initial values to create the new node from
                new_size = node_start.size * multiplier
                new_id = self.nodes[-1].id + 1
                
                #End branch now if size is too small
                if new_size < min_size:
                    current_retries = max_retries
                    failed_nodes += 1
                    continue
                    
                direction = random.choice(self.directions)
                new_location = tuple(a + b * node_start.size * 2 for a, b in zip(node_start.location, direction))
                 
            #Check tree for collisions
            node_path = tree.calculate(new_location, new_size)
            near_nodes = tree.near(node_path)
            if collision_check(self, near_nodes, new_location, new_size, bounds):
                current_retries += 1
                continue
            
            #Add to original node as child
            try:
                node_start.children.append(new_id)
            except UnboundLocalError:
                pass
            
            #Create a new node
            new_node = Node(new_id, new_location, new_size)
            new_node.update_parent(node_id, self.nodes)
            
            #Update values with new node
            total_nodes += 1
            current_length += 1
            self.nodes.append(new_node)
            tree.add(new_node, node_path)
            
            
generation = GenerationCore(3)
generation.generate(min_nodes=1000, max_length=100, multiplier=0.9)


start = 0
end = generation.nodes[-1].id
node_list = [generation.nodes[node_id] for node_id in recursive_pathfind(start, end, generation.nodes)]
draw_path(node_list)
