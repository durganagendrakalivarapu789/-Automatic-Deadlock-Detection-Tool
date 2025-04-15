import json
from typing import List, Dict
import logging

class DeadlockDetector:
    def __init__(self, allocated: List[List[int]], requested: List[List[int]] = None, max: List[List[int]] = None, available: List[int] = None):
        if not (len(allocated) > 0 and len(allocated[0]) > 0):
            raise ValueError("Invalid input dimensions for allocated resources")
        if requested and (len(requested) != len(allocated) or len(requested[0]) != len(allocated[0])):
            raise ValueError("Invalid input dimensions for requested resources")
        if max and (len(max) != len(allocated) or len(max[0]) != len(allocated[0])):
            raise ValueError("Invalid input dimensions for max resources")
        if available and len(available) != len(allocated[0]):
            raise ValueError("Invalid input dimensions for available resources")
        
        self.allocated = allocated
        self.requested = requested
        self.max = max
        self.available = available or [0] * len(allocated[0])
        self.num_processes = len(allocated)
        self.num_resources = len(allocated[0])
        self.mode = 'single' if requested else 'multi'
    
    def detect_deadlock(self) -> Dict[str, any]:
        work = self.available.copy()
        finish = [False] * self.num_processes
        steps = []
        deadlocked_processes = []
        
        max_iterations = self.num_processes * 2
        iteration_count = 0
        
        progress = True
        while progress and iteration_count < max_iterations:
            progress = False
            iteration_count += 1
            
            for i in range(self.num_processes):
                if finish[i]:
                    continue
                
                can_allocate = True
                need_or_request = []
                if self.mode == 'single':
                    need_or_request = self.requested[i]
                    can_allocate = all(
                        self.requested[i][j] <= work[j] 
                        for j in range(self.num_resources)
                    )
                else:  # multi
                    need_or_request = [self.max[i][j] - self.allocated[i][j] for j in range(self.num_resources)]
                    can_allocate = all(
                        need_or_request[j] <= work[j] 
                        for j in range(self.num_resources)
                    )
                
                if can_allocate:
                    step = {
                        'process': i,
                        'request': need_or_request.copy(),
                        'allocated': self.allocated[i].copy(),
                        'before_available': work.copy(),
                        'after_available': None,
                        'description': f'Process P{i} can proceed and release resources.'
                    }
                    
                    for j in range(self.num_resources):
                        work[j] += self.allocated[i][j]
                    
                    step['after_available'] = work.copy()
                    steps.append(step)
                    
                    finish[i] = True
                    progress = True
        
        for i in range(self.num_processes):
            if not finish[i]:
                deadlocked_processes.append(i)
        
        return {
            'is_deadlock': len(deadlocked_processes) > 0,
            'deadlocked_processes': deadlocked_processes,
            'steps': steps
        }
    
    def save_scenario(self, filename: str):
        try:
            scenario = {
                'mode': self.mode,
                'allocated': self.allocated,
                'requested': self.requested,
                'max': self.max,
                'available': self.available
            }
            with open(filename, 'w') as f:
                json.dump(scenario, f, indent=2)
            print(f"Scenario saved successfully to {filename}")
        except IOError as e:
            logging.error(f"Error saving scenario: {e}")
    
    @classmethod
    def load_scenario(cls, filename: str) -> 'DeadlockDetector':
        try:
            with open(filename, 'r') as f:
                scenario = json.load(f)
            return cls(
                allocated=scenario['allocated'],
                requested=scenario.get('requested'),
                max=scenario.get('max'),
                available=scenario['available']
            )
        except (IOError, KeyError, json.JSONDecodeError) as e:
            logging.error(f"Error loading scenario: {e}")
            raise

def main():
    # Single mode example
    print("Single Mode Example:")
    allocated_single = [[0, 1, 0], [2, 0, 0], [3, 0, 2]]
    requested_single = [[0, 0, 5], [2, 0, 0], [0, 0, 2]]
    available_single = [0, 3, 0]
    detector_single = DeadlockDetector(allocated_single, requested_single, None, available_single)
    result_single = detector_single.detect_deadlock()
    print(f"Is Deadlock: {result_single['is_deadlock']}")
    print(f"Deadlocked Processes: {result_single['deadlocked_processes']}")
    for step in result_single['steps']:
        print(f"Process P{step['process']}: {step['description']}")

    # Multi mode example
    print("\nMulti Mode Example:")
    allocated_multi = [[0, 1, 0], [2, 0, 0], [3, 0, 2]]
    max_multi = [[7, 5, 3], [3, 2, 2], [9, 0, 2]]
    available_multi = [3, 3, 2]
    detector_multi = DeadlockDetector(allocated_multi, None, max_multi, available_multi)
    result_multi = detector_multi.detect_deadlock()
    print(f"Is Deadlock: {result_multi['is_deadlock']}")
    print(f"Deadlocked Processes: {result_multi['deadlocked_processes']}")
    for step in result_multi['steps']:
        print(f"Process P{step['process']}: {step['description']}")

if __name__ == '__main__':
    main()