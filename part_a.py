import sys 
import csv
import json

def parse_input(input_csv):
    """Reads the CSV and initializes problem variables."""
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        row = next(reader)
        print(row)
    
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

#check if nurse is surgical or not
def is_surgical(nurse_id,N_s):
    if(nurse_id < N_s):
        return True
    else:
        return False

#check if nurse is on leave
def is_nurse_on_leave(nurse_id,leaves,D,day):
    if(leaves[nurse_id*D+day] == "L"):
        return True
    else:
        return False

#Class of nurse and its attributes
class Nurse:
    def __init__(self,nurse_id, last_shift, consecutive_day_count, max_shift_limit):
        self.n_id = nurse_id
        self.ls = last_shift
        self.cdc = consecutive_day_count
        self.msl = max_shift_limit  
        self.shifts_worked = 0
        self.remaining_shifts = max_shift_limit

    #Check nurse availability for shifts
    def get_legal_shift(self, day, day_type, leaves, D, max_shifts, N_s):

        #Mandatory Rest Cases (return only ['R'])
        if is_nurse_on_leave(self.n_id, leaves, D, day):
            return ['R']
        if self.cdc == 5:
            return ['R']
        if self.remaining_shifts<=0:
            return ['R']

        #Build the list of allowed shifts
        legal = ['R']

        #Morning shift availability
        if self.remaining_shifts>=1 and self.ls not in ['M','B','E']:
            legal.append('M') 

        #Afternoon shift availability
        if self.remaining_shifts>=1 and self.ls != 'B':
            legal.append('A')

        #Evening shift availability
        if self.remaining_shifts>=1:
            legal.append('E')
        
        # nurse Can work in 'B, if:
        #  day_type is 'S'
        #  nurse is surgical 
        #  remaining_shifts >= 2
        #  last_shift was not 'M', 'B', or 'E'
        if(day_type == 'S' and
            is_surgical(self.n_id, N_s) and
              self.remaining_shifts >=2 and
                self.ls not in ['M', 'B', 'E']):
            legal.append('B')

        return legal

    #shift assignment
    def assign_shift(self, shift):
        if(shift == 'R'):
            self.ls = 'R'
            self.cdc = 0

        if(shift in ['M','A','E']):
            self.ls = shift
            self.cdc += 1
            self.shifts_worked += 1
            self.remaining_shifts -= 1
        
        if(shift == 'B'):
            self.ls = 'B'
            self.cdc += 1
            self.shifts_worked += 2
            self.remaining_shifts -= 2

    #save/restore the state of all nurses if need to backtrack
    def copy(self):
        new_nurse = Nurse(self.n_id, self.ls, self.cdc, self.msl)
        new_nurse.shifts_worked = self.shifts_worked
        new_nurse.remaining_shifts = self.remaining_shifts
        return new_nurse

#solve function    
def solve(N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves):
    nurses = [Nurse(nurse_id=i, last_shift=None, consecutive_day_count=0, max_shift_limit=max_shifts)
               for i in range(N)]
    schedule = {}
    def search_day(day):
        # Base Case: All days successfully scheduled!
        if day == D:
            return True
        
        day_type = days[day]
        # On surgery days ('S'), try b = 1; on general days ('G'), b = 0
        b_options = [1] if day_type == 'S' else [0]
        
        for b in b_options:
            needed = {'B': b, 'M': m - b, 'A': a - b, 'E': e}
            day_assignment = [None] * N
            def match_nurses(nurse_idx):
                total_needed = sum(needed.values())
                unassigned = N - nurse_idx
                
                # Pruning: Not enough unassigned nurses left to fill needed shifts
                if total_needed > unassigned:
                    return False
                
                # If all nurses for today have been assigned
                if nurse_idx == N:
                    if total_needed == 0:
                        # 1. Save backup of nurses' states
                        backup = [n.copy() for n in nurses]
                        
                        # 2. Apply assignments for this day
                        for i in range(N):
                            nurses[i].assign_shift(day_assignment[i])
                            schedule[f"N{i}_{day}"] = day_assignment[i]
                        
                        # 3. Recurse to next day
                        if search_day(day + 1):
                            return True
                        
                        # 4. Backtrack: restore nurse states if next day failed
                        for i in range(N):
                            nurses[i] = backup[i]
                    return False
                
                legal = nurses[nurse_idx].get_legal_shift(day, day_type, leaves, D, max_shifts, Ns)
                
                # Try assigning working shifts first ('B', 'M', 'A', 'E')
                for s in ['B', 'M', 'A', 'E']:
                    if s in legal and needed[s] > 0:
                        needed[s] -= 1
                        day_assignment[nurse_idx] = s
                        if match_nurses(nurse_idx + 1):
                            return True
                        needed[s] += 1 # backtrack count
                
                # Try assigning Rest ('R')
                if 'R' in legal and (unassigned - 1 >= total_needed):
                    day_assignment[nurse_idx] = 'R'
                    if match_nurses(nurse_idx + 1):
                        return True
                
                return False
            if match_nurses(0):
                return True
                
        return False
    if search_day(0):
        return schedule
    return {}   


if __name__ == '__main__': 
    N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves = parse_input(sys.argv[1])
    output_file = sys.argv[2]

    solution = solve(N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves)
    
    with open(output_file, 'w') as f:
        json.dump(solution, f)