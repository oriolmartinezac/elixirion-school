from pycompss.api.api import compss_barrier
import time
from pycompss.api.task import task
from scipy import linalg
import numpy as np
import ctypes

@task(returns=int)
def sleep_task():
    time.sleep(0.1)
    return 1

@task(returns=list)
def createBlock(BSIZE, MKLProc, diag):
    import os
    os.environ["MKL_NUM_THREADS"]=str(MKLProc)
    block = np.array(np.random.random((BSIZE, BSIZE)), dtype=np.double,copy=False)
    mb = np.matrix(block, dtype=np.double, copy=False)
    mb = mb + np.transpose(mb)
    if diag:
        mb = mb + 2*BSIZE*np.eye(BSIZE)
    return mb

@task(returns=np.ndarray)
def potrf(A, MKLProc):
    from scipy.linalg.lapack import dpotrf
    import os
    os.environ['MKL_NUM_THREADS']=str(MKLProc)
    A = dpotrf(A, lower=True)[0]
    return A

@task(returns=np.ndarray)
def solve_triangular(A, B, MKLProc):
    from scipy.linalg import solve_triangular
    from numpy import transpose
    import os
    os.environ['MKL_NUM_THREADS']=str(MKLProc)
    B = transpose(B)
    B = solve_triangular(A, B, lower=True)  # , trans='T'
    B = transpose(B)
    return B

@task(returns=np.ndarray)
def gemm(alpha, A, B, C, beta, MKLProc):
    from scipy.linalg.blas import dgemm
    from numpy import transpose
    import os
    os.environ['MKL_NUM_THREADS']=str(MKLProc)
    B = transpose(B)
    C = dgemm(alpha, A, B, c=C, beta=beta)
    return C

def genMatrix(MSIZE, BSIZE, MKLProc, A):
    for i in range(MSIZE):
        A.append([])
        for j in range(MSIZE):
            A[i].append([])
    for i in range(MSIZE):
        mb = createBlock(BSIZE, MKLProc, True)
        A[i][i]=mb
        for j in range(i+1,MSIZE):
            mb = createBlock(BSIZE, MKLProc, False)
            A[i][j]=mb
            A[j][i]=mb

def cholesky_blocked(MSIZE, BSIZE, mkl_threads, A):
    import os
    for k in range(MSIZE):
        # Diagonal block factorization
        A[k][k] = potrf(A[k][k], mkl_threads)
        # Triangular systems
        for i in range(k+1, MSIZE):
            A[i][k] = solve_triangular(A[k][k], A[i][k], mkl_threads)
            A[k][i] = np.zeros((BSIZE,BSIZE))
        # update trailing matrix
        for i in range(k+1, MSIZE):
            for j in range(i, MSIZE):
                A[j][i] = gemm(-1.0, A[j][k], A[i][k], A[j][i], 1.0, mkl_threads)
    return A

def parse_args():
    """
    Arguments parser.
    Code for experimental purposes.
    :return: Parsed arguments.
    """
    import argparse
    description = 'COMPSs Cholesky implementation'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-b', '--block_size', type=int, default=1024,
                        help='Block size'
                        )
    parser.add_argument('-m', '--matrix_size', type=int, default=6,
                        help='Matrix size'
                        )
    parser.add_argument('-s', '--sleep_tasks', type=int, default=0,
                        help='Number of WarmUp tasks'
                        )
    parser.add_argument('-mt', '--mkl_threads', type=int, default=1,
                        help='MKL number of threads'
                        )
    return parser.parse_args()


def main(block_size, matrix_size, sleep_tasks, mkl_threads):
    """
    This will be executed if called as main script.
    This code is used for experimental purposes.
    This code applies Cholesky Decomposition matrices.
    :param block_size: Size of the Block
    :param matrix_size: Size of the Matrix
    :param sleep_tasks: Number of WarmUp tasks
    :return: None
    """
    MSIZE = matrix_size
    BSIZE = block_size
    mkl_threads = mkl_threads
    
    for i in range(sleep_tasks):
        patata = sleep_task()

    compss_barrier()
    
    # Generate de matrix
    startTime = time.time()

    # Generate supermatrix
    A = []
    res = []
    genMatrix(MSIZE, BSIZE, mkl_threads, A)
    compss_barrier()

    initTime = time.time() - startTime
    startDecompTime = time.time()
    res = cholesky_blocked(MSIZE, BSIZE, mkl_threads, A)
    compss_barrier()

    decompTime = time.time() - startDecompTime
    totalTime = decompTime + initTime

    print("---------- Elapsed Times ----------")
    print("initT:{}".format(initTime))
    print("decompT:{}".format(decompTime))
    print("totalTime:{}".format(totalTime))
    print("-----------------------------------")

    f = open("execution_time.txt", "w")
    f.write(str(totalTime))
    f.close()

if __name__ == "__main__":
    opts = parse_args()
    main(**vars(opts))