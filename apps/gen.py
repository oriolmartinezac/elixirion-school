#!/usr/bin/python
#
#  Copyright 2002-2022 Barcelona Supercomputing Center (www.bsc.es)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# -*- coding: utf-8 -*-

import argparse
import random
import sys
import time
from pycompss.api.task import task
from pycompss.api.parameter import *
from pycompss.api.api import TaskGroup
from pycompss.api.api import compss_barrier_group
from pycompss.api.api import compss_wait_on
from pycompss.api.api import compss_barrier
import redis
import numpy as np

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_QUEUE = 'task_times'
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@task(returns=int)
def sleep_task():
    time.sleep(1)
    return 1

def getParents(cycle_start, population, target, retain=0.2):
    init_fitness_time = time.time()
    fitInd = [(p, fitness(p, target)) for p in population]
    #compss_barrier()
    end_fitness_time = time.time()
    print(f"FITNESS TIME IS: {end_fitness_time - init_fitness_time}")
    
    sortFitIndices(fitInd)

    compss_barrier()

    end_time = time.time()
    #
    ##r.set(REDIS_QUEUE, elapsed_time)
    #print(f"ELAPSED TIME IS: {end_time - cycle_start}")
    
    # CAPTURE TIME END
    numRetain = int(len(population) * retain)
    return [fitInd[i][0] for i in range(numRetain)], end_time


@task(fitInd=COLLECTION_INOUT)
def sortFitIndices(fitInd):
    sortFitInd = sorted(fitInd, key=lambda i: i[1])
    for i in range(len(fitInd)):
        fitInd[i] = sortFitInd[i]


@task(returns=list)
def mutate(p, seed):
    random.seed(seed)
    ind = random.randint(0, len(p) - 1)
    p[ind] = random.randint(min(p), max(p))
    return p


@task(returns=list)
def crossover(male, female):
    n = 350
    A = np.random.rand(n, n)
    B = np.random.rand(n, n)
    
    # Matrix multiplication (CPU-bound)
    C = np.dot(A, B)

    half = int(len(male) / 2)
    child = male[:half] + female[half:]
    return child


@task(returns=list)
def individual(size, seed):
    n = 1000
    A = np.random.rand(n, n)
    B = np.random.rand(n, n)
    
    # Matrix multiplication (CPU-bound)
    C = np.dot(A, B)

    random.seed(seed)
    return [random.randint(0, 100) for _ in range(size)]


def genPopulation(numIndividuals, size, seed):
    return [individual(size, seed + i) for i in range(numIndividuals)]


@task(returns=float)
def fitness(individual, target):
    n = 1000
    A = np.random.rand(n, n)
    B = np.random.rand(n, n)
    
    # Matrix multiplication (CPU-bound)
    C = np.dot(A, B)
    value = sum(individual)
    return abs(target - value)


@task(returns=1, population=COLLECTION_IN)
def grade(population, target):
    values = map(fitness, population, [target for _ in range(len(population))])
    return sum(values) / float(len(population))


def evolve(cycle_start, population, target, seed, retain=0.2, random_select=0.05, mutate_rate=0.01):
    # Get parents
    parents, end_time = getParents(cycle_start, population, target, retain)

    # Add genetic diversity
    for p in population:
        if p not in parents and random_select > random.random():
            parents.append(p)

    # Mutate some individuals
    for p in parents:
        if mutate_rate > random.random():
            p = mutate(p, seed)
            seed += 1
    random.seed(seed)

    # Crossover parents to create childrens
    childrens = []
    numParents = len(parents)
    while len(childrens) < len(population) - numParents:
        male = random.randint(0, numParents - 1)
        female = random.randint(0, numParents - 1)
        if male != female:
            childrens.append(crossover(parents[male], parents[female]))

    newpopulation = parents + childrens

    # Return population
    return newpopulation, end_time

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Genetic Algorithm Implementation with PyCOMPSs")
    parser.add_argument('-n', '--num_individuals', type=int, default=100,
                        help="Number of individuals in the population")
    parser.add_argument('-s', '--size', type=int, default=100,
                        help="Size of each individual (number of genes)")
    parser.add_argument('-x', '--target', type=int, default=200,
                        help="Target value for fitness function")
    parser.add_argument('-l', '--lifecycles', type=int, default=10,
                        help="Number of generations (life cycles)")
    parser.add_argument('-gf', '--get-fitness', type=str, choices=['True', 'False'], default="True",
                        help="Enable ('True') or disable ('False') fitness history (default: 'True').")
    parser.add_argument('-i', '--iterations', type=int, default=10,
                        help="Number of iterations to run")
    parser.add_argument('-st', '--sleep_tasks', type=int, default=0,
                        help='Number of WarmUp tasks'
                        )

    args = parser.parse_args()

    args.get_fitness = args.get_fitness == "True"

    return args

def main():
    # Input parameters
    args = parse_args()

    N = args.num_individuals # 100  # individuals
    size = args.size # 100  # size of individuals
    x = args.target # 200  # target
    lifeCycles = args.lifecycles # 10
    get_fitness = args.get_fitness # True or False
    iterations = args.iterations
    sleep_tasks = args.sleep_tasks

    seed = 1234
    random.seed(seed)


    print("----- PARAMS -----")
    print(f" - N: {N}")
    print(f" - size: {size}")
    print(f" - x: {x}")
    print(f" - lifeCycles: {lifeCycles}")
    print(f" - getFitness: {get_fitness}")
    print(f" - Iterations: {iterations}")
    print(f" - SleepTasks: {sleep_tasks}")
    print("------------------")

    for i in range(sleep_tasks):
        patata = sleep_task()

    compss_barrier()

    total_time = time.time()

    for n in range(iterations):
        print(f"iteration: {n}")
        iteration_time = time.time()

        init_time = time.time()

        st = time.time()
        p = genPopulation(N, size, seed)
        et = time.time()


        print("genPopulation: Elapsed Time {} (s)".format(et - st))
        if get_fitness:
            fitnessHistory = [grade(p, x)]

        for i in range(lifeCycles):

            cycle_start = time.time()

            p, end_time = evolve(init_time, p, x, seed)

            init_time = end_time

            seed += 1
            random.seed(seed)
            
            if get_fitness:
                fitnessHistory.append(grade(p, x))
                
            
            compss_barrier()

            #p = compss_wait_on(p)
            elapsed_time = time.time() - cycle_start
            r.set(REDIS_QUEUE, elapsed_time)
            print(f"ELAPSED TIME IS: {elapsed_time}")

        else:
            p = compss_wait_on(p)
            print("genAlgorithm: Elapsed Time {} (s)".format(time.time() - et))
            print("Final result: %s" % str(p))
            if get_fitness:
                fitnessHistory.append(grade(p, x))
                fitnessHistory = compss_wait_on(fitnessHistory)
                print("final fitness: {}".format(fitnessHistory))

        compss_barrier()

        print(f"Time Spent in iteration {time.time() - iteration_time}")

    print(f"TOTAL Time spent on computation {time.time() - total_time}")

if __name__ == "__main__":
    main()