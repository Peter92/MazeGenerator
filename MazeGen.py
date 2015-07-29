from __future__ import division
import random, operator

def calculate_directions(dimensions):
    """Return a list of possible directions (non diagonal) for any dimensions.
    For example, in 2 dimensions, you can go up (0, 1), down (0, -1), left (-1, 0), or right (1, 0).
    """
    direction_list = []
    dimensions = int(dimensions)
    for i in range(dimensions):
        direction_positive = []
        direction_negative = []
        for j in range(dimensions):
            direction_value = int(i == j)
            direction_positive.append(direction_value)
            direction_negative.append(-direction_value)
        direction_list += [tuple(direction_positive), tuple(direction_negative)]
    return tuple(direction_list)


class MazeGen(object):
    def __init__(self):
        self.fork_dict = {}
        #self.fork_dict[coordinate] = (sequence_number, fork_number, size)
        self.failed_attempts = 0
    
    def calculate(self, fork_length, fork_number, dimensions, fork_start=None,
                  direction_retries=4):
        
        if not isinstance(fork_start, (tuple, list)) or len(fork_start) != dimensions:
            fork_start = [0]*dimensions
        
        #Initial calculations
        r_choice = random.choice
        self.direction_list = calculate_directions(dimensions)
        self.fork_dict[tuple(fork_start)] = (0, 0, 1)
        range_fork_number = tuple(range(fork_number))
        range_fork_length = tuple(range(fork_length))
        
        
        for f_n in range_fork_number:
            point_current = r_choice(fork_dict.keys())
            point_sequence = point_current[0]
            
            for f_l in range_fork_length:
                
                #Calculate new direction
                point_next = self._new_direction(point_current, direction_retries)
                if point_next is not None:
                    point_sequence += 1
                    point_current = point_next
                    self.fork_dict[point_current] = (point_sequence, f_n, 1)
                    
                    
        return self.fork_dict
    
    def _new_direction(self, point_current, direction_retries):
        for i in range(direction_retries):
            new_direction = r_choice(self.direction_list)
            new_coordinates = tuple(x+y for x, y in zip(point_current, new_direction))
            if new_coordinates not in self.fork_dict:
                return new_coordinates
            self.failed_attempts += 1


fork_length = 10
fork_number = 1
dimensions = 2
fork_dict = MazeGen().calculate(fork_length, fork_number, dimensions)


#Debug list
sorted_dict = sorted(fork_dict.items(), key=operator.itemgetter(1))
for key, value in sorted_dict:
    if value[1] == 0:
        print key, value
