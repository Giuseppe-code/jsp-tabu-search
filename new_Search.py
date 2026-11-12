from dataclasses import dataclass
import random as rd
import matplotlib.pyplot as plt

MAX_EVAL = 1000
OPTIMUM = 32
ELITE_SIZE = 7
N_MOVES = 5 # elementi del vicinato
INT_AT, DIV_AT = 10, 15 #dopo quante iterazioni iniziare 


@dataclass
class Operation:
    machine: int
    time: int
    name: str
    job_id: int
    n_operation: int

    def __str__(self):
        return self.name

    __repr__ = __str__


def read_files(operations):
    with open("jobs.txt", "r") as f:
        n_jobs, n_machines = map(int, f.readline().split())
        for job in range(n_jobs):
            valori = list(map(int, f.readline().split()))
            for k in range(n_machines):
                operations.append(Operation(
                    job_id=job,
                    n_operation=k,
                    machine=valori[k * 2],
                    time=valori[k * 2 + 1],
                    name=f"O{job}-{k}"))


def calculate_makespan(operations):
    machine = [0, 0, 0, 0]
    job_step = [0, 0, 0, 0]
    job_time = [0, 0, 0, 0]
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
                remaining.pop(i)
                break
    return max(machine)


def end_condition(num_iteration, current_value):
    return num_iteration >= MAX_EVAL or current_value <= OPTIMUM


def random_moves(operations):
    """N_MOVES mosse (i, j): l'elemento in i viene inserito in j."""
    return [tuple(rd.sample(range(len(operations)), 2)) for _ in range(N_MOVES)]


def elite_positions(elite_set):
    """Per ogni operazione, la posizione più frequente nelle soluzioni elite.
    Restituisce [(nome, posizione, frequenza)] ordinata dalla più frequente."""
    count = {}
    #calcolo per ogni operazione la frequenza tipo :(O1-1, 3) usato 5 volte
    for _, sol in elite_set:
        for pos, op in enumerate(sol):
            count[(op.name, pos)] = count.get((op.name, pos), 0) + 1
    best = {}
    for (name, pos), c in count.items():
        if name not in best or c > best[name][1]:
            best[name] = (pos, c)
    #ritorna (nome_operazione, posizione_preferita, conteggio) basandosi sull'ordinamento conteggio in ordine decrescente
    return sorted(((n, p, c) for n, (p, c) in best.items()), key=lambda x: -x[2])


def intensification_moves(operations, elite_set):
    """Mosse che portano le operazioni nella loro posizione più frequente nell'elite."""
    index = {op.name: i for i, op in enumerate(operations)}
    moves = [(index[name], pos)
             for name, pos, _ in elite_positions(elite_set)
             if index[name] != pos]
    return moves[:N_MOVES]


def select_neighbor(operations, moves, threshold, tabu_list, dim_tabu_list):
    best_candidate, best_makespan, best_inverse = None, float('inf'), None

    for index_take, index_push in moves:
        neighbor = operations.copy()
        elem = neighbor.pop(index_take)
        neighbor.insert(index_push, elem)

        new_makespan = calculate_makespan(neighbor)

        is_tabu = (elem.name, index_push) in tabu_list
        if is_tabu and new_makespan < threshold:  # aspirazione
            is_tabu = False

        if not is_tabu and new_makespan < best_makespan:
            best_makespan = new_makespan
            best_candidate = neighbor
            best_inverse = (elem.name, index_take)

    if best_candidate is not None:
        tabu_list.append(best_inverse)
        while len(tabu_list) > dim_tabu_list:
            tabu_list.pop(0)
        return best_candidate, False, best_makespan

    return operations, True, float('inf')


def add_set_to_elite(elite_set, operations, new_makespan):
    if any(sol == operations for _, sol in elite_set):
        return
    elite_set.append((new_makespan, operations.copy()))
    elite_set.sort(key=lambda x: x[0])
    while len(elite_set) > ELITE_SIZE:
        elite_set.pop()


def update_freq(freq_matrix, operations):
    for pos, op in enumerate(operations):
        freq_matrix[(op.name, pos)] = freq_matrix.get((op.name, pos), 0) + 1


def build_diversified_solution(operations, freq_matrix):
    available = operations.copy()
    rd.shuffle(available)  # spareggio casuale
    new_solution = []
    #avaible = i nomi delle operazioni, O1-1, O2-2 etc, ma nmano che scelgo un nuovo elemento lo rimuovo da operazioni, c
    # così non uso lo stesso elemento 2 volte, non ho una soluzione del tipo O1-1,O1-1,O1-1, O2-2..
    for pos in range(len(operations)):
        op = min(available, key=lambda o: freq_matrix.get((o.name, pos), 0))
        available.remove(op)
        new_solution.append(op)
    return new_solution


