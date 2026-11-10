from dataclasses import dataclass
from collections import deque
import random as rd

@dataclass
class Operation:
    machine :int
    time : int
    name : str
    job_id :int 
    n_operation: int #the operations respect a sequence 
    def __str__(self):
        return self.name

    ##list print like the single print of operation
    __repr__ = __str__


def build_diversified_solution(operations, freq_matrix):
    new_solution = []
    available_ops = operations.copy()
    
    for pos in range(len(operations)):
        # Ordiniamo le operazioni disponibili in base a quanto POCO sono state in 'pos'
        available_ops.sort(key=lambda op: freq_matrix.get((op.name, pos), 0))
        
        # Scegliamo quella meno usata in questa posizione
        chosen_op = available_ops.pop(0)
        new_solution.append(chosen_op)
        
    return new_solution

def calculate_makespan(operations):
    machine=[0,0,0,0] ##time of every machine
    job_step=[0,0,0,0] #counter of the job, ex. first process of the first job
    job_time = [0,0,0,0]
    remaining = operations.copy()
    while(len(remaining)):
        for i in range(len(remaining)):
            op=remaining[i]
            if(job_step[op.job_id]==op.n_operation):
                #il job successivo non può partire se non ha finito quello vecchio (in un'altra macchina)
                start_time = max(job_time[op.job_id], machine[op.machine-1])
                end_time = start_time + op.time

                job_time[op.job_id] = end_time
                machine[op.machine-1] = end_time

                job_step[op.job_id] += 1
                print(op, end=" ")
                remaining.pop(i)
                break
    print("Tempo max", max(machine)) 
    return max(machine) # (4)
        
def get_random_swap_neighbor(operations):
    """
    Genera un vicino scambiando due posizioni casuali.
    """
    neighbor = operations.copy()
    n = len(neighbor)
    
    # rd.sample sceglie 2 indici distinti a caso nell'intervallo [0, n-1]
    i, j = rd.sample(range(n), 2)
    # Restituiamo la nuova soluzione e le operazioni coinvolte nello swap
    return i, j

def read_files(operations):
    f = open("jobs.txt", "r")
    line = f.readline()
    n_jobs, n_machines = map(int, line.split())
    print(f"n_job {n_jobs} n_macchine {n_machines}")
    for job in range(n_jobs):
            valori = f.readline()
            valori = list(map(int, valori.split()))
            for counter_sequence in range(n_machines):
                operations.append(Operation(job_id= job, n_operation=counter_sequence, machine=valori[counter_sequence*2], time=valori[counter_sequence*2+1], name=f"J{job}-{counter_sequence}"))
    for op in operations:
        print(op, end=" ")
    print("")


def end_condition(num_iteration, current_value):
    return num_iteration>=1000 or current_value<=32

def random_selection_neighbor(operations, threshold, tabu_list, dim_tabu_list):
    neighbor = operations.copy()

    index_take, index_push= get_random_swap_neighbor(operations)
    op_pair = (neighbor[index_push].name, neighbor[index_take].name) #"tabu list contenente le mosse inverse a quelle eseguite di recente"

    #max dimensione list

    elem = neighbor.pop(index_take)
    neighbor.insert(index_push, elem)

    new_makespan = calculate_makespan(neighbor)
    if op_pair not in tabu_list or new_makespan < threshold:
        tabu_list.append(op_pair)
        while len(tabu_list) > dim_tabu_list:
            tabu_list.pop(0)
        return neighbor, False, new_makespan
    print("coppia già generata")
    return operations, True, new_makespan

#top 5
def add_set_to_elite(elite_set, operations, new_makespan):
    elite_set.append((new_makespan,operations))
    elite_set.sort(key = lambda x : x[0])
    while(len(elite_set)>5):
        elite_set.pop()

def main():
    print("Dentro main")
    operations = []
    read_files(operations)

    num_iteration=0
    rd.seed(15)
    rd.shuffle(operations)
    print(operations)
    current_value=calculate_makespan(operations)
    index_take=0
    index_push=0
    repeat=True
    tabu_list=[]
    elite_set = []
    dim_tabu_list=5
    counter_no_increment=0
    #repeat
    iteration_final =0
    elite_set.append((operations,current_value))
    while not end_condition(num_iteration, current_value):
        repeat=True
        while(repeat and num_iteration<1000):
            neighbor, repeat, new_makespan =random_selection_neighbor(operations,current_value,tabu_list, dim_tabu_list)
            num_iteration+=1
        if current_value == new_makespan:
            counter_no_increment+=1
            print("Nessun incremento ", counter_no_increment)
        #intensification
        if(counter_no_increment>= 15):
            dim_tabu_list=10
            elite_chosed=rd.randint(0,len(elite_set))
            current_value,operations = elite_set[elite_chosed].copy() ##da qui
        #diversification
        if(counter_no_increment>=15):
            dim_tabu_list=15

        #new best
        if(new_makespan < current_value):
            dim_tabu_list=5
            counter_no_increment=0
            add_set_to_elite(elite_set, operations, new_makespan)
            current_value=new_makespan
            iteration_final=num_iteration
            operations=neighbor.copy()
        
        
    print(f"\n--- RISULTATO FINALE ---")
    print(f"Makespan ottimo/finale: {elite_set[0][1]}")
    print(f"Iterazioni totali: {num_iteration}")
    print(f"Soluzione trovata alla : {iteration_final}")
    print(f"Sequenza: {elite_set[0][0]}")


if __name__ == "__main__":
    main()
