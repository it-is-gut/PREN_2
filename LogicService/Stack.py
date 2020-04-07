from collections import deque
import time
import threading
import asyncio


class Stack:
    size = 100
    buf = deque()
    buf_lock = threading.Lock()
    min_front_val = 5
    min_height = 5
    min_side_val = 5
    history = 100

    # Need to add logic to keep the buffer flowing. As in if there is no more space remove
    # earlier elements and make space
    # Almost like a sliding window
    # This sliding window type thing has been implemented below in @evaluate_relevant_data()
    def push_to_stack(self, to_push):
        if len(self.buf) < self.size:
            self.buf.append(to_push)
        else:
            print("Increase stack size to accomodate more elements")
    def pop_from_stack(self):
        try:
            return self.buf.pop()
        except IndexError:
            # print("Stack is empty cannot pop")
            return None

    def get_val(self, index):
        lock = threading.Lock()
        lock.acquire()
        try:
            return self.buf[index]
        finally:
            lock.release()

    def process_data(self, data):
        pass

    def evaluate_relevant_data(self, new_data):
        '''
        Evaluate the data to see if it is relevant or not.
        :param new_data:
        Convention for new_data is
        (height, side distance, front distance)
        :return: str
        ==== Error Codes Retured ====
        Code 1 : new_data was not of type tuple
        Code 2 : new_data had more or less than 3 elements in it
        '''
        if isinstance(new_data, tuple):
            if len(new_data) == 3:
                if self.stack.buf[-1][0] == new_data[0] or self.stack.buf[-1][1] == new_data[1] or self.stack.buf[-1][2] == new_data[2]:
                    del new_data
                    return 'Data Evaluated. Irrelevant data.'
                else:
                    self.stack.push_to_stack(new_data)
                    if len(self.stack.buf) > self.history:                  # This is the boundary variable for when to start sliding. Can change this variable to create a bigger history
                        del self.stack.buf[0]                               # This is where the sliding window happens remove if unnecesary
                    return 'Data Evaluated. Relevant data'
            else:
                return 'Evaluation procedure ended with error code 2\n'
        else:
            return 'Evaluation procedure ended with error code 1\n'
