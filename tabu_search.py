from dataclasses import dataclass
import random as rd
import matplotlib.pyplot as plt
import statistics
#0.61 elite=13 , int=10, div = 15, dim_tabu_list = 6, 11 
MAX_EVAL = 1000
OPTIMUM = 32
ELITE_SIZE = 13
N_MOVES = 4
INT_AT, DIV_AT = 10, 15 # dopo quante iterazioni iniziare 


@dataclass
class Operation:
    machine: int
    time: int
    name: str #per esempio J1-1
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
                    name=f"J{job}-{k}"))


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

def calculate_makespan_return_sequence(operations):
    machine = [0, 0, 0, 0]
    job_step = [0, 0, 0, 0]
    job_time = [0, 0, 0, 0]
    sequence = []
    remaining = operations.copy()
    while remaining:
        for i, op in enumerate(remaining):
            if job_step[op.job_id] == op.n_operation:
                start_time = max(job_time[op.job_id], machine[op.machine - 1])
                end_time = start_time + op.time
                job_time[op.job_id] = end_time
                machine[op.machine - 1] = end_time
                job_step[op.job_id] += 1
                sequence.append(op)
                remaining.pop(i)
                break
    return sequence

def end_condition(num_iteration, current_value):
    return num_iteration >= MAX_EVAL or current_value <= OPTIMUM


def random_moves(operations):
    """Ritorno una tupla contenente coppie di indici, ogni indice va da 0 a len(operation), ripeto l'operazione per il numero di mosse"""
    return [tuple(rd.sample(range(len(operations)), 2)) for _ in range(N_MOVES)]


def elite_precedences(elite_set):
    """
    Conta le precedenze relative: quante volte l'operazione A compare PRIMA 
    dell'operazione B nelle soluzioni elite.
    Per efficienza e località forte, analizziamo solo operazioni sulla STESSA MACCHINA.
    """
    prec_counts = {}
    for _, sol in elite_set:
        n = len(sol)
        for i in range(n):
            for j in range(i + 1, n):
                # Se due operazioni condividono la macchina, registriamo che sol[i] precede sol[j]
                if sol[i].machine == sol[j].machine:
                    pair = (sol[i].name, sol[j].name)
                    prec_counts[pair] = prec_counts.get(pair, 0) + 1
    return prec_counts


def intensification_moves(operations, elite_set):
    """
    Trova coppie di operazioni sulla stessa macchina il cui ordine attuale è opposto
    a quello preferito dall'elite set, e genera le mosse per scambiarle (Swap/Exchange).
    """
    #numero di volte in cui J1-1 precede J1-2 nell'elite
    prec_counts = elite_precedences(elite_set) 
    moves = []
    n = len(operations)
    
    # Analizziamo l'array corrente per cercare "inversioni" rispetto all'elite
    for i in range(n):
        for j in range(i + 1, n):
            op1 = operations[i]
            op2 = operations[j]
            
            if op1.machine == op2.machine:
                # Allo stato attuale op1 precede op2. 
                # Vediamo quante volte l'elite preferisce questo ordine o l'inverso.
                elite_prefers_op2_first = prec_counts.get((op2.name, op1.name), 0)
                elite_prefers_op1_first = prec_counts.get((op1.name, op2.name), 0)
                
                # Se nell'elite set abbiamo una preferenza nell'ordine (op2 prima di op1)
                if elite_prefers_op2_first > elite_prefers_op1_first:
                    # Calcoliamo un punteggio: più l'elite è d'accordo, più alto è lo score
                    score = elite_prefers_op2_first - elite_prefers_op1_first
                    moves.append((score, i, j))
                    
    # Ordiniamo le mosse dalla più "richiesta" dall'elite in giù
    moves.sort(key=lambda x: -x[0])
    
    # Restituiamo le migliori N_MOVES (scartando lo score, tenendo solo le tuple (i, j))
    return [(i, j) for score, i, j in moves[:N_MOVES]]


