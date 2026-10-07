# 🏥 Automated Nurse Rostering & Constraint Optimization Engine

An algorithmic AI scheduling engine designed to solve the NP-hard **Nurse Rostering Problem (NRP)** under complex labor laws, shift transition rules, and workforce capacity constraints using **Constraint Satisfaction Problems (CSP)** and **Anytime Stochastic Local Search**.

---

## 📌 Overview

Hospital workforce scheduling requires balancing strict operational rules (shift coverage, rest windows, pre-approved leaves, surgical presence) with nurse fairness and workload distribution.

This project implements a **2-Stage Hybrid Optimization Pipeline**:
1. **Part A (Feasibility Solver):** A day-by-day CSP recursive backtracking search with forward checking and capacity pruning to guarantee 100% legal schedule generation in $< 0.05\text{s}$.
2. **Part B (Soft Constraint Optimizer):** Combines greedy constructive shift prioritization with an anytime stochastic local search (hill climbing via shift swapping) to minimize shift variance penalties within a fixed time budget $T$.

---

## ⚙️ Problem Formulation

### 1. Hard Constraints (H1 – H9)
A schedule is valid if and only if all 9 hard constraints are strictly satisfied:
* **H1 (Role Domain):** Surgical block shifts (`B`, covering both Morning & Afternoon) are restricted to surgical nurses.
* **H2 (Morning Spacing):** No consecutive morning shifts ($\{M, B\} \to \{M, B\}$ is illegal).
* **H3 (Evening Recovery):** Morning shifts immediately after evening shifts ($E \to \{M, B\}$) are forbidden.
* **H4 (Exact Daily Coverage):** Exact staffing demands $(m, a, e)$ must be satisfied every day. On general days, $B = 0$.
* **H5 (Max Consecutive Work):** Every 6-day rolling window must contain at least one rest day (`R`).
* **H6 (Post-Block Recovery):** Shift `B` can only be followed by `R` or `E` on the next day.
* **H7 (Surgical Presence):** On every surgery day (`S`), at least one surgical nurse must be assigned to `B`.
* **H8 (Workload Limit):** Total shifts worked by any nurse cannot exceed $K$ (`B` counts as 2 shifts).
* **H9 (Leave Adherence):** Pre-approved leave days (`L`) must strictly be assigned Rest (`R`).

### 2. Optimization Objective (Soft Constraint)
The optimizer minimizes the variance across Morning ($M_i$), Afternoon ($A_i$), and Evening ($E_i$) shifts for each nurse:
$$\text{Cost} = \sum_{i=0}^{N-1} \Big( (M_i - A_i)^2 + (A_i - E_i)^2 + (E_i - M_i)^2 \Big)$$
A cost of **$0$** represents a perfectly balanced roster where $M_i = A_i = E_i$.

---

## 🚀 Architecture & Algorithms
