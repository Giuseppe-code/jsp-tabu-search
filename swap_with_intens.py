from dataclasses import dataclass
import random as rd
import matplotlib.pyplot as plt
import statistics
#0.61 elite=13 , int=10, div = 15, dim_tabu_list = 5, 8 in intensificazione
#0.58
#0.71
#0.77
#0.98 senza intensificazione eidversificazione
MAX_EVAL = 1000
OPTIMUM = 32
ELITE_SIZE = 10
N_MOVES = 5 
INT_AT, DIV_AT = 10, 15 # dopo quante iterazioni iniziare 


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
    """N_MOVES mosse (i, j): l'elemento in i viene scambiato (SWAP) con l'elemento in j."""
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
    a quello preferito dall'elite set, e genera le mosse per scambiarle (SWAP).
    """
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
                
                # Se l'elite set preferisce nettamente l'ordine inverso (op2 prima di op1)
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
        
        # --- MODIFICA: Applicazione dello SWAP invece dell'insert ---
        neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]

        new_makespan = calculate_makespan(neighbor)

        # --- MODIFICA: Identificativo mossa per la Tabu List ---
        # Salviamo la coppia di operazioni scambiate. Usiamo `sorted` 
        # così lo scambio (A, B) è considerato identico allo scambio (B, A)
        op1_name = operations[idx1].name
        op2_name = operations[idx2].name
        move_id = tuple(sorted([op1_name, op2_name]))

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

    current_value = calculate_makespan(operations)
    num_iteration = 1
    tabu_list, elite_set, freq = [], [], {}
    dim_tabu_list = 5
    counter_no_increment = 0
    iteration_final = 1
    
    # Inizializziamo l'elite set con la prima soluzione
    add_set_to_elite(elite_set, operations, current_value)

    # --- NOVITÀ: Variabili per tracciare l'ottimo locale corrente ---
    best_local_sol = operations.copy()
    best_local_make = current_value

    history = [(num_iteration, current_value, current_value)] 
    events = [] 
    
    while not end_condition(num_iteration, elite_set[0][0]) and num_iteration + N_MOVES <= MAX_EVAL:
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

            # 1. Se troviamo un NUOVO RECORD GLOBALE, lo salviamo subito
            if new_makespan < elite_set[0][0]:
                iteration_final = num_iteration
                add_set_to_elite(elite_set, operations, new_makespan)

            # 2. Aggiorniamo l'ottimo locale se troviamo qualcosa di meglio in questa "discesa"
            if new_makespan < best_local_make:
                best_local_make = new_makespan
                best_local_sol = operations.copy()

            if new_makespan < current_value:  
                counter_no_increment = 0
                if(dim_tabu_list<9):
                    dim_tabu_list =dim_tabu_list+1
            else:
                if(dim_tabu_list>5):
                    dim_tabu_list =dim_tabu_list-1
                counter_no_increment += 1

            current_value = new_makespan
            
            # (Rimosso l'add_set_to_elite ad ogni singola iterazione)

        history.append((num_iteration, current_value, elite_set[0][0]))

        # --- FASE DI INTENSIFICAZIONE ---
        if counter_no_increment == INT_AT:
            events.append((num_iteration, "intensificazione"))
            #tabu_list.clear()
            
            # Aggiungiamo all'Elite Set l'OTTIMO LOCALE in cui ci siamo appena incastrati
            add_set_to_elite(elite_set, best_local_sol, best_local_make)

        # --- FASE DI DIVERSIFICAZIONE ---
        if counter_no_increment >= DIV_AT and num_iteration + 1 <= MAX_EVAL:
            events.append((num_iteration, "diversificazione"))
            operations = build_diversified_solution(operations, freq)
            current_value = calculate_makespan(operations) 
            num_iteration += 1
            
            if current_value < elite_set[0][0]:
                iteration_final = num_iteration
                add_set_to_elite(elite_set, operations, current_value)
                
            history.append((num_iteration, current_value, elite_set[0][0]))
            #tabu_list.clear()
            counter_no_increment = 0
            
            # Reset dell'ottimo locale per la nuova discesa
            best_local_make = current_value
            best_local_sol = operations.copy()

    print("\n--- RISULTATO FINALE ---")
    print(f"Makespan finale: {elite_set[0][0]}")
    print(f"Valutazioni totali: {num_iteration}")
    print(f"Trovata alla valutazione: {iteration_final}")
    print(f"Sequenza: {elite_set[0][1]}")
    print("Ottimo trovato" if elite_set[0][0] == OPTIMUM else "Ottimo non trovato")

    return elite_set[0], iteration_final, history, events


if __name__ == "__main__":
    results, evals, operations, runs = [], [], [], {}

    seeds = [
    37, 814, 9028, 17, 34912, 6, 881, 2094, 53, 7120,
    954, 18, 305, 772, 419, 80, 263, 501, 62, 938,
    114, 58, 207, 883, 45, 912, 33, 670, 81, 299,
    704, 12, 856, 31, 940, 57, 188, 73, 415, 60,
    322, 49, 871, 26, 509, 84, 137, 95, 660, 21,
    893, 52, 140, 77, 368, 10, 925, 43, 681, 99,
    517, 36, 844, 22, 603, 79, 156, 48, 931, 65,
    279, 14, 802, 55, 390, 87, 123, 61, 964, 38,
    645, 29, 718, 40, 852, 16, 291, 74, 506, 92,
    183, 68, 977, 35, 420, 82, 314, 59, 769, 27,
    836, 41, 259, 93, 608, 15, 742, 50, 195, 86,
    471, 24, 916, 67, 383, 90, 528, 11, 867, 44,
    205, 76, 649, 32, 994, 53, 170, 85, 331, 62,
    950, 19, 563, 88, 217, 47, 806, 25, 489, 70,
    398, 64, 102, 96, 735, 28, 554, 71, 921, 39,
    627, 13, 891, 54, 460, 97, 233, 42, 784, 63,
    159, 81, 376, 20, 819, 69, 442, 98, 675, 34,
    885, 46, 510, 75, 134, 91, 903, 30, 268, 83,
    412, 60, 753, 17, 986, 56, 329, 84, 617, 21,
    746, 33, 198, 89, 541, 23, 870, 65, 404, 78,
    293, 72, 661, 45, 187, 94, 535, 12, 962, 51,
    911, 26, 840, 61, 309, 82, 724, 37, 153, 90,
    568, 49, 225, 99, 876, 14, 490, 73, 833, 58,
    130, 86, 792, 31, 455, 68, 918, 22, 647, 79,
    857, 50, 316, 77, 689, 43, 201, 95, 574, 16,
    379, 92, 583, 24, 942, 60, 115, 87, 708, 35,
    604, 11, 937, 55, 260, 81, 849, 40, 391, 74,
    241, 67, 478, 96, 713, 29, 596, 88, 127, 63,
    988, 38, 145, 70, 526, 15, 362, 93, 899, 46,
    523, 85, 701, 42, 190, 76, 955, 25, 438, 69,
    765, 19, 354, 91, 807, 34, 622, 80, 285, 57,
    109, 64, 880, 21, 475, 98, 739, 47, 164, 83,
    821, 48, 219, 75, 961, 13, 503, 66, 990, 32,
    456, 97, 673, 28, 324, 89, 178, 54, 631, 18,
    934, 30, 548, 82, 795, 41, 411, 99, 250, 71,
    287, 74, 906, 16, 532, 62, 865, 27, 710, 94,
    651, 23, 182, 95, 846, 51, 394, 78, 557, 14,
    318, 88, 729, 40, 150, 67, 983, 20, 484, 86,
    770, 44, 465, 81, 609, 36, 247, 92, 826, 59,
    142, 69, 851, 22, 974, 55, 688, 17, 303, 73,
    597, 15, 336, 90, 741, 49, 125, 84, 913, 39,
    830, 53, 992, 26, 271, 79, 560, 45, 789, 61,
    407, 96, 614, 33, 818, 12, 945, 68, 232, 87,
    968, 24, 176, 77, 585, 46, 381, 93, 654, 21,
    255, 70, 897]
   # Simula la creazione del file jobs.txt per evitare errori se non esiste localmente
   
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

    
    # results è la lista dei makespan finali ottenuti nel tuo main
    if len(results) > 1:
        deviazione_standard = statistics.stdev(results)
        print(f"Deviazione standard dei makespan: {deviazione_standard:.2f}")
        print("Media ultima iterazione con miglioramento:", sum(evals) / len(evals))
    else:
        print("Deviazione standard: N/A (serve più di un run)")
    s = seeds[0] 
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
    plt.savefig("grafico2.png", dpi=150)
    plt.show()
