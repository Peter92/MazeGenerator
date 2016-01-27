from __future__ import division
'''
new point
convert to quad tree - 1035
search all recursive points - 10350, 10351, 10352, 10353
'''

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
                print 'problem' + str(total)
        return path


class TreeData:

    def __init__(self, start_size, min_size=None):
        if min_size is None:
            min_size = start_size
        self.size = start_size
        self.min = min_size
    
    def adjust_size(self, coordinate):
        start_size = self.size
        highest_coord = max(new_point)
        lowest_coord = min(new_point)
        max_range = 2 ** self.size
        while max_range < highest_coord or -max_range > lowest_coord:
            self.size += 1
            max_range = 2 ** self.size
        return self.size - start_size

new_point = (10.72, 10.32)
td = TreeData(1, -5)
td.adjust_size(new_point)


print 'tree size:' + str(td.size)

cts = CoordinateToSegment(2, td)
print cts.paths

print cts.convert(new_point, 0.005)
print cts.reverse(cts.convert(new_point, 0.005))
