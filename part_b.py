import sys
import csv
import json
import time
import random


def parse_input(input_csv):
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        row = next(reader)
    
        N = int(row['N'])
        D = int(row['D'])
        N_s = int(row['N_s'])
        N_g = int(row['N_g'])
        m = int(row['m'])
        a = int(row['a'])
        e = int(row['e'])
        T = float(row['T'])
        days = row['days']
        max_shifts = int(row['K'])
        leaves = row['leaves']
    return N, D, N_s, N_g, m, a, e, T, days, max_shifts, leaves


def is_surgical(nurse_id, N_s):
    return nurse_id < N_s


def on_leave(nurse_id, day, leaves, D):
    return leaves[nurse_id * D + day] == 'L'


class Nurse:
    def __init__(self, nurse_id, max_shifts):
        self.id = nurse_id
        self.last_shift = None
        self.consecutive_days = 0
        self.max_shifts = max_shifts
        self.shifts_done = 0
        self.rem_shifts = max_shifts
        self.counts = {'M': 0, 'A': 0, 'E': 0}

    def get_legal_shifts(self, day, day_type, leaves, D, N_s):
        # forced rest checks
        if on_leave(self.id, day, leaves, D) or self.consecutive_days == 5 or self.rem_shifts <= 0:
            return ['R']

        options = ['R']
        
        # single shifts
        if self.rem_shifts >= 1:
            if self.last_shift not in ['M', 'B', 'E']:
                options.append('M')
            if self.last_shift != 'B':
                options.append('A')
            options.append('E')

        # surgical block shift
        if (day_type == 'S' and is_surgical(self.id, N_s) and 
            self.rem_shifts >= 2 and self.last_shift not in ['M', 'B', 'E']):
            options.append('B')

        return options

    def apply_shift(self, shift):
        if shift == 'M':
            self.counts['M'] += 1
        elif shift == 'A':
            self.counts['A'] += 1
        elif shift == 'E':
            self.counts['E'] += 1
        elif shift == 'B':
            self.counts['M'] += 1
            self.counts['A'] += 1

        if shift == 'R':
            self.last_shift = 'R'
            self.consecutive_days = 0
        elif shift in ['M', 'A', 'E']:
            self.last_shift = shift
            self.consecutive_days += 1
            self.shifts_done += 1
            self.rem_shifts -= 1
        elif shift == 'B':
            self.last_shift = 'B'
            self.consecutive_days += 1
            self.shifts_done += 2
            self.rem_shifts -= 2

    def clone(self):
        copy_nurse = Nurse(self.id, self.max_shifts)
        copy_nurse.last_shift = self.last_shift
        copy_nurse.consecutive_days = self.consecutive_days
        copy_nurse.shifts_done = self.shifts_done
        copy_nurse.rem_shifts = self.rem_shifts
        copy_nurse.counts = self.counts.copy()
        return copy_nurse


def compute_cost(table, N, D):
    total_cost = 0
    for i in range(N):
        m = a = e = 0
        for d in range(D):
            s = table[i][d]
            if s in ('M', 'B'): m += 1
            if s in ('A', 'B'): a += 1
            if s == 'E': e += 1

        tot = m + a + e
        total_cost += 3 * (m**2 + a**2 + e**2) - (tot**2)
    return total_cost


def is_valid_sequence(nurse_id, row, D, leaves, max_shifts, N_s):
    # check leave days
    for d in range(D):
        if leaves[nurse_id * D + d] == 'L' and row[d] != 'R':
            return False

    # general nurse role
    if not is_surgical(nurse_id, N_s) and any(s == 'B' for s in row):
        return False

    # shift quota
    shifts_count = sum(2 if s == 'B' else (1 if s in ('M', 'A', 'E') else 0) for s in row)
    if shifts_count > max_shifts:
        return False

    # rolling 6-day rest
    for start in range(D - 5):
        if all(row[d] != 'R' for d in range(start, start + 6)):
            return False

    # day-to-day transitions
    for d in range(D - 1):
        s1, s2 = row[d], row[d + 1]
        if s1 in ('M', 'B') and s2 in ('M', 'B'):
            return False
        if s1 == 'E' and s2 in ('M', 'B'):
            return False
        if s1 == 'B' and s2 not in ('R', 'E'):
            return False

    return True


