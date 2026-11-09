from dataclasses import dataclass

@dataclass
class Operation:
    machine :int
    time : int
    name : str
    def __str__(self):
        return self.name

def read_files(operations):
    f = open("jobs.txt", "r")
    line = f.readline()
    n_jobs, n_machines = map(int, line.split())
    print(f"n_job {n_jobs} n_macchine {n_machines}")
    for job in range(n_jobs):
            valori = f.readline()
            valori = list(map(int, valori.split()))
            for machine in range(n_machines):
                operations.append(Operation(machine=valori[machine*2], time=valori[machine*2+1], name=f"J{job}-{machine}"))
    for op in operations:
        print(op, end=" ")
     
def main():
    print("Dentro main")
    operations = []
    read_files(operations)


if __name__ == "__main__":
    main()
