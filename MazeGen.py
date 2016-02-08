from __future__ import division
import random
import cPickle

def format_coordinate(coordinate, links, default_location=[], default_value=0.0):
    """Reformat a coordinate using the new links.
    For example, the coordinate (-1.0, 0.0, 1.0) with new links as (1, 2, 0, 3)
    will be reformatted as [0.0, 1.0, -1.0, 0.0].
    Always returns a list of len(links) values.
    """
    
    dimensions = len(coordinate)
    
    '''
    #Trim off any unnecessary coordinates
    n = 0
    for i in links[::-1]:
        if i >= dimensions:
            n += 1
        else:
            break
    if n:
        links = links[:-n]
    '''
    
    #Reformat the coordinate
    new_location = [None for i in links]
    for i, j in enumerate(links):
        if j < dimensions:
            new_location[i] = coordinate[j]
        else:
            try:
                new_location[i] = default_location[i]
            except:
                new_location[i] = default_value
        
    return new_location
    
        
class MayaDraw(object):
    """Class to be used for Maya only.
    It handles building cubes and curves to visualise the maze.
    """
    
    import pymel.core as pm
    
    def __init__(self, generation):
        self._gen = generation
        self._cubes = []
        self._curves = []
        self._paths = []
        self._bounding_box = None
        self._links = range(4)
        self._time_mult = 3
    
    def cubes(self):
        """Draw cubes based on information from the nodes.
        As neighbour checking is spherical, there may be some 
        overlapping where corners meet.
        It is here you interpret the dimensions, where currently it has
        support for up to 4 (4th is used for keyframes).
        """
        
        self.remove(cubes=True, curves=False, paths=False, bounding_box=False)
        default_location = self._gen.nodes[0].location
                
        for node in self._gen.nodes:
            size = node.size * 1.98
            new_location = format_coordinate(node.location, self._links, default_location)
            
            #Create new cube
            new_cube = self.pm.polyCube(n='genCube{}'.format(node.id), w=size, h=size, d=size)[0]
            self.pm.move(new_cube, new_location[:3])
            self._cubes.append(str(new_cube))
            
            #Set attributes
            self.pm.addAttr(new_cube, sn='gen_id', ln='GenerationID', min=0, at='long')
            self.pm.setAttr('{}.gen_id'.format(new_cube), node.id)
            self.pm.addAttr(new_cube, sn='gen_dist', ln='GenerationDistance', min=0, at='long')
            self.pm.setAttr('{}.gen_dist'.format(new_cube), node.distance)
            self.pm.addAttr(new_cube, sn='gen_parent', ln='GenerationParent', dt='string')
            self.pm.setAttr('{}.gen_parent'.format(new_cube), str(node.parent))
            self.pm.addAttr(new_cube, sn='gen_child', ln='GenerationChildren', dt='string')
            self.pm.setAttr('{}.gen_child'.format(new_cube), ', '.join(map(str, node.children)))
            self.pm.addAttr(new_cube, sn='gen_adj', ln='GenerationNeighbours', min=0, at='long')
            self.pm.setAttr('{}.gen_adj'.format(new_cube), node.neighbours)
            
            #Set 4th dimension as keys
            if self._gen.dimensions > self._links[3]:
                time_gap = max(1, node.size * 2 * self._time_mult)
                time_start = new_location[3] * self._time_mult
                self.pm.setKeyframe(new_cube, at='v', value=0, time=time_start - time_gap)
                self.pm.setKeyframe(new_cube, at='v', value=1, time=time_start)
                self.pm.setKeyframe(new_cube, at='v', value=0, time=time_start + time_gap)

        self.bounding_box(time_slider=True, draw=False)

    
    def curves(self):
        """Draw curves by following the path of children.
        Start a new curve when the next ID is no longer a child.
        """
        self.remove(curves=True, cubes=False, paths=False, bounding_box=False)
        default_location = self._gen.nodes[0].location
        
        #Run through all the points
        curve_list = []
        for i, node in enumerate(self._gen.nodes):
            
            #Start a new curve
            if node.id not in self._gen.nodes[i-1].children:
                try:
                    start_point = self._gen.nodes[self._gen.nodes[i].parent].location
                    start_point = format_coordinate(start_point, self._links, default_location)[:3]
                except TypeError:
                    start_point = []
                curve_list.append([start_point])
            
            new_location = format_coordinate(node.location, self._links, default_location)[:3]
            curve_list[-1].append(new_location)
        
        #Convert to suitable coordinates and draw
        for curves in curve_list:
            if len(curves) > 1:
                converted_coordinates = [coordinate for coordinate in curves if coordinate]
                new_curve = self.pm.curve(p=converted_coordinates, d=1) 
                self._curves.append(str(new_curve))


    def path(self, start, end):
        """Draw path between two nodes."""
        nodes = self._gen.nodes
        path = recursive_pathfind(start, end, nodes)
        if path is None:
            return
            
        curve_points = [format_coordinate(nodes[node_id].location, 
                                          self._links, 
                                          self._gen.nodes[0].location)[:3]
                        for node_id in path]
        self._paths.append(str(self.pm.curve(p=curve_points, d=5)))

    def bounding_box(self, draw=True, time_slider=False):
        
        default_location = self._gen.nodes[0].location
        bb = [format_coordinate(i, self._links, default_location)
              for i in self._gen.get_bounds()]
        
        #Draw the box
        if draw:
            self.remove(bounding_box=True, curves=False, cubes=False, paths=False)
            mid_point = [i / 2 for i in (bb[0][i] + bb[1][i] for i in range(3))]
            bb_cube = self.pm.polyCube(w=bb[1][0] - bb[0][0],
                                       h=bb[1][1] - bb[0][1],
                                       d=bb[1][2] - bb[0][2])
            self.pm.move(bb_cube[0], mid_point)
            self._bounding_box = str(bb_cube[0])
        
        #Update the time slider
        if time_slider and self._gen.dimensions > self._links[3]:
            pm.playbackOptions(min=int(bb[0][3] * self._time_mult - 1), 
                               max=int(bb[1][3] * self._time_mult) + 2)
            pm.currentTime(int(bb[0][3] - 1) * self._time_mult)
        
        return bb


    def change_coordinate_links(self, x=None, y=None, z=None, t=None):
        """Update coordinate links using the input value.
        It will attempt to rearrange them based on the input to not 
        result in any duplicates.
        See format_coordinates() for how the links are used.
        """
        available_links = range(4)
        
        if x is not None:
            del available_links[available_links.index(x)]
        if y is not None:
            del available_links[available_links.index(y)]
        if z is not None:
            del available_links[available_links.index(z)]
        if t is not None:
            del available_links[available_links.index(t)]
        if x is None:
            x = available_links.pop(0)
        if y is None:
            y = available_links.pop(0)
        if z is None:
            z = available_links.pop(0)
        if t is None:
            t = available_links.pop(0)
        
        self._links = [x, y, z, t]
        

    def remove(self, cubes=True, curves=True, paths=True, bounding_box=True):
        """Remove any objects created by this class."""
        scene_objects = set(map(str, self.pm.ls()))
        delete_objects = []
        if cubes:
            for cube in self._cubes:
                if cube in scene_objects:
                    delete_objects.append(cube)
            self._cubes = []
        if curves:
            for curve in self._curves:
                if curve in scene_objects:
                    delete_objects.append(curve)
            self._curves = []
        if paths:
            for path in self._paths:
                if path in scene_objects:
                    delete_objects.append(path)
            self._paths = []
        if bounding_box:
            if self._bounding_box in scene_objects:
                delete_objects.append(self._bounding_box)
        self.pm.delete(delete_objects)
            