def select_neighbor(operations, moves, threshold, tabu_list, dim_tabu_list):
    best_candidate, best_makespan, best_tabu_move = None, float('inf'), None

    for idx1, idx2 in moves:
        neighbor = operations.copy()
        
        # Exchange Operator
        neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]

        new_makespan = calculate_makespan(neighbor)

        op1_name = operations[idx1].name
        op2_name = operations[idx2].name
        #la mossa swap e il suo inverso sono uguali, quindi li conto una volta
        move_id =  tuple(sorted((op1_name, op2_name)))

        is_tabu = move_id in tabu_list
        if is_tabu and new_makespan < threshold:  # aspirazione
            is_tabu = False

        if not is_tabu and new_makespan < best_makespan:
            best_makespan = new_makespan
            best_candidate = neighbor
            best_tabu_move = move_id

    if best_candidate is not None:
        tabu_list.append(best_tabu_move)
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
    rd.shuffle(available) 
    new_solution = []
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

    prec_value = calculate_makespan(operations)
    num_iteration = 1
    tabu_list, elite_set, freq = [], [], {}
    dim_tabu_list = 6
    counter_no_increment = 0
    iteration_final = 1

    #inizializzazione elite_Set
    add_set_to_elite(elite_set, operations, prec_value)

    best_local_sol = operations.copy()
    #miglior makespan ottenuto nelle iterazioni, quando diversifico (ricomincio) lo resetto
    best_local_make = prec_value

    #per mat_plot_lib, funzione, momento di intensificazione / diverisficazione
    history = [(num_iteration, prec_value, prec_value)] 
    events = [] 
    
    while not end_condition(num_iteration, elite_set[0][0]) and num_iteration + N_MOVES <= MAX_EVAL:
        moves = []
        if counter_no_increment >= INT_AT:
            moves = intensification_moves(operations, elite_set)
        else:
            moves = random_moves(operations)

        neighbor, all_tabu, new_makespan = select_neighbor(
            operations, moves, elite_set[0][0], tabu_list, dim_tabu_list)
        num_iteration += len(moves)

        if all_tabu:
            counter_no_increment += 1
        else:
            operations = neighbor.copy()
            update_freq(freq, operations)

            # 1. Se troviamo un NUOVO RECORD GLOBALE, lo salviamo subito
            if new_makespan < elite_set[0][0]:
                iteration_final = num_iteration
                add_set_to_elite(elite_set, operations, new_makespan)

            #ottimo trovato nell'iterazione
            if new_makespan < best_local_make:
                best_local_make = new_makespan
                best_local_sol = operations.copy()

            #l'algoritmo sta migliorando, quindi adatto la tabu list
            if new_makespan < prec_value:  
                counter_no_increment = 0
                if(dim_tabu_list<11):
                    dim_tabu_list =dim_tabu_list+1
            else: #qui non migliora
                if(dim_tabu_list>6):
                    dim_tabu_list =dim_tabu_list-1
                counter_no_increment += 1

            prec_value = new_makespan
            

        history.append((num_iteration, prec_value, elite_set[0][0]))

        #INTENSIFICAZIONE
        if counter_no_increment == INT_AT:
            events.append((num_iteration, "intensificazione"))
            #aggiungo l'ottimo all'elite
            add_set_to_elite(elite_set, best_local_sol, best_local_make)


        #DIVERSIFICAZIONE
        if counter_no_increment >= DIV_AT and num_iteration + 1 <= MAX_EVAL:
            events.append((num_iteration, "diversificazione"))
            operations = build_diversified_solution(operations, freq)
            prec_value = calculate_makespan(operations) 
            num_iteration += 1
            
            if prec_value < elite_set[0][0]:
                iteration_final = num_iteration
                add_set_to_elite(elite_set, operations, prec_value)
                
            history.append((num_iteration, prec_value, elite_set[0][0]))
            tabu_list.clear()
            counter_no_increment = 0
            
            # Reset dell'ottimo locale per la nuova discesa
            best_local_make = prec_value
            best_local_sol = operations.copy()

    print(f"\n--- RISULTATI SEED {seed} ---")
    print(f"Makespan finale: {elite_set[0][0]}")
    print(f"Valutazioni totali: {num_iteration}")
    print(f"Trovata alla valutazione: {iteration_final}")
    print(f"Sequenza: {elite_set[0][1]}")
    print(f"Sequenza scritta correttamente", calculate_makespan_return_sequence(elite_set[0][1]))
    print("Ottimo trovato" if elite_set[0][0] == OPTIMUM else "Ottimo non trovato")

    return elite_set[0], iteration_final, history, events

if __name__ == "__main__":
    #guardare def main
    results, evals, operations, runs = [], [], [], {}
    seeds =[0, 17, 12423, 3, 865]
    #seeds = rd.sample(range(10000), 1000)


   
    for s in seeds:
        best, it_final, hist, ev  = main(seed=s)
        results.append(best[0])
        runs[s] = (hist, ev)
        operations.append(best[1])
        evals.append(it_final)

    print("---RISULTATI---")
    print("Ultima iterazione con miglioramento per run:", evals)
    
    print("Makespan per run:", results)
    print("Media makespan:", sum(results) / len(results))

    deviazione_standard = statistics.stdev(results)
    print(f"Deviazione standard dei makespan: {deviazione_standard:.2f}")
    print("Media ultima iterazione con miglioramento:", sum(evals) / len(evals))
    print("Run a 32:", results.count(OPTIMUM), "su", len(results))
    s = seeds[1] 
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
            
    ax.plot([], [], ls="--", color="green", label="intensificazione")
    ax.plot([], [], ls="--", color="red", label="diversificazione")

    ax.axhline(32, color="k", ls=":", label="ottimo (32)")
    ax.set_title(f"Seed {s}")
    ax.set_xlabel("Valutazioni")
    ax.set_ylabel("Makespan")
    ax.legend()
    plt.savefig("grafico1.png", dpi=150)
    plt.show()
