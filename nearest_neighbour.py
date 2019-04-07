"""Code for nearest neighbour calculations.

Old bits (https://codereview.stackexchange.com/questions/118299/n-dimensional-maze-generation-with-octrees-and-pathfinding):
    #Check tree for collisions
    node_path = self.tree.calculate(new_location, new_size)
    near_nodes = self.tree.near(node_path)
    if self.collision_check(new_location, new_size, self.bounds, near_nodes):
        return -2


    def collision_check(self, location, size, bounds=None, node_ids=None):
        '''Check a new node isn't too close to an existing one.

        The first calculation is a simple range check, if a bounding box
        has been defined.

        The second calculation iterates through all the nodes, and first
        checks that the maximum distance on a single plane isn't over 
        the combined node size. If it is within range, pythagoras is
        used to find and compare the squared distance.
        '''

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

"""
from __future__ import division

import itertools


def calculate_distance(start, end):
    return calculate_distance_squared(start, end) ** 0.5


def calculate_distance_squared(start, end):
    """Calculate the distance between two points."""
    return sum((i - j) ** 2 for i, j in zip(start, end))



class NdTree(object):
    """N-Dimensional tree similar to a quadtree/octree.

    The tree structure is lists of lists containing each branch,
    when the first list contains the point IDs in that tree.
    For example, a 2D tree would be like so:
    branch = [[branch1], [branch2], [branch3], [branch4], [value1, value2, ...]]

    The point will take the first branch it fully fits in.
    If it is crossing a chunk line, then it will be added to both chunks.
    """
    def __init__(self, dimensions=2, max_level=8, max_depth=None):
        """Setup the class and save some calculations.

        Parameters:
            dimensions (int): How many dimensions there are
            max_level (int): The size of a chunk (2^n)
            max_depth (int): How many branches to use
        """
        self._dimensions = dimensions
        self._max_level = max_level
        self._max_depth = max_depth or self._max_level      # If max_depth is empty, then set it to same as level

        self._tree = {}
        self._chunk_cache = {}
        self._point_data = []
        self._counter = 0

        # Do calculations here to reduce processing time by as much as possible
        adjusted_range = [self._max_level - self._max_depth + j for j in range(self._max_depth)]
        self._level_to_value = {i: 2 ** i for i in adjusted_range}                                  # Cache the 2^n values
        self._segments = self.level_to_value(self._dimensions)                                     # How many parts are in each branch
        self._chunk_size = self.level_to_value(self._max_level)                                    # The actual size of each chunk
        self._chunk_offset = self.level_to_value(self._max_level - 1)

        self._level_range = tuple(range(self._max_level))
        self._segments_range = tuple(range(self._segments))
        self._dimensions_range = tuple(range(self._dimensions))
        self._depth_range = tuple(range(self._max_depth))

        # Generate possible segments and their ID
        segments = [bin(i)[2:].zfill(self._dimensions) for i in self._segments_range]
        self._segment_lookup = {tuple(map(int, list(value))): i for i, value in enumerate(segments)}
    
    def get_chunk(self, coordinate):
        """Get the chunk that a coordinate is in.
        
        Returns:
            (chunk (int), offset (int))

        >>> tree = NdTree()
        >>> tree.get_chunk(0)
        (0, 128)
        >>> tree.get_chunk(255)
        (1, 127)
        >>> tree.get_chunk(-128)
        (0, 0)
        """
        if coordinate not in self._chunk_cache:
            div, remainder = divmod(coordinate + self._chunk_offset, self._chunk_size)
            div = int(div)
            self._chunk_cache[coordinate] = (div, remainder)
        return self._chunk_cache[coordinate]
    
    def segment_index(self, segment):
        """Find which segment a certain coordinate is in.
        Each coordinate must be either 0 or 1 as the tree has two branches in any direction.

        Returns:
            segment_index (int)

        >>> tree = NdTree(2)
        >>> tree.segment_index((0, 0))
        0
        >>> tree.segment_index((0, 1))
        1
        >>> tree.segment_index((1, 0))
        2
        >>> tree.segment_index((1, 1))
        3
        """
        return self._segment_lookup[segment]

    def level_to_value(self, level):
        """Cache the power calculations, every little helps."""
        try:
            return self._level_to_value[level]
        except KeyError:
            self._level_to_value[level] = 2 ** level
            return self._level_to_value[level]

    def _find_all_children(self, current_level):
        children = []
        if current_level:
            for next_level in current_level[:-1]:
                children += self._find_all_children(next_level)
            children += current_level[-1]
        return children

    def add_point(self, coordinates, radius=0):

        # Find the min/max values of each axis
        coordinate_radius = []
        for coordinate in coordinates:
            coordinate_radius.append((coordinate - radius, coordinate + radius))
        
        # Convert into a list of all coordinates
        bounding_box = itertools.product(*coordinate_radius)

        # Find the min/max chunk
        max_chunk = [-float('inf') for _ in self._dimensions_range]
        min_chunk = [float('inf') for _ in self._dimensions_range]
        max_offset = [-float('inf') for _ in self._dimensions_range]
        min_offset = [float('inf') for _ in self._dimensions_range]
        for edge_coordinates in bounding_box:
            for i, coordinate in enumerate(edge_coordinates):
                chunk, offset = self.get_chunk(coordinate)
                if chunk > max_chunk[i]:
                    max_chunk[i] = chunk
                    max_offset[i] = offset
                elif chunk == max_chunk[i] and max_offset[i] < offset:
                    max_offset[i] = offset
                if chunk < min_chunk[i]:
                    min_chunk[i] = chunk
                    min_offset[i] = offset
                elif chunk == min_chunk[i] and min_offset[i] > offset:
                    min_offset[i] = offset
        
        # Find which cunks the object is in
        chunk_limits = zip(min_chunk, (i+1 for i in max_chunk))
        try:
            chunk_range = (range(*limit) for limit in chunk_limits)
            chunks = set(itertools.product(*chunk_range))
        
        # Catch exception if the number of coordinates input is incorrect
        except TypeError:
            num_coordinates = len(coordinates)
            if num_coordinates != self._dimensions:
                raise ValueError('{} requires {} coordinate{} ({} given)'.format(
                    self.__class__.__name__,
                    self._dimensions,
                    '' if self._dimensions == 1 else 's',
                    num_coordinates)
                )
            raise

        print('Chunk(s): {}'.format(', '.join(map(str, chunks))))
        print('Min Offsets: {}'.format(min_offset))
        print('Max Offsets: {}'.format(max_offset))

        # Ignore the segment path if split over multiple chunks
        if len(chunks) > 1:
            segment_path = []

        # Calculate the segment path within the current chunk
        else:
            segment_paths = [[] for _ in self._dimensions_range]
            
            max_depth = None
            for i in self._dimensions_range:
                current_level = self._max_level
                current_centre = 2 ** (current_level - 1)
                for depth in self._depth_range:
                    # Stop if another coordinate got stuck at the same depth
                    if max_depth is not None and depth >= max_depth:
                        break

                    # Stop if the centre point is currently intersecting
                    if current_centre in (min_offset[i], max_offset[i]):
                        max_depth = depth
                        break
                    
                    #Find if the edges of the object cross over the centre
                    x_low = min_offset[i] > current_centre
                    x_high = max_offset[i] > current_centre
                    if x_low != x_high:
                        max_depth = depth
                        break

                    segment_paths[i].append(int(x_low))

                    # Add or remove to the centre point
                    current_level -= 1
                    if x_low:
                        current_centre += 2 ** current_level
                    else:
                        current_centre -= 2 ** current_level

            # Generate the tree path
            segment_path = [self.segment_index(i) for i in zip(*segment_paths)]

        # Find all the potential intersections
        possible_points = []
        for chunk in chunks:

            # Set the tree to the correct chunk
            try:
                current_dict = self._tree[chunk]
            except KeyError:
                current_dict = self._tree[chunk] = [[] for _ in self._segments_range] + [set()]

            # Navigate the tree to get down to the branch
            possible_points += list(current_dict[-1])
            for segment_index in segment_path:
                if not current_dict[segment_index]:
                    current_dict[segment_index] = [[] for _ in self._segments_range] + [set()]
                current_dict = current_dict[segment_index]
                possible_points += current_dict[-1]
        
            # Check any children in a smaller branch
            possible_points += self._find_all_children(current_dict)

            # Perform distance check (without square root as it's expensive)
            for point_id in possible_points:
                point_data = self._point_data[point_id]
                point_coordinates, point_radius = point_data

                radius_sq = (radius+point_radius) ** 2
                distance_sq = sum((a-b) ** 2 for a, b in zip(coordinates, point_coordinates))
                if distance_sq < radius_sq:
                    return None
        
            # Add current point to dictionary
            current_dict[-1].add(self._counter)

        # Add the point and increment the point ID
        self._counter += 1
        self._point_data.append([coordinates, radius])

        return self._counter


    def get_point(self, point_id):
        return self._point_data[point_id]


# Testing
if __name__ == '__main__':
    tree = NdTree(2, 8, 8)

    print tree.add_point((70, 37.5), 0)
    print tree.add_point((70, 37.5), 2)
    print tree.add_point((72, 37.5), 2)

    print tree.add_point((0, 0), 77)

    #print tree.add_point((385, 0, 0), 5)