class Node(object):
    """Store the data for each node."""
    
    def __init__(self, id, location, size, distance=0, 
                 parent=None, children=None, tree=None, neighbours=None):
        self.id = id
        self.location = tuple(location)
        self.size = size
        self.parent = parent
        self.distance = distance
        self.children = children if children else []
        self.tree = tree
        self.neighbours = neighbours
        
    def __repr__(self):
        return ('Node(id={x.id}, ' 
                     'tree={x.tree}, '
                     'distance={x.distance}, '
                     'location={x.location}, '
                     'size={x.size}, '
                     'parent={x.parent}, '
                     'children={x.children}, '
                     'neighbours={x.neighbours}').format(x=self)
    
    def update_neighbours(self):
        self.neighbours = len(self.children) + (self.parent is not None)
                     
    def update_parent(self, parent, node_list):
        """Set a new parent and calculate the distance from origin."""
        if parent < 0:
            parent = None
        self.parent = parent
        try:
            self.distance = node_list[parent].distance + 1
        except TypeError:
            self.distance = 0


def recursive_pathfind(start, end, node_list, _path=[], _reverse=True, _last_id=None):
    """Recursively find a path between two nodes."""
    _path = _path + [start]
    
    #Path complete
    if start == end:
        return _path
        
    #Search parents
    if _reverse:
        parent = node_list[start].parent
        if parent is not None:
            found_path = recursive_pathfind(parent, end, node_list,
                                            _path=_path, _reverse=True, _last_id=start)
            if found_path is not None:
                return found_path
                
    #Search children
    for node_id in node_list[start].children:
        if node_id != _last_id:
            found_path = recursive_pathfind(node_id, end, node_list, 
                                            _path=_path, _reverse=False, _last_id=start)
            if found_path is not None:
                return found_path
    return None
        

