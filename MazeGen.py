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
        self.point_dict = {}
        self.fork_list = []
        #self.point_dict[coordinate] = (sequence_number, fork_number, size)
        self.failed_attempts = 0
    
    def generate(self, fork_length, fork_number, dimensions, fork_start=None,
                  direction_retries=4):
        
        if not isinstance(fork_start, (tuple, list)) or len(fork_start) != dimensions:
            fork_start = [0]*dimensions
        
        #Initial calculations
        r_choice = random.choice
        self.direction_list = calculate_directions(dimensions)
        self.point_dict[tuple(fork_start)] = (0, -1, 1)
        range_fork_number = tuple(range(fork_number))
        range_fork_length = tuple(range(fork_length))
        add_fork = self.fork_list.append
        
        
        for f_n in range_fork_number:
            point_current = r_choice(self.point_dict.keys())
            point_sequence = self.point_dict[point_current][0]
            point_fork = self.point_dict[point_current][1]
            add_fork((point_fork, point_sequence))
            
            for f_l in range_fork_length:
                
                #Calculate new direction
                point_next = self._new_direction(point_current, direction_retries)
                if point_next is not None:
                    point_sequence += 1
                    point_current = point_next
                    self.point_dict[point_current] = (point_sequence, f_n, 1)
                    
                    
        return (self.point_dict, tuple(self.fork_list))
        
        
    def _new_direction(self, point_current, direction_retries):
        for i in range(direction_retries):
            new_direction = r_choice(self.direction_list)
            new_coordinates = tuple(x+y for x, y in zip(point_current, new_direction))
            if new_coordinates not in self.point_dict:
                return new_coordinates
            self.failed_attempts += 1


fork_length = 10
fork_number = 3
dimensions = 2
point_dict, fork_list = MazeGen().generate(fork_length, fork_number, dimensions)


#Debug list
sorted_dict = sorted(point_dict.items(), key=operator.itemgetter(1))
for key, value in sorted_dict:
    print key, value
print fork_list
