from collections import deque
import random


# for shuffled index
def random_int(min: int, max: int, excluded_ints: deque = deque()):
    random_number = random.randint(min, max)
    while random_number in excluded_ints:
        random_number = random.randint(min, max)
    return random_number