def main(seed):
    operations = []
    read_files(operations)
    rd.seed(seed)
    rd.shuffle(operations)

    current_value = calculate_makespan(operations)
    num_iteration = 1
    tabu_list, elite_set, freq = [], [], {}
    dim_tabu_list = 5
    counter_no_increment = 0
    iteration_final = 1
    add_set_to_elite(elite_set, operations, current_value)

    history = [(num_iteration, current_value, current_value)]  # (valutazioni, corrente, best)
    events = []  # (valutazioni, tipo)
    while not end_condition(num_iteration, elite_set[0][0]) and num_iteration + N_MOVES <= MAX_EVAL:
        # scelta delle mosse: intensificazione guidata dall'elite, altrimenti casuale
        moves = []
        if counter_no_increment >= INT_AT and len(elite_set) >= 3:
            moves = intensification_moves(operations, elite_set)
        if not moves:
            moves = random_moves(operations)

        neighbor, all_tabu, new_makespan = select_neighbor(
            operations, moves, elite_set[0][0], tabu_list, dim_tabu_list)
        num_iteration += len(moves)

        if all_tabu:
            counter_no_increment += 1
        else:
            operations = neighbor.copy()
            update_freq(freq, operations)

            if new_makespan < elite_set[0][0]:
                iteration_final = num_iteration

            if new_makespan < current_value:   # migliora la soluzione precedente
                counter_no_increment = 0
                dim_tabu_list = 5
            else:
                counter_no_increment += 1

            current_value = new_makespan
            add_set_to_elite(elite_set, operations, new_makespan)

        history.append((num_iteration, current_value, elite_set[0][0]))

        # inizio intensificazione: tabu list più lunga e svuotata
        if counter_no_increment == INT_AT:
            events.append((num_iteration, "intensificazione"))
            dim_tabu_list = 12
            tabu_list.clear()

        # diversificazione: restart dalle frequenze minori
        if counter_no_increment >= DIV_AT and num_iteration + 1 <= MAX_EVAL:
            events.append((num_iteration, "diversificazione"))
            operations = build_diversified_solution(operations, freq)
            current_value = calculate_makespan(operations)  # costa 1 valutazione
            num_iteration += 1
            if current_value < elite_set[0][0]:
                iteration_final = num_iteration
            add_set_to_elite(elite_set, operations, current_value)
            history.append((num_iteration, current_value, elite_set[0][0]))
            tabu_list.clear()
            dim_tabu_list = 5
            counter_no_increment = 0

    print("\n--- RISULTATO FINALE ---")
    print(f"Makespan finale: {elite_set[0][0]}")
    print(f"Valutazioni totali: {num_iteration}")
    print(f"Trovata alla valutazione: {iteration_final}")
    print(f"Sequenza: {elite_set[0][1]}")
    print("Ottimo trovato" if elite_set[0][0] == OPTIMUM else "Ottimo non trovato")

    return elite_set[0], iteration_final, history, events


if __name__ == "__main__":
    results, evals, operations, runs = [], [], [], {}
    seeds = [1, 2026, 432526, 22032004, 9876543, 1231, 3214, 5435, 57658769, 532452]
    for s in seeds:
        best, it_final, hist, ev  = main(seed=s)
        results.append(best[0])
        runs[s] = (hist, ev)
        operations.append(best[1])
        evals.append(it_final)
    print("Makespan per run:", results)
    print("Media makespan:", sum(results) / len(results))
    print("Ultima iterazione con miglioramento per run:", evals)
    print("Media ultima iterazione con miglioramento:", sum(evals) / len(evals))
    for i in range(len(seeds)):
        print(f"{operations[i]} seed - {seeds[i]}")

    s = seeds[0]  # cambia indice per vedere un altro seed
    hist, ev = runs[s]
    x, cur, best_curve = zip(*hist)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.step(x, best_curve, where="post", lw=2, label="best globale")
    ax.plot(x, cur, alpha=0.3, label="soluzione corrente")

    for e, t in ev:
        if t == "intensificazione":
            ax.axvline(e, ls="--", color="green", alpha=0.7)
        else:
            ax.axvline(e, ls="--", color="red", alpha=0.7)
    # etichette in legenda (una sola volta)
    ax.plot([], [], ls="--", color="green", label="intensificazione")
    ax.plot([], [], ls="--", color="red", label="diversificazione")

    ax.axhline(32, color="k", ls=":", label="ottimo (32)")
    ax.set_title(f"Seed {s}")
    ax.set_xlabel("Valutazioni")
    ax.set_ylabel("Makespan")
    ax.legend()
    plt.savefig("grafico2.png", dpi=150)
    plt.show()