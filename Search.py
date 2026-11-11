from dataclasses import dataclass
import random as rd

MAX_EVAL = 1000
OPTIMUM = 32


@dataclass
class Operation:
    machine: int
    time: int
    name: str
    job_id: int
    n_operation: int  # le operazioni di un job rispettano una sequenza

    def __str__(self):
        return self.name

    __repr__ = __str__


def read_files(operations):
    with open("jobs.txt", "r") as f:
        n_jobs, n_machines = map(int, f.readline().split())
        #print(f"n_job {n_jobs} n_macchine {n_machines}")
        for job in range(n_jobs):
            valori = list(map(int, f.readline().split()))
            for k in range(n_machines):
                operations.append(Operation(
                    job_id=job,
                    n_operation=k,
                    machine=valori[k * 2],
                    time=valori[k * 2 + 1],
                    name=f"J{job}-{k}"))
    for op in operations:
        print(op, end=" ")
    print("")


def calculate_makespan(operations):
    machine = [0, 0, 0, 0]   # tempo di ogni macchina
    job_step = [0, 0, 0, 0]  # prossima operazione di ogni job
    job_time = [0, 0, 0, 0]  # fine dell'ultima operazione di ogni job
    remaining = operations.copy()
    while len(remaining):
        for i in range(len(remaining)):
            op = remaining[i]
            if job_step[op.job_id] == op.n_operation:
                start_time = max(job_time[op.job_id], machine[op.machine - 1])
                end_time = start_time + op.time
                job_time[op.job_id] = end_time
                machine[op.machine - 1] = end_time
                job_step[op.job_id] += 1
                #print(op, end=" ")
                remaining.pop(i)
                break
    #print("Tempo: ", max(machine))
    return max(machine)


def end_condition(num_iteration, current_value):
    return num_iteration >= MAX_EVAL or current_value <= OPTIMUM


def get_random_insert_neighbor(operations):
    """Sceglie due posizioni distinte: l'elemento in i viene inserito in j."""
    i, j = rd.sample(range(len(operations)), 2)
    return i, j


def random_selection_neighbor(operations, threshold, tabu_list, dim_tabu_list):
    best_candidate = None
    best_makespan = float('inf')
    best_inverse = None

    for _ in range(5):
        index_take, index_push = get_random_insert_neighbor(operations)
        neighbor = operations.copy()
        elem = neighbor.pop(index_take)
        neighbor.insert(index_push, elem)

        new_makespan = calculate_makespan(neighbor)

        inverse_move = (elem.name, index_take)

        # tabu se rimette elem in una posizione vietata
        is_tabu = (elem.name, index_push) in tabu_list

        # aspirazione: batte il record globale
        if is_tabu and new_makespan < threshold:
            is_tabu = False

        if not is_tabu and new_makespan < best_makespan:
            best_makespan = new_makespan
            best_candidate = neighbor
            best_inverse = inverse_move

    if best_candidate is not None:
        tabu_list.append(best_inverse)
        while len(tabu_list) > dim_tabu_list:
            tabu_list.pop(0)
        return best_candidate, False, best_makespan

    print("Tutte le 3 mosse generate erano Tabu")
    return operations, True, float('inf')


# top 7
def add_set_to_elite(elite_set, operations, new_makespan):
    if any(sol == operations for _, sol in elite_set):
        return False  # duplicato
    elite_set.append((new_makespan, operations.copy()))
    elite_set.sort(key=lambda x: x[0])
    while len(elite_set) > 5:
        elite_set.pop()

def update_freq(freq_matrix, operations):
    for pos, op in enumerate(operations):
        freq_matrix[(op.name, pos)] = freq_matrix.get((op.name, pos), 0) + 1


def build_diversified_solution(operations, freq_matrix):
    new_solution = []
    available_ops = operations.copy()
    rd.shuffle(available_ops)  # spareggio casuale
    for pos in range(len(operations)):
        available_ops.sort(key=lambda op: freq_matrix.get((op.name, pos), 0))
        new_solution.append(available_ops.pop(0))
    return new_solution


def main(seed):
    operations = []
    read_files(operations)
    rd.seed(seed)
    rd.shuffle(operations)

    current_value = calculate_makespan(operations)
    num_iteration = 1  # la valutazione iniziale conta
    tabu_list, elite_set, freq = [], [], {}
    dim_tabu_list = 7
    counter_no_increment = 0
    iteration_final = 1
    add_set_to_elite(elite_set, operations, current_value)

    while not end_condition(num_iteration, elite_set[0][0]) and num_iteration + 5 <= MAX_EVAL:
        neighbor, all_tabu, new_makespan = random_selection_neighbor( operations, elite_set[0][0], tabu_list, dim_tabu_list)
        num_iteration += 5

        if all_tabu:
            counter_no_increment += 1
        else:
            operations = neighbor.copy()
            update_freq(freq, operations)
            if new_makespan < elite_set[0][0]:
                #print(f"---- Nuovo Record Globale: {new_makespan}")
                dim_tabu_list = 5
                counter_no_increment = 0
                iteration_final = num_iteration
            else:
                counter_no_increment += 1
                #print("Nessun incremento, contatore:", counter_no_increment)
            add_set_to_elite(elite_set, operations, new_makespan)

        # intensificazione, se ho 15 iterazioni senza incrementi
        if counter_no_increment == 35:
            dim_tabu_list = 12
            tabu_list.clear()
            operations = rd.choice(elite_set)[1].copy()

        # diversificazione
        if counter_no_increment >= 50 and num_iteration + 1 <= MAX_EVAL:
            operations = build_diversified_solution(operations, freq)
            calculate_makespan(operations)  # costa 1 valutazione
            num_iteration += 1
            tabu_list.clear()
            dim_tabu_list = 7
            counter_no_increment = 0

    print("\n--- RISULTATO FINALE ---")
    print(f"Makespan finale: {elite_set[0][0]}")
    print(f"Valutazioni totali: {num_iteration}")
    print(f"Trovata alla valutazione: {iteration_final}")
    print(f"Sequenza: {elite_set[0][1]}")
    print("Ottimo trovato" if elite_set[0][0] == OPTIMUM else "Ottimo non trovato")
    print("--- ELITE ---")
    for m, sol in elite_set:
        print(m, sol)

    return elite_set[0], iteration_final


if __name__ == "__main__":
    results = []
    evals = []
    for s in [9, 787678768, 4324234, 34214234, 3565724]:
        best, it_final = main(seed=s)
        results.append(best[0])
        evals.append(it_final)
    print("Makespan per run:", results)
    print("Media makespan:", sum(results) / len(results))
    print("Ultima iterazione con miglioramento per run:", evals)
    print("Media ultima iterazione con miglioramento:", sum(evals) / len(evals))