class CoordinateToSegment(object):
    """Class used for the tree calculations.
    Its main purpose is to find which segment a node would be in, and
    generate the path to it.
    """
    def __init__(self, dimensions, tree_data):
        self.td = tree_data
        self.dimensions = dimensions
        self._range = range(dimensions)
        n = 0
        
        #Build index of paths
        self.paths = {}
        for path in self._paths():
            self.paths[tuple(path)] = n
            n += 1

    def convert(self, coordinates, point_size):
        """Convert a coordinate into segments."""
        
        if len(coordinates) != self.dimensions:
            raise ValueError('invalid coordinate size')
        
        #Find path to each coordinate
        segments = []
        for i in self._range:
            segments.append(self._find_segment(coordinates[i], point_size))
        
        #Trim them all to the same length
        min_len = min(len(i) for i in segments)
        segments = [tuple(i[:min_len]) for i in segments]
        
        #Calculate the path IDs
        path = [self.paths[i] for i in zip(*segments)]
        return path

    def reverse(self, segment):
        """Calculate the coordinates from a segment.
        This only gives a rough value, and is only needed for debugging.
        """
        #Find path from the path index IDs
        segments = [k for i in segment for k, v in self.paths.iteritems() if v == i]
        
        #Split into separate coordinates
        joined_segments = []
        for i in range(self.dimensions):
            joined_segments.append([j[i] for j in segments])
            
        #Calculate where the coordinate is following the path
        totals = []
        for coordinate in joined_segments:
            n = self.td.size - 1
            total = 0
            for i in coordinate:
                total += i * pow(2, n)
                n -= 1
            totals.append(total)
        print totals
            
    def _paths(self, current_path=None, current_level=0, directions=(-1, 1)):
        """Generate a list of paths in the current dimension.
        This is used to get the path index.
        """
        if current_path is None:
            current_path = []
        if current_level == self.dimensions:
            return [current_path]
        
        #Repeat recursively until editing current_path[-1]
        return_path = []
        for i in directions:
             return_path += self._paths(current_path + [i], current_level + 1, 
                                        directions=directions)
             
        return return_path

    def _find_segment(self, coordinate, point_size):
        """Convert a number into the correct segment.
        If the maximum tree size changes, this needs to be recalculated.
        This runs until either the minimum size has been hit, or the 
        node is overlapping multiple segments.
        """
        total = 0
        path = []
        coordinate_sort = sorted((coordinate - point_size, coordinate + point_size))
        
        for i in range(self.td.size - self.td.min - 1):
            current_amount = pow(2, self.td.size - i - 1)
            
            #Detect whether to end or which way to continue
            if coordinate == total or coordinate_sort[0] <= total <= coordinate_sort[1]:
                return path
            elif coordinate_sort[1] < total:
                total -= current_amount
                path.append(-1)
            elif coordinate_sort[0] > total:
                total += current_amount
                path.append(1)
            else:
                raise ValueError('unknown segment error')
                
        return path


