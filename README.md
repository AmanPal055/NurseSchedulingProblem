# 🏥 Automated Nurse Rostering & Constraint Optimization Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Algorithm](https://img.shields.io/badge/Algorithm-CSP%20%7C%20Local%20Search-green.svg)]()

An automated Artificial Intelligence scheduling engine designed to solve the NP-hard **Nurse Rostering Problem (NRP)** under complex labor regulations, shift transition dynamics, and workforce capacity limits. The project implements a **2-Stage Hybrid Optimization Pipeline** combining **Constraint Satisfaction Problem (CSP)** backtracking search with **Anytime Stochastic Local Search (Hill Climbing)**.

---

## 📌 Table of Contents
- [Overview](#-overview)
- [Problem Formulation](#-problem-formulation)
  - [Hard Constraints (H1–H9)](#1-hard-constraints-h1--h9)
  - [Soft Constraint Objective](#2-soft-constraint-objective)
- [Architecture & Algorithm Design](#-architecture--algorithm-design)
  - [Part A: Day-by-Day CSP Backtracking](#part-a-day-by-day-csp-backtracking)
  - [Part B: 2-Stage Progressive Optimization](#part-b-2-stage-progressive-optimization)
- [Experimental Results & Benchmarks](#-experimental-results--benchmarks)
- [Repository Structure](#-repository-structure)
- [Installation & Usage](#-installation--usage)
  - [Running the Solvers](#1-running-the-solvers)
  - [Verifying Solutions](#2-verifying-solutions)
  - [Visualizing the Roster](#3-visualizing-the-roster)
- [Authors & Acknowledgments](#-authors--acknowledgments)
- [License](#-license)

---

## 📖 Overview

Hospital workforce management requires generating staffing rosters over an $N \times D$ grid ($N$ nurses over $D$ days) that respect exact staffing demands, role restrictions, and employee fatigue limits, while ensuring equitable distribution of shifts across all personnel.

This solver operates under strict performance and architectural constraints:
* **Zero 3rd-party solver dependencies** (pure Python standard library).
* **Guaranteed constraint satisfaction** on large instances ($N \le 50, D \le 30$).
* **Anytime optimization** that maximizes roster fairness within dynamic time budgets $T$.

---

## ⚙️ Problem Formulation

### 1. Hard Constraints (H1 – H9)
A generated roster is valid if and only if all 9 operational constraints are strictly satisfied:

| ID | Constraint Name | Description |
| :---: | :--- | :--- |
| **H1** | **Role Domain** | Shift domain $\in \{M, A, E, R, B\}$. Block shift $B$ (covering both Morning and Afternoon) is restricted exclusively to surgical nurses ($i < N_s$). General nurses cannot take $B$. |
| **H2** | **Morning Spacing** | No consecutive morning shifts ($\{M, B\} \to \{M, B\}$ is illegal). |
| **H3** | **Evening Recovery** | An evening shift cannot be followed by a morning shift ($E \to \{M, B\}$ is forbidden). |
| **H4** | **Exact Coverage** | On every day $d$, exactly $m$ Morning, $a$ Afternoon, and $e$ Evening shifts must be filled. On General days ($G$), $B = 0$. |
| **H5** | **Rest Window** | Every rolling 6-day window must contain at least one Rest day ($R$); no nurse may work $\ge 6$ consecutive days. |
| **H6** | **Post-Block Recovery** | A block shift $B$ can only be followed on the next day by Rest ($R$) or Evening ($E$). |
| **H7** | **Surgical Presence** | On every Surgery day ($S$), at least one surgical nurse must be assigned to shift $B$. |
| **H8** | **Workload Quota** | Total shifts worked by any nurse across $D$ days cannot exceed $K$ ($B$ counts as 2 shifts). |
| **H9** | **Leave Adherence** | Pre-approved leave days ($L$) must strictly be assigned Rest ($R$). |

### 2. Soft Constraint Objective
The optimization objective penalizes variance between Morning ($M_i$), Afternoon ($A_i$), and Evening ($E_i$) shifts for each nurse:

$$\text{Cost} = \sum_{i=0}^{N-1} \Big( 3(M_i^2 + A_i^2 + E_i^2) - (M_i + A_i + E_i)^2 \Big) = \sum_{i=0}^{N-1} \Big( (M_i - A_i)^2 + (A_i - E_i)^2 + (E_i - M_i)^2 \Big)$$

* **Global Minimum:** $\text{Cost} = 0$ is achieved when all working nurses have equal counts across all shift types ($M_i = A_i = E_i$).

---

## 🚀 Architecture & Algorithm Design

```
[Input CSV Instance]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 1: Cost-Aware Greedy CSP Backtracking Search    │
│  • Day-by-Day column decomposition                     │
│  • Lookahead capacity pruning                          │
│  • Dynamic shift prioritization: sort(M,A,E by counts) │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
                  [Valid Initial Roster S₀] (Cost: ~88, <0.05s)
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 2: Stochastic Anytime Local Search              │
│  • Neighborhood: Uniform pair sampling (nurse i, j)    │
│  • Sequence Gatekeeper: is_valid_sequence check        │
│  • Hill Climbing: Accept swap if ΔCost <= 0            │
│  • Time Budget Guard: Auto-stops at (T - 1.5s)         │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
               [Optimized Final Output JSON] (Cost: ~18-36)
```

### Part A: Day-by-Day CSP Backtracking
* **State Tracking:** Nurses maintain internal state trackers recording `last_shift`, `consecutive_days`, `shifts_done`, and `rem_shifts`.
* **Column Decomposition:** Instead of assigning cell-by-cell ($5^{N \times D}$ combinations), assignments are solved day-by-day.
* **Capacity Lookahead Pruning:** If remaining unassigned nurses on day $d$ is less than the remaining required working shifts for the day, the branch is immediately pruned.

### Part B: 2-Stage Progressive Optimization
1. **Stage 1 (Cost-Aware Greedy Constructive Search):** When assigning a nurse, working shifts `['M', 'A', 'E']` are dynamically sorted by whichever shift type the nurse has worked the least so far. This immediately prevents workload skewing during construction.
2. **Stage 2 (Anytime Local Search Optimizer):** Iteratively samples random nurse pairs on random days, evaluates complete $D$-day feasibility using a fast sequence validator, and accepts moves that lower or maintain the overall cost until the time limit $T$ approaches.

---

## 📊 Experimental Results & Benchmarks

Evaluated against benchmark instances using `verifier.py`:

| Test Instance | Nurses ($N$) | Days ($D$) | Max Shifts ($K$) | Baseline CSP | + Greedy Ordering (Stage 1) | + Local Search (Stage 2 Final) | Total Cost Reduction |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`test1.csv`** | 18 | 9 | 6 | 184 | 88 | **36** | **-80.4%** |
| **`test2.csv`** | 39 | 4 | 4 | 88 | 88 | **24** | **-72.7%** |
| **`test3.csv`** | 23 | 6 | 2 | 20 | 20 | **18** | **-10.0%** |

*All generated schedules achieve 100% feasibility with 0 hard constraint violations.*

---

## 📁 Repository Structure

```
├── part_a.py           # Part A CSP Backtracking Feasibility Solver
├── part_b.py           # Part B Two-Stage Hybrid Optimizer (Greedy + Local Search)
├── verifier.py         # Official solution verification & cost evaluator
├── visualizer.py       # Terminal ANSI visualizer for shift tables
├── sample_test_cases/  # Benchmark CSV test instances
│   ├── test1.csv
│   ├── test2.csv
│   └── test3.csv
├── report.txt          # Technical algorithm report
└── group.txt           # Submission metadata
```

---

## 🛠️ Installation & Usage

### Prerequisites
* Python 3.10+ (Standard library only; no external package installations required).

### 1. Running the Solvers

#### Generate Feasible Schedule (Part A):
```bash
python3 part_a.py sample_test_cases/test1.csv out_a.json
```

#### Generate Optimized Schedule (Part B):
```bash
python3 part_b.py sample_test_cases/test1.csv out_b.json
```

### 2. Verifying Solutions
Verify that the output JSON satisfies all hard constraints (H1–H9) and check its cost:
```bash
python3 verifier.py sample_test_cases/test1.csv out_b.json
```
*Expected Output:*
```
VALID 36
```

### 3. Visualizing the Roster
Render a color-coded terminal view of the schedule:
```bash
python3 visualizer.py sample_test_cases/test1.csv out_b.json 9
```

---

## 👥 Authors
* **Aman**

---

## 📜 License
This project is open-source and available under the [MIT License](LICENSE).
