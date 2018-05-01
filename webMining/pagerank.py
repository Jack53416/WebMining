import numpy as np
 
class PageRank_Matrix:
    "Power iteration with random teleports that addresses Spider trap problem or Dead end problem "
    beta = 0.85
    epsilon = 0.0001
 
    def __init__(self, beta=0.85, epsilon=0.0001):
        self.beta = beta
        self.epsilon = epsilon
 
    def distance(self, v1, v2):
        v = v1 - v2
        v = v * v
        return np.sum(v)
 
    def compute(self, G):
        "G is N*N matrix where if j links to i then G[i][j]==1, else G[i][j]==0"
        N = len(G)
        d = np.zeros(N)
        for i in range(N):
            for j in range(N):
                if (G[j, i] == 1):
                    d[i] += 1
            if d[i]==0:   # i is dead end, teleport always
                d[i] = N
 
        r0 = np.zeros(N, dtype=np.float32) + 1.0 / N
        # construct stochastic M
        M = np.zeros((N, N), dtype=np.float32)
        for i in range(N):
            if (d[i]==N):  # i is dead end
                for j in range(N):
                    M[j, i] = 1.0 / d[i]
            else:
                for j in range(N):
                    if G[j, i] == 1:
                        M[j, i] = 1.0 / d[i]
 
        T = (1.0 - self.beta) * (1.0 / N) * (np.zeros((N, N), dtype=np.float32) + 1.0)
        A = self.beta * M +  T
        print A
        while True:
            r1 = np.dot(A, r0)
            dist = self.distance(r1, r0)
            if dist < self.epsilon:
                break
            else:
                r0 = r1
 
        return r1

def executeAlgo(M):
    damping = 0.80
    error = 0.001
    N = M.shape[0]
    
    v = np.ones(N)
    v = v / np.linalg.norm(v, 1)
    last_v = np.full(N, np.finfo(float).max)
    print "1-N: ", 1.0/N
    for i in range(0, N):
        if sum(M[:, i]) == 0:
            M[:, i] = np.full(N, 1.0/N)
        
    
    M_hat = np.multiply(M, damping) + np.full((N,N), (1-damping)/N)
    print M_hat
    while np.linalg.norm(v - last_v) > error:
        last_v = v
        v = np.matmul(M_hat, v)
    
    return v

pr = PageRank_Matrix(beta = 0.8)

# Example extracted from 'Introduction to Information Retrieval'
G = np.array([[0,0,0,0,1],
              [0.5,0,0,0,0], 
              [0.5,0,0,0,0], 
              [0,1,0.5,0,0],
              [0,0,0.5,1,0]])
K = np.array([[0,  1, 0],
              [1,1, 0],
              [1, 0,  0]])
Ks = np.array([[0,  0.5, 0],
              [0.5,0.5, 0],
              [0.5, 0,  0]])
Ds = np.array([[0, 0, 0, 0, 0.25],
              [0, 0, 0, 0, 0.25],
              [0, 0, 0, 0, 0.25],
              [0, 0, 0, 0, 0.25],
              [1, 0, 0, 0, 0]])
print pr.compute(Ds)
print executeAlgo(Ds)