def get_recursive_items(tree, items=None):
    """Iterate through a list to get all recursive items."""
    if items is None:
        items = []
    try:
        for branch in tree:
            items += get_recursive_items(branch)
    except TypeError:
        items += tree
    return items


class TreeData(object):
    """Class to store the tree of points.
    It can work in any dimension, and dynamically grows when needed.
    """

    def __init__(self, generation, start_size, min_size=None):
        self._gen = generation
        self._conversion = CoordinateToSegment(self._gen.dimensions, self)
        if min_size is None:
            min_size = start_size
        self.size = start_size
        self.min = min_size
        self._branch_length = range(len(self._conversion.paths) + 1)
        self.data = [[] for i in self._branch_length]
    
    def adjust_size(self, coordinate):
        """Increase the size of the tree if needed.
        If the size does change, everything is recalculated.
        """
        start_size = self.size
        highest_coord = max(coordinate)
        lowest_coord = min(coordinate)
        
        #Increment by 1 until the size fits
        max_range = pow(2, self.size)
        while max_range < highest_coord or -max_range > lowest_coord:
            self.size += 1
            max_range = pow(2, self.size)
        if self.size - start_size:
            self.recalculate()
    
    def recalculate(self):
        """Recalculate the path to every point."""
        self.data = [[] for i in self._branch_length]
        for node in self._gen.nodes:
            path = self.calculate(node.location, node.size, check_size=False)
            self.add(node, path)
    
    def add(self, node, path):
        """Add a node to the tree."""
        node.tree = path
        self._recursive_branch(path)[0][-1].append(node.id)

    def calculate(self, location, size, check_size=True):
        """Calculate the path to a point with location and size."""
        if check_size:
            self.adjust_size(location)
        path = self._conversion.convert(location, size)
        return path

    def near(self, path):
        """Find all nodes near a path for collision checking.
        Use TreeData.calculate to get the path.
        """
        branch, nodes = self._recursive_branch(path)
        nearby_nodes = get_recursive_items(branch)
        return nearby_nodes + nodes
    
    def _recursive_branch(self, path):
        """Follows a recursive path to get part of a list.
        If the path goes deeper than the list, new branches of the list
        will be created.
        For collision check purposes, a list of all items found going 
        to that branch is also returned.
        """
        branch = self.data
        nodes = []
        
        for branch_id in path:
            nodes += branch[-1]
            
            #Create new branch if it doesn't exist
            if not branch[branch_id]:
                branch[branch_id] = [[] for i in self._branch_length]
                
            branch = branch[branch_id]
        return branch, nodes
       

