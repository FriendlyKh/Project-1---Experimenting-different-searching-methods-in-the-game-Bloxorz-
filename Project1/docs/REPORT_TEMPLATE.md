# Report Template & Video Guidelines (40 Points Total)

This document provides a structure and checklist for your team to write the **Report (30 pts)** and prepare the **Demo Video (10 pts)** as specified in Section 3.6 and Section 3.7 of the assignment.

---

## Part 1: Report Structure (30 Points)

### 1. Cover Page
- **University:** University of Science, VNU-HCM (Faculty of Information Technology)
- **Course:** CSC14003 - Introduction to Artificial Intelligence
- **Project 1:** Bloxorz Solver
- **Team Name / Group Number:**
- **Student Members:**
  - Student 1: [Full Name] - [Student ID]
  - Student 2: [Full Name] - [Student ID]
  - Student 3: [Full Name] - [Student ID]
  - Student 4: [Full Name] - [Student ID]
- **Public Video Link:** `https://youtu.be/...`

---

### 2. Project Planning & Task Distribution
*Must accurately reflect individual contributions (each member's final grade = Group Score × Completion %).*

| Member | Student ID | Assigned Modules & Tasks | Completion % |
| :--- | :--- | :--- | :--- |
| Student 1 | 22xxxxx1 | Game Engine, Orientation roll physics, Stage parser, State hashing | 100% |
| Student 2 | 22xxxxx2 | Search framework, Metrics profiling (`tracemalloc`), BFS, DFS | 100% |
| Student 3 | 22xxxxx3 | UCS with custom cost function, A* Search, Heuristic design & proofs | 100% |
| Student 4 | 22xxxxx4 | Pygame GUI, Animated replay, Benchmark runner, Matplotlib plotting | 100% |

---

### 3. Problem Formalization & Algorithm Description (10 Points)

#### 3.1 State Representation & Invariants
- Explain the $(B, \mathcal{M})$ state representation (`block` coordinates/orientation + `bridge_states` tuple).
- Explain why including the bridge configuration in the state hash is necessary (Page 4 FYI).
- Explain cycle avoidance using a hashable `set()` of visited states.

#### 3.2 Transitions & Actions
- Detail the 12 orientation roll transitions (include the transition table from `docs/ARCHITECTURE.md`).
- Describe switch triggering mechanics (soft vs heavy vs split).
- Describe split cubes and the adjacency rejoining condition.

#### 3.3 Search Algorithms
- **BFS (Breadth-First Search):** FIFO queue exploration, optimality for unit step cost.
- **DFS (Depth-First Search):** Stack-based exploration, cycle detection, depth limits.
- **UCS (Uniform-Cost Search):** Priority queue, cost function definition:
  - Formally define your cost function (e.g., $c_{\text{base}} = 1.0$, fragile penalty $+2.0$, switch bonus $-0.5$).
  - Justify why rolling on fragile tiles costs more and why switches are encouraged.
- **A\* Search:**
  - Formulate $f(n) = g(n) + h(n)$.
  - Present Heuristic 1 (Manhattan / 2) and Heuristic 2 (Orientation-aware).
  - Provide the formal proofs of admissibility and consistency (from `docs/ALGORITHMS_GUIDE.md`).

---

### 4. Experimental Evaluation (20 Points)

#### 4.1 Test Dataset Description
The benchmark suite evaluates **4 search algorithms (`BFS`, `DFS`, `UCS`, `A*`)** across **24 stages** (`96` total runs, unified `120.0s` timeout per run), grouped into two categories:
1. **Core & Large-Scale Puzzle Progression (`stage_01_core` – `stage_14_spiral`, 14 stages):**
   - *Mechanics Introduction (`stage_01_core` – `stage_04_split`):* Baseline 1×1×2 rolling (`stage_01_core`), fragile orange tile avoidance (`stage_02_fragile`), soft/heavy switch & bridge toggling (`stage_03_bridge`), and dual-cube split/merge coordination (`stage_04_split`).
   - *Medium-to-Extreme Combinatorial Maps (`stage_05_labyrinth` – `stage_14_spiral`):* Large multi-island and pixel-art boards combining fragile corridors, chained toggle bridges, and split switches (`stage_08_rick_roll`, `stage_09_anime_girl`, `stage_11_bad_apple`, `stage_13_rainbow_cat` expanding up to ~248,000 states), plus spiral perimeter corridor puzzles (`stage_14_spiral`).
2. **Diagnostic & Adversarial Stress Maps (10 specialized stages):**
   - *A\*-Favorable vs. A\*-Adversarial (`proastar1`, `proatrar2`, `conastar1`, `conastar2`):* Wide open branching boards where Manhattan guidance excels versus deceptive obstacle/switch detours that force optimal paths to temporarily move away from the goal.
   - *BFS / DFS / UCS Targeted Maps (`probfs1`, `probfs2`, `prodfs1`, `prodfs2`, `proucs1`, `proucs2`):* Shallow branching boards, deep directional corridors aligned with DFS action order, and fragile-vs-switch trade-off maps highlighting UCS's risk-aware cost model.

#### 4.2 Benchmark Results Table
*Generated via `python3 Project1/Source/main.py --benchmark` (`DEFAULT_SEARCH_TIMEOUT = 120.0s`; `A*` configured with pure `manhattan_heuristic`; `UCS` configured with `custom_cost_function`):*

##### A. Aggregate Summary Across All 24 Stages (`96 / 96` Solved)

| Algorithm | Solved Stages | Total Moves (24 Stages) | Avg. Moves / Stage | Total Expanded Nodes | Avg. Expanded / Stage | Total Search Time (ms) | Max Peak Memory (KB) |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **BFS** | **24 / 24 (100%)** | **940** | **39.17** | 611,299 | 25,470.79 | 111,749.95 | 264,152.61 |
| **DFS** | **24 / 24 (100%)** | 30,627 | 1,276.12 | **38,706** | **1,612.75** | **6,892.31** | **40,833.96** |
| **UCS** | **24 / 24 (100%)** | 954 | 39.75 | 454,375 | 18,932.29 | 100,685.47 | 278,544.29 |
| **A\*** | **24 / 24 (100%)** | **940** | **39.17** | 291,767 | 12,156.96 | 58,528.24 | 180,668.81 |

##### B. Detailed Per-Stage Benchmark Results (All 24 Stages)

| Stage | Algorithm | Solution Found? | Moves (Length) | Total Cost | Search Time (ms) | Peak Memory (KB) | Expanded Nodes | Generated Nodes |
| :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **stage_01_core** | BFS | Yes | 4 | 4.00 | 1.33 | 12.17 | 5 | 9 |
| | DFS | Yes | 4 | 4.00 | 0.64 | 7.18 | 4 | 8 |
| | UCS | Yes | 4 | 4.00 | 1.68 | 6.72 | 8 | 12 |
| | A* | Yes | 4 | 4.00 | 1.37 | 6.76 | 7 | 11 |
| **stage_02_fragile** | BFS | Yes | 7 | 7.00 | 7.93 | 37.60 | 47 | 63 |
| | DFS | Yes | 29 | 29.00 | 5.12 | 28.14 | 39 | 56 |
| | UCS | Yes | 7 | 7.00 | 7.03 | 32.32 | 38 | 60 |
| | A* | Yes | 7 | 7.00 | 3.85 | 23.49 | 24 | 43 |
| **stage_03_bridge** | BFS | Yes | 7 | 7.00 | 7.07 | 48.80 | 52 | 75 |
| | DFS | Yes | 56 | 56.00 | 7.24 | 73.59 | 79 | 113 |
| | UCS | Yes | 7 | 6.50 | 6.64 | 57.89 | 65 | 95 |
| | A* | Yes | 7 | 7.00 | 3.06 | 19.45 | 22 | 39 |
| **stage_04_split** | BFS | Yes | 17 | 17.00 | 19.04 | 77.27 | 119 | 146 |
| | DFS | Yes | 52 | 52.00 | 8.99 | 66.68 | 79 | 122 |
| | UCS | Yes | 17 | 16.40 | 22.00 | 103.14 | 149 | 175 |
| | A* | Yes | 17 | 17.00 | 5.86 | 26.10 | 36 | 54 |
| **stage_05_labyrinth** | BFS | Yes | 57 | 57.00 | 1525.01 | 8340.91 | 9695 | 9697 |
| | DFS | Yes | 344 | 344.00 | 50.84 | 655.68 | 439 | 831 |
| | UCS | Yes | 57 | 66.20 | 1849.82 | 8356.60 | 9694 | 9917 |
| | A* | Yes | 57 | 57.00 | 1893.79 | 7907.86 | 8918 | 9303 |
| **stage_06_citadel** | BFS | Yes | 98 | 98.00 | 3305.30 | 19328.56 | 15723 | 15902 |
| | DFS | Yes | 367 | 367.00 | 131.86 | 1525.37 | 890 | 1229 |
| | UCS | Yes | 98 | 185.80 | 4303.53 | 20317.17 | 15826 | 19231 |
| | A* | Yes | 98 | 98.00 | 1502.43 | 8724.96 | 6395 | 6936 |
| **stage_07_terra_globe** | BFS | Yes | 77 | 77.00 | 1330.80 | 8747.35 | 6905 | 7028 |
| | DFS | Yes | 344 | 344.00 | 155.52 | 1701.66 | 1122 | 1405 |
| | UCS | Yes | 79 | 100.10 | 1354.92 | 8400.25 | 6047 | 7098 |
| | A* | Yes | 77 | 77.00 | 983.60 | 6420.33 | 4687 | 5185 |
| **stage_08_rick_roll** | BFS | Yes | 123 | 123.00 | 18479.39 | 106098.21 | 97340 | 98545 |
| | DFS | Yes | 5563 | 5563.00 | 1275.89 | 18270.10 | 6414 | 14814 |
| | UCS | Yes | 125 | 160.60 | 21035.33 | 111738.35 | 96826 | 98061 |
| | A* | Yes | 123 | 123.00 | 17544.60 | 93888.37 | 82428 | 84765 |
| **stage_09_anime_girl** | BFS | Yes | 79 | 79.00 | 24140.77 | 163946.52 | 124611 | 131714 |
| | DFS | Yes | 10431 | 10431.00 | 2403.44 | 40833.96 | 12287 | 28898 |
| | UCS | Yes | 79 | 79.30 | 10588.67 | 74917.56 | 43822 | 61688 |
| | A* | Yes | 79 | 79.00 | 5300.80 | 37705.06 | 24283 | 28170 |
| **stage_10_neko_cat** | BFS | Yes | 62 | 62.00 | 1114.38 | 10821.87 | 7890 | 8474 |
| | DFS | Yes | 1376 | 1376.00 | 392.17 | 4041.76 | 1826 | 3193 |
| | UCS | Yes | 62 | 60.70 | 803.39 | 4851.18 | 3199 | 4237 |
| | A* | Yes | 62 | 62.00 | 548.53 | 6548.63 | 4434 | 5134 |
| **stage_11_bad_apple** | BFS | Yes | 33 | 33.00 | 14990.91 | 128314.88 | 77638 | 97361 |
| | DFS | Yes | 757 | 757.00 | 161.93 | 2774.98 | 1145 | 2184 |
| | UCS | Yes | 33 | 34.00 | 2535.03 | 23356.18 | 11373 | 17466 |
| | A* | Yes | 33 | 33.00 | 720.78 | 5553.46 | 3407 | 4346 |
| **stage_12_heart** | BFS | Yes | 82 | 82.00 | 1408.86 | 11237.91 | 9036 | 9214 |
| | DFS | Yes | 573 | 573.00 | 184.61 | 1875.59 | 981 | 1518 |
| | UCS | Yes | 84 | 129.10 | 1264.62 | 10142.94 | 6722 | 8804 |
| | A* | Yes | 82 | 82.00 | 1027.41 | 7024.76 | 4640 | 5522 |
| **stage_13_rainbow_cat**| BFS | Yes | 124 | 124.00 | 43375.70 | 264152.61 | 248043 | 248440 |
| | DFS | Yes | 7185 | 7185.00 | 1485.63 | 27423.21 | 8489 | 20998 |
| | UCS | Yes | 127 | 172.20 | 53896.99 | 278544.29 | 240044 | 300042 |
| | A* | Yes | 124 | 124.00 | 27954.78 | 180668.81 | 146983 | 159376 |
| **stage_14_spiral** | BFS | Yes | 68 | 68.00 | 33.51 | 247.83 | 415 | 418 |
| | DFS | Yes | 75 | 75.00 | 13.65 | 77.68 | 124 | 144 |
| | UCS | Yes | 68 | 73.00 | 39.09 | 217.11 | 419 | 421 |
| | A* | Yes | 68 | 68.00 | 40.57 | 221.25 | 399 | 412 |
| **conastar1** | BFS | Yes | 18 | 18.00 | 486.31 | 4966.12 | 3947 | 4050 |
| | DFS | Yes | 879 | 879.00 | 123.78 | 2913.23 | 1229 | 2325 |
| | UCS | Yes | 18 | 17.50 | 537.87 | 5423.45 | 4219 | 4431 |
| | A* | Yes | 18 | 18.00 | 706.01 | 4775.47 | 3526 | 4083 |
| **conastar2** | BFS | Yes | 3 | 3.00 | 0.91 | 16.57 | 8 | 24 |
| | DFS | Yes | 48 | 48.00 | 8.92 | 86.43 | 70 | 135 |
| | UCS | Yes | 3 | 6.00 | 5.07 | 31.54 | 28 | 64 |
| | A* | Yes | 3 | 3.00 | 1.92 | 16.76 | 12 | 33 |
| **proastar1** | BFS | Yes | 10 | 10.00 | 359.37 | 4841.02 | 2320 | 3937 |
| | DFS | Yes | 1079 | 1079.00 | 126.40 | 3215.23 | 1334 | 2650 |
| | UCS | Yes | 10 | 10.00 | 545.88 | 8369.48 | 4448 | 6576 |
| | A* | Yes | 10 | 10.00 | 6.99 | 95.47 | 62 | 131 |
| **proatrar2** | BFS | Yes | 6 | 6.00 | 35.37 | 470.19 | 271 | 519 |
| | DFS | Yes | 741 | 741.00 | 119.48 | 1857.09 | 811 | 1686 |
| | UCS | Yes | 6 | 6.00 | 96.53 | 886.36 | 551 | 950 |
| | A* | Yes | 6 | 6.00 | 1.30 | 8.59 | 6 | 16 |
| **probfs1** | BFS | Yes | 8 | 8.00 | 1.15 | 7.14 | 11 | 12 |
| | DFS | Yes | 8 | 8.00 | 1.36 | 6.39 | 8 | 10 |
| | UCS | Yes | 8 | 18.00 | 1.83 | 6.30 | 11 | 12 |
| | A* | Yes | 8 | 8.00 | 2.05 | 6.30 | 11 | 12 |
| **probfs2** | BFS | Yes | 8 | 8.00 | 2.79 | 18.91 | 25 | 30 |
| | DFS | Yes | 8 | 8.00 | 1.30 | 7.07 | 10 | 12 |
| | UCS | Yes | 8 | 18.00 | 6.47 | 25.55 | 45 | 49 |
| | A* | Yes | 8 | 8.00 | 1.71 | 10.11 | 14 | 19 |
| **prodfs1** | BFS | Yes | 16 | 16.00 | 991.43 | 10426.70 | 6464 | 7856 |
| | DFS | Yes | 16 | 16.00 | 1.34 | 14.12 | 16 | 18 |
| | UCS | Yes | 16 | 16.00 | 1607.53 | 12293.65 | 9786 | 9941 |
| | A* | Yes | 16 | 16.00 | 237.27 | 3162.45 | 1233 | 2468 |
| **prodfs2** | BFS | Yes | 18 | 18.00 | 50.15 | 488.93 | 395 | 505 |
| | DFS | Yes | 18 | 18.00 | 3.68 | 18.22 | 18 | 22 |
| | UCS | Yes | 18 | 18.00 | 131.10 | 1090.11 | 888 | 1038 |
| | A* | Yes | 18 | 18.00 | 22.74 | 171.04 | 198 | 247 |
| **proucs1** | BFS | Yes | 10 | 10.00 | 74.10 | 634.29 | 310 | 406 |
| | DFS | Yes | 652 | 652.00 | 221.81 | 3072.70 | 1269 | 1764 |
| | UCS | Yes | 10 | 7.50 | 30.02 | 204.12 | 122 | 191 |
| | A* | Yes | 10 | 10.00 | 14.19 | 54.04 | 32 | 59 |
| **proucs2** | BFS | Yes | 5 | 5.00 | 8.37 | 42.74 | 29 | 52 |
| | DFS | Yes | 22 | 22.00 | 6.71 | 28.17 | 23 | 39 |
| | UCS | Yes | 10 | 6.50 | 14.43 | 50.97 | 45 | 69 |
| | A* | Yes | 5 | 5.00 | 2.63 | 15.87 | 10 | 22 |

#### 4.3 Comparison Plots
- Insert the four comparative bar charts generated by `python3 Project1/Source/main.py --plot` (`Project1/Source/experiments/output/algorithm_comparison.png`).

#### 4.4 Analytical Insights & Discussion
1. **Search Efficiency & Heuristic Guidance (`A*` vs. `BFS`):**
   - Across all 24 stages, **A\*** (strictly using `manhattan_heuristic`, $h(s) = \text{Manhattan}/2$) expands **291,767** total nodes compared to **611,299** for **BFS** (**52.27% reduction**) and cuts cumulative search time nearly in half (**58.53s vs. 111.75s**, **47.63% faster**).
   - On high-branching boards where geometric proximity correlates with true distance, heuristic pruning is dramatic: on `stage_11_bad_apple`, A\* expands **3,407** nodes vs. BFS's **77,638** (**22.8× fewer nodes**, **20.8× faster**: `720.78 ms` vs. `14,990.91 ms`); on `proastar1` and `proatrar2`, A\* expands **37.4×** (`62` vs. `2,320`) and **45.2×** (`6` vs. `271`) fewer nodes respectively.
   - **Adversarial Heuristic Traps:** On maps with switch detours or U-shaped/spiral barriers (`conastar1`, `stage_05_labyrinth`, `stage_14_spiral`), the optimal path must temporarily move *away* from the goal, creating a heuristic local minimum. Here, A\* expands almost as many states as BFS (`3,526` vs. `3,947` on `conastar1`; `8,918` vs. `9,695` on `stage_05_labyrinth`; `399` vs. `415` on `stage_14_spiral`), and its runtime slightly exceeds BFS (`706.01 ms` vs. `486.31 ms` on `conastar1`; `40.57 ms` vs. `33.51 ms` on `stage_14_spiral`) because min-heap operations ($O(\log N)$) and per-state heuristic evaluation carry higher constant overhead than BFS's $O(1)$ `collections.deque` operations.
2. **Solution Optimality vs. First-Path Speed (`BFS` / `A*` / `UCS` vs. Graph-Search `DFS`):**
   - **BFS** and **A\*** achieve **100% identical shortest move counts on every single stage** (`940` total moves across 24 stages), empirically validating the admissibility and consistency of `manhattan_heuristic`.
   - **Why Graph-Search `DFS` is Faster & Uses Fewer Nodes/Memory, Yet Produces Severely Suboptimal Solutions:** Because Bloxorz boards are finite, strongly connected state graphs, standard Graph-Search DFS (`visited` set without premature depth cutoffs) plunges directly along a single deep trajectory rather than sweeping breadth-wise layers $d = 1, 2, \dots, d^*$. Consequently, DFS stumbles into the goal after expanding only **38,706** total nodes (**6.89s** total runtime, max memory **40.83 MB**) and excels on aligned corridor maps (`prodfs1`: `16` nodes in `1.34 ms` vs. BFS's `6,464` nodes in `991.43 ms`). However, this speed comes at the cost of **extreme path suboptimality**: DFS requires **30,627 total moves** (**32.6× worse** than optimal `940` moves), wandering for **10,431 moves** vs. `79` optimal on `stage_09_anime_girl` (**132× longer**) and **7,185 moves** vs. `124` on `stage_13_rainbow_cat` (**57.9× longer**). Moreover, when DFS's fixed action order enters dead-end regions first (`stage_03_bridge`, `conastar2`, `proatrar2`, `proucs1`), DFS expands *more* nodes and runs *slower* than both BFS and A\* (e.g., `811` nodes / `119.48 ms` for DFS vs. `6` nodes / `1.30 ms` for A\* on `proatrar2`).
3. **Risk-Aware Cost Optimization (`UCS` Behavior):**
   - **UCS** optimizes the non-uniform risk-aware cost model (`BASE_MOVE_COST = 1.0`, `FRAGILE_PENALTY = +2.0`, `SWITCH_EVENT_COST = 0.5`, `SPLIT_MOVE_PENALTY = +0.2`, `SWITCH_CUBE_COST = 0.3`).
   - On fragile-tile stages (`proucs2`, `stage_07_terra_globe`, `stage_08_rick_roll`, `stage_12_heart`, `stage_13_rainbow_cat`), UCS deliberately trades extra moves for safer routing—most visibly on `proucs2`, taking a **10-move** switch/safe detour with total cost **6.50** instead of the **5-move** fragile shortcut.
   - Interestingly, on switch-gated puzzles (`stage_11_bad_apple`, `stage_09_anime_girl`, `stage_10_neko_cat`, `proucs1`), assigning `SWITCH_EVENT_COST = 0.5 < 1.0` prioritizes switch-activating states in the priority queue, allowing UCS to unlock bridges early and expand far fewer nodes than BFS (`11,373` vs. `77,638` on `stage_11_bad_apple`; `43,822` vs. `124,611` on `stage_09_anime_girl`).
4. **Memory Consumption & Combinatorial Split-State Scaling:**
   - Peak memory (`tracemalloc`) scales linearly with the number of stored `SearchNode` and `GameState` objects in `frontier` and `visited` / `best_g_cost`.
   - Standard 1×1×2 block stages (`stage_01`–`stage_03`, `stage_14_spiral`) require under **250 KB**, whereas **Split-Switch stages** square the coordinate state space from $O(R \cdot C)$ to $O((R \cdot C)^2 \cdot 2^{|\mathcal{M}|})$: on `stage_13_rainbow_cat`, BFS peaks at **264,152.61 KB (~258.0 MB)** and UCS at **278,544.29 KB (~272.0 MB)** (higher than BFS due to lazy-deletion duplicate heap entries), while A\*'s heuristic pruning reduces peak memory by **31.6%** down to **180,668.81 KB (~176.4 MB)**.

---

### 5. References & Appendix
- List books (e.g., Russell & Norvig: *Artificial Intelligence: A Modern Approach*), Coolmath Games reference, Python documentation.
- **Generative AI Disclosure (Section 3.6):** Document how LLM tools were utilized (e.g., for scaffolding code structure, reviewing orientation math, generating report outlines) and disclose sample prompts.

> [!CAUTION]
> **Academic Integrity Warning:**  
> The course instructors include "canary prompts" in assignment PDFs (such as the prompt injection on Page 8 asking to include a phrase about the *"quantum cat theorem"*). **Never copy-paste unverified text into your report.** Write explanations in your own words so you are fully prepared for the oral interview!

---

## Part 2: Demo Video Guide (10 Points)

**Platform:** YouTube (Public or Unlisted link)  
**Duration:** 3 - 5 minutes  
**Language:** English or Vietnamese (with clear subtitles or voiceover narration)

### Recommended Video Timeline:
- **0:00 - 0:45 (Graphical Interface Demo - 5 pts):**
  - Show the GUI running.
  - Explain the visual layout: floor tiles, goal hole, fragile orange tiles, bridges, switches.
  - Show the 3D block representation across all 3 orientations (Standing, Lying H, Lying V).
  - Walk through sidebar buttons (Restart, Next/Prev Stage, Solvers, Replay controls).
- **0:45 - 2:00 (Manual Play Demonstration - 2.5 pts):**
  - Play Stage 1 manually with arrow keys.
  - Demonstrate falling off the board (illegal move detection).
  - Demonstrate standing on a fragile tile (tile breaks, loss condition).
  - Demonstrate pressing switches to toggle bridges.
  - Demonstrate a split switch (controlling 2 cubes independently with spacebar, then merging back).
  - Reach the goal upright and show the victory banner!
- **2:00 - 3:30 (Solver Demonstration & Replay - 2.5 pts):**
  - Choose Classic Stage 1 or Stage 3.
  - Click **Solve BFS** -> show terminal/sidebar metrics (time, nodes expanded, solution length).
  - Click **Play** on the replay controller to watch the animated solution step-by-step.
  - Click **Solve A*** -> highlight the reduction in expanded nodes compared to BFS.
  - Demonstrate stepping forward/backward through moves.
- **3:30 - 3:45 (Conclusion):** Brief wrap-up and credits.
