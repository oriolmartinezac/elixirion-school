import argparse
from pycompss.api.task import task
from pycompss.api.api import compss_barrier
import redis
import time
import random

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_QUEUE = 'task_times'
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@task()
def dummy_task(task_id):
    """Simulates a computational task with random execution time."""
    execution_time = 2.0  # Simulate a task taking 0.5 to 2 seconds
    time.sleep(execution_time)
    print(f"Task {task_id} completed in {execution_time:.2f} seconds.")
    return execution_time

def parse_args():
    parser = argparse.ArgumentParser(description="PyCOMPSs Parallel Task Execution")
    parser.add_argument('-i', '--iterations', type=int, default=5, help="Number of iterations")
    parser.add_argument('-t', '--tasks', type=int, default=10, help="Number of parallel tasks per iteration")
    return parser.parse_args()

def main():
    args = parse_args()
    num_iterations = args.iterations
    num_tasks = args.tasks
    
    for i in range(num_iterations):
        print(f"Iteration {i + 1} - Launching {num_tasks} parallel tasks.")
        
        start_time = time.time()
        tasks = [dummy_task(j) for j in range(num_tasks)]
        
        compss_barrier()  # Wait for all tasks to complete
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        r.rpush(REDIS_QUEUE, elapsed_time)  # Push elapsed time to Redis
        print(f"Iteration {i + 1} completed in {elapsed_time:.2f} seconds.\n")

if __name__ == "__main__":
    main()