class GenerationCore(object):
    """Create and store the main generation."""
    
    def __init__(self, dimensions, size=1, min_size=None, multiplier=0.99, 
                 bounds=None, max_retries=None, _nodes=None, _tree_data=None):
        self.nodes = [] if _nodes is None else _nodes
        self.dimensions = dimensions
        self.range = range(dimensions)
        self.directions = self._possible_directions()
        
        self.size = max(0.001, size)
        self.bounds = bounds
        self.retries = max_retries
        self.multiplier = max(0.001, multiplier)
        
        if self.retries is None:
            self.retries = self.dimensions
        
        #Check the bounds are in the correct format
        if self.bounds is not None:
            if len(self.bounds) != 2:
                raise ValueError('bounding box should contain 2 values')
            for item in self.bounds:
                if len(item) != self.dimensions:
                    raise ValueError('incorrect bounding box size')
        
        #Find out how small the tree needs to go
        if min_size is None:
            min_size = self.size / 20
        self.min_size = max(0.001, min_size)
        min_size_exp = 0
        while pow(2, min_size_exp) > self.min_size:
            min_size_exp -= 1
            
        #Make the tree cover everything without wasting space
        self.tree = TreeData(self, 0, min_size_exp)
        if _tree_data is not None:
            self.tree.data = _tree_data
    
    def _possible_directions(self):
        """Build a list of every direction the maze can move in."""
        directions = []
        for i in self.range:
            for j in (-1, 1):
                directions.append([j if i == n else 0 for n in self.range])
        return directions
    
    def generate(self, max_nodes=None, max_length=None, location=None, min_nodes=None, 
                 max_fails=500):
        """Main function to generate the maze."""
        
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
        
        #Make up other values if not specified
        if max_length is None:
            max_length = max_nodes // 5
        
        #Check the location is in the correct format
        if location is None:
            location = [0.0 for i in generation.range]
        elif len(location) != self.dimensions:
            raise ValueError('invalid coordinates for starting location')
        
        #General range checks
        min_nodes = max(-1, min_nodes)
        max_nodes = max(min_nodes, max_nodes)
        max_length = max(1, max_length)
        
        #Start generation
        failed_nodes = current_retries = 0
        current_length = total_nodes = -1
        while (total_nodes + failed_nodes < max_nodes
               or total_nodes < min_nodes and failed_nodes < max_fails):
                
            #End the branch if too many fails
            if current_retries >= self.retries:
                current_length = max_length
                current_retries = 0
                failed_nodes += 1
                
            #End the branch if too long
            if current_length >= max_length:
                node_id = random.randint(0, total_nodes)
                current_length = 0
            else:
                node_id = total_nodes
            
            if node_id < 0:
                node_status = self._add_node(location=location)
            else:
                node_status = self._add_node(node_id=node_id)
                
            if node_status == -1:
                current_retries = self.retries
                failed_nodes += 1
            elif node_status == -2:
                current_retries += 1
            else:
                total_nodes += 1
                current_length += 1
                
    
    def _add_node(self, node_id=None, location=None):
        """Add individual node to the generation.
        Needs either a base node or a location to work off.
        """
        
        if node_id is None:
            if location is None:
                raise ValueError('location must be defined if no nodes exist')
            new_size = self.size
            new_location = location
            new_id = 0
            
        else:
            node_start = self.nodes[node_id]
                
            #Get the initial values to create the new node from
            new_size = node_start.size * self.multiplier
            new_id = self.nodes[-1].id + 1
            
            #End branch now if size is too small
            if new_size < self.min_size:
                return -1
                
            direction = random.choice(self.directions)
            new_location = tuple(a + b * node_start.size * 2 * max(1, self.multiplier)
                                 for a, b in zip(node_start.location, direction))
             
        #Check tree for collisions
        node_path = self.tree.calculate(new_location, new_size)
        near_nodes = self.tree.near(node_path)
        if self.collision_check(new_location, new_size, self.bounds, near_nodes):
            return -2
        
        #Add to original node as child
        try:
            node_start.children.append(new_id)
            node_start.neighbours += 1
        except UnboundLocalError:
            pass
        
        #Create a new node
        new_node = Node(new_id, new_location, new_size, neighbours=node_id is not None)
        new_node.update_parent(node_id, self.nodes)
        
        #Update values with new node
        self.nodes.append(new_node)
        self.tree.add(new_node, node_path)
        return new_id
        
    def add_branch(self, length=1, node_id=None):
        """Individually add a new branch to the generation."""
        total_directions = len(self.directions)
        
        #Find a node without any neighbours
        while node_id is None:
            node_id = random.choice(self.nodes).id
            if self.nodes[node_id].neighbours == total_directions:
                node_id = None
        
        #Draw a path until a limit is reached
        i = 0
        retries = 0
        while i < length:
            node_status = self._add_node(node_id)
            if node_status == -1 or retries > self.retries:
                return i
            elif node_status == -2:
                retries += 1
                continue
            else:
                node_id = node_status
                retries = 0
                i += 1
        return i
    
    
    def collision_check(self, location, size, bounds=None, node_ids=None):
        """Check a new node isn't too close to an existing one.
        
        The first calculation is a simple range check, if a bounding box
        has been defined.
        
        The second calculation iterates through all the nodes, and first
        checks that the maximum distance on a single plane isn't over 
        the combined node size. If it is within range, pythagoras is
        used to find and compare the squared distance.
        """
        
        #Get every node ID if not provided
        if node_ids is None:
            node_ids = range(len(self.nodes))
        
        #Bounding box search
        if bounds:
            for i in self.range:
                if not bounds[0][i] + size <= location[i] <= bounds[1][i] - size:
                    return True
        
        #Pythagoras search
        for node_id in node_ids:
            node = self.nodes[node_id]
            size_total = size + node.size
            distance = [abs(a - b) for a, b in zip(location, node.location)]
            
            #Skip before the calculation if the maximum distance is too far
            if max(distance) > size_total:
                continue
                
            distance_total = sum(pow(i, 2) for i in distance)
            if distance_total < pow(size_total, 2):
                return True
                
        return False
    
    def save(self, location):
        save_data = {'Bounds': self.bounds,
                     'Dimensions': self.dimensions,
                     'Min': self.min_size,
                     'Multiplier': self.multiplier,
                     'Nodes': self.nodes,
                     'Retries': self.retries,
                     'Size': self.size,
                     'Tree': self.tree.data}
        with open(location, 'w') as f:
            f.write(cPickle.dumps(save_data))
    
    @classmethod
    def load(cls, location):
        with open(location, 'r') as f:
            file_data = cPickle.loads(f.read())
        return cls(bounds=file_data['Bounds'],
                   dimensions=file_data['Dimensions'],
                   min_size=file_data['Min'],
                   multiplier=file_data['Multiplier'],
                   _nodes=file_data['Nodes'],
                   max_retries=file_data['Retries'],
                   size=file_data['Size'],
                   _tree_data=file_data['Tree'])

    def get_bounds(self):
        """Find the bounds of the generation, including the node size."""
        bounds = [[float('inf') for i in range(self.dimensions)], 
                  [-float('inf') for i in range(self.dimensions)]]
        for node in self.nodes:
            for i, coordinate in enumerate(node.location):
                if bounds[0][i] > coordinate:
                    try:
                        bounds[0][i] = coordinate - node.size[i]
                    except TypeError:
                        bounds[0][i] = coordinate - node.size
                elif bounds[1][i] < coordinate:
                    try:
                        bounds[1][i] = coordinate + node.size[i]
                    except TypeError:
                        bounds[1][i] = coordinate + node.size
        bounds = tuple(tuple(i) for i in bounds)
        return bounds
        

#Delete previous generation
try:
    draw.remove()
except NameError:
    pass

#Create new generation
dimensions = 4
generation = GenerationCore(dimensions, multiplier=0.98)
generation.generate(min_nodes=500, max_length=100, max_fails=2000)
generation.add_branch(100)

#Save/load generation
if False:
    import os
    file_location = os.path.expanduser('~') + '/MazeGen.cache'
    generation.save(file_locationz)
    generation = GenerationCore.load(file_location)

#Draw generation in 3D if in Maya
try:
    draw = MayaDraw(generation)
except ImportError:
    pass
else:
    draw.change_coordinate_links(x=3, t=2)
    draw.cubes()
    draw.curves()
    draw.path(0, generation.nodes[-1].id)
