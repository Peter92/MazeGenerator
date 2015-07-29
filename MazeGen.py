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


class Curves(object):
    def __init__(self, point_dict, fork_list):
        self.point_dict = point_dict
        self.fork_list = fork_list
        self.sorted_dict = sorted(self.point_dict.items(), key=lambda e: e[1][1])
    
    def draw(self):

        last_fork = -1
        point_list = {}
        
        while self.sorted_dict:
            current_point = self.sorted_dict.pop(0)
            current_coordinates = current_point[0]
            current_sequence = current_point[1][0]
            current_fork = current_point[1][1]
            if current_fork != last_fork:
                self._pymel_curve(point_list, last_fork)
                last_fork = current_fork
                point_list = {}
            point_list[current_coordinates] = current_sequence
        self._pymel_curve(point_list, current_fork)
        
    def _pymel_curve(self, point_list, fork_number):
        point_list = sorted(point_list, key=point_list.get)
        if fork_number >= 0:
            point_list_sorted = [self.fork_list[fork_number]]+point_list
            
        if len(point_list) > 1:
            dimensions = len(point_list_sorted[0])
            if dimensions < 3:
                if dimensions == 2:
                    point_list_sorted = tuple((i[0], 0, i[1]) for i in point_list_sorted)
                else:
                    point_list_sorted = tuple((i[0], 0, 0) for i in point_list_sorted)
            elif dimensions > 3:
                point_list_sorted = tuple(i[:3] for i in point_list_sorted)
            
            new_curve = pm.curve(n='fork{}'.format(fork_number), p=point_list_sorted, d=1)


Curves(point_dict, fork_list).draw()