def solve(N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves):
    start_time = time.time()
    nurses = [Nurse(i, max_shifts) for i in range(N)]
    schedule = {}

    def fill_day(day):
        if day == D:
            return True

        day_type = days[day]
        b_choices = [1] if day_type == 'S' else [0]

        for b in b_choices:
            demands = {'B': b, 'M': m - b, 'A': a - b, 'E': e}
            cur_day = [None] * N

            def assign_nurse(idx):
                needed_slots = sum(demands.values())
                remaining_nurses = N - idx
                if needed_slots > remaining_nurses:
                    return False

                if idx == N:
                    if needed_slots == 0:
                        saved_nurses = [nurse.clone() for nurse in nurses]
                        for i in range(N):
                            nurses[i].apply_shift(cur_day[i])
                            schedule[f"N{i}_{day}"] = cur_day[i]

                        if fill_day(day + 1):
                            return True

                        for i in range(N):
                            nurses[i] = saved_nurses[i]
                    return False

                nurse = nurses[idx]
                allowed = nurse.get_legal_shifts(day, day_type, leaves, D, Ns)
                
                # sort working shifts by least worked
                priority_order = sorted(['M', 'A', 'E'], key=lambda s: nurse.counts[s])
                if 'B' in allowed:
                    priority_order = ['B'] + priority_order

                for s in priority_order:
                    if s in allowed and demands[s] > 0:
                        demands[s] -= 1
                        cur_day[idx] = s
                        if assign_nurse(idx + 1):
                            return True
                        demands[s] += 1

                if 'R' in allowed and (remaining_nurses - 1 >= needed_slots):
                    cur_day[idx] = 'R'
                    if assign_nurse(idx + 1):
                        return True

                return False

            if assign_nurse(0):
                return True

        return False

    if not fill_day(0):
        return {}

    # convert to table for local search
    table = [[schedule[f"N{i}_{d}"] for d in range(D)] for i in range(N)]
    current_cost = compute_cost(table, N, D)
    best_table = [row[:] for row in table]
    best_cost = current_cost

    time_limit = max(0.0, T - 1.5)
    while (time.time() - start_time) < time_limit and best_cost > 0:
        d = random.randint(0, D - 1)
        i, j = random.sample(range(N), 2)
        s_i, s_j = table[i][d], table[j][d]

        if s_i == s_j:
            continue

        if days[d] == 'S':
            surg_count = sum(
                1 for k in range(Ns)
                if (table[k][d] if k not in (i, j) else (s_j if k == i else s_i)) == 'B'
            )
            if surg_count == 0:
                continue

        sched_i = table[i][:]
        sched_i[d] = s_j
        if not is_valid_sequence(i, sched_i, D, leaves, max_shifts, Ns):
            continue

        sched_j = table[j][:]
        sched_j[d] = s_i
        if not is_valid_sequence(j, sched_j, D, leaves, max_shifts, Ns):
            continue

        table[i][d], table[j][d] = s_j, s_i
        new_cost = compute_cost(table, N, D)

        if new_cost <= current_cost:
            current_cost = new_cost
            if new_cost < best_cost:
                best_cost = new_cost
                best_table = [row[:] for row in table]
        else:
            table[i][d], table[j][d] = s_i, s_j

    return {f"N{i}_{d}": best_table[i][d] for i in range(N) for d in range(D)}


if __name__ == '__main__':
    N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves = parse_input(sys.argv[1])
    output_file = sys.argv[2]

    solution = solve(N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves)

    with open(output_file, 'w') as f:
        json.dump(solution, f)