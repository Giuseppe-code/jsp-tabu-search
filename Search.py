from dataclasses import dataclass
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
                break;
    print("Tempo max", max(machine))
    return max(machine)
        


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

def end_condition(num_iteration, best_value):
    return num_iteration>=1000 or best_value<=32

def main():
    print("Dentro main")
    operations = []
    read_files(operations)

    num_iteration=0
    best_value=99999
    rd.seed(0)
    #rd.shuffle(operations)
    print(operations)
    calculate_makespan(operations)
    while(end_condition(num_iteration, best_value)):

        num_iteration+=1
        return


if __name__ == "__main__":
    main()
