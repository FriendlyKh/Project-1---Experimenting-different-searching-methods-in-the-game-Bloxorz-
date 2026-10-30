# Search Algorithms & Heuristics Guide

This guide provides the theoretical formalization, algorithm breakdowns, cost function designs, and mathematical proofs of admissibility needed for your code implementation and final report.

---

## 1. Formalization of the Bloxorz Search Problem

As required by **Section 3.6 (Algorithm Description - 10 pts)**:

### A. State Space $S$
A state $s \in S$ is formalized as:
$$s = (B, \mathcal{M})$$
Where:
- $B$ is the block representation:
  - In standard mode: $B = (r, c, \theta)$ where $(r, c) \in \mathbb{Z}^2$ is the anchor cell and $\theta \in \{\text{STANDING}, \text{LYING\_H}, \text{LYING\_V}\}$.
  - In split mode: $B = (c_1, c_2, i_{\text{active}})$ where $c_1, c_2 \in \mathbb{Z}^2$ are the coordinates of the two unit cubes and $i_{\text{active}} \in \{0, 1\}$.
- $\mathcal{M} = \{(\text{id}_1, b_1), (\text{id}_2, b_2), \dots\}$ is the boolean configuration of all dynamic bridges on the board ($b_k \in \{\text{True}, \text{False}\}$).

### B. Initial State $s_0$
$$s_0 = ((r_{\text{start}}, c_{\text{start}}, \text{STANDING}), \mathcal{M}_0)$$
Where the block stands upright on the level's designated starting cell, and bridges are set to their initial configuration.

### C. Actions $A(s)$
- Standard mode: $A(s) = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}\}$.
- Split mode: $A(s) = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{SWITCH\_CUBE}\}$.

### D. Transition Model $T(s, a)$
$T(s, a) \to s'$ computes the new block placement according to the deterministic 12-orientation physics table (or 1-unit movement for the active split cube), applies switch activation rules to update bridge statuses $\mathcal{M}'$, and checks validity:
- If any part of the block rests on $\text{VOID}$ or an out-of-bounds cell $\to$ illegal move.
- If the block stands upright on a fragile tile ($\text{FRAGILE}$) $\to$ illegal move.
- If illegal, $T(s, a) = \emptyset$ (pruned from successor generation).

### E. Goal Test $G(s)$
$$G(s) = \text{True} \iff (\neg s.B.\text{is\_split}) \land (s.B.\theta = \text{STANDING}) \land ((s.B.r, s.B.c) = \text{pos}_{\text{goal}})$$
*(Note: A block merely lying across the goal or an isolated unit cube does NOT satisfy the goal condition).*

---

## 2. Algorithm Theoretical Comparison

| Algorithm | Complete? | Optimal? | Time Complexity | Space Complexity | Frontier Data Structure |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BFS** | Yes | Yes (for unit costs) | $O(b^d)$ | $O(b^d)$ | FIFO Queue (`collections.deque`) |
| **DFS** | Yes* (with cycle check) | No | $O(b^m)$ | $O(b \cdot m)$ | LIFO Stack (`list`) |
| **UCS** | Yes (if $c \ge \epsilon > 0$) | Yes (any non-negative $c$) | $O(b^{1 + \lfloor C^* / \epsilon \rfloor})$ | $O(b^{1 + \lfloor C^* / \epsilon \rfloor})$ | Min-Heap Priority Queue (`heapq`) |
| **A\*** | Yes (if $h$ admissible) | Yes (if $h$ admissible) | $O(b^d)$ | $O(b^d)$ | Min-Heap ordered by $f(n) = g(n) + h(n)$ |

---

## 3. Cost Function Design for UCS (Section 3.4)

In Section 3.4 of the assignment:
> *"In the report, clearly define and justify your cost function... Note that if every move has cost 1, UCS reduces to BFS; designing a non-uniform cost function (and explaining the intuition behind it) is what makes this task meaningful."*

### Proposed Design: "Risk-Aware Cost Model"
$$c(s, a, s') = c_{\text{base}} + c_{\text{fragile\_penalty}} - c_{\text{switch\_incentive}} + c_{\text{split\_overhead}}$$

1. **Base Movement Cost ($c_{\text{base}} = 1.0$):** Standard physical work to rotate the block.
2. **Fragile Surface Penalty ($c_{\text{fragile\_penalty}} = +2.0$):** Moving onto fragile orange tiles poses structural hazard. UCS is penalized for using fragile shortcuts unless they substantially reduce overall path length.
3. **Switch Activation Incentive ($c_{\text{switch\_incentive}} = -0.5$):** Toggling switches expands the accessible topology of the stage. Rewarding switch interaction guides the search towards unlocking bridges.
4. **Coordination Overhead ($c_{\text{split\_overhead}} = +0.2$):** Maneuvering split cubes requires alternating moves and coordination.

---

## 4. Heuristic Design & Admissibility Proofs (Section 3.5)

### A. Heuristic 1: Manhattan Distance Divided by 2
$$h_1(s) = \frac{|r_{\text{block}} - r_{\text{goal}}| + |c_{\text{block}} - c_{\text{goal}}|}{2}$$

#### Proof of Admissibility:
- In Bloxorz, rolling the 1x1x2 block from `STANDING` to `LYING` shifts its center of mass or edge by at most **2 grid cells** in a single move.
- In 4-connected grid geometry, the true shortest path between two points $(r_1, c_1)$ and $(r_2, c_2)$ has length at least $\Delta r + \Delta c = \text{Manhattan}((r_1, c_1), (r_2, c_2))$.
- Since each single action can reduce the Manhattan distance to the goal by at most $2$ units:
$$\text{Cost}^*(s) \ge \left\lceil \frac{\text{Manhattan}(s, \text{goal})}{2} \right\rceil \ge \frac{\text{Manhattan}(s, \text{goal})}{2} = h_1(s)$$
- Since $h_1(s) \le \text{Cost}^*(s)$ for all states $s$, $h_1$ never overestimates the true remaining cost and is therefore **strictly admissible**.

### B. Heuristic 2: Orientation-Aware Manhattan Heuristic
$$h_2(s) = h_1(s) + \text{penalty}(\theta)$$
Where:
$$\text{penalty}(\theta) = \begin{cases} 0 & \text{if } \theta = \text{STANDING} \\ 0.5 & \text{if } \theta \in \{\text{LYING\_H}, \text{LYING\_V}\} \end{cases}$$

#### Proof of Admissibility:
- To achieve victory, the block must be in `Orientation.STANDING` on the goal cell.
- If the block is currently `LYING_H` or `LYING_V`, it is impossible to transition into the goal state in 0 rolls, even if one of its occupied cells already overlaps the goal cell. It requires at least one extra roll to stand upright.
- Adding a conservative $+0.5$ preserves $h_2(s) \le \text{Cost}^*(s)$, making $h_2$ strictly more informed (tighter) than $h_1$ while remaining **admissible**.

### C. Consistency (Monotonicity) Proof
A heuristic is consistent if for every state $s$ and successor $s'$ generated by action $a$:
$$h(s) \le c(s, a, s') + h(s')$$
With unit step cost $c = 1$:
$$h_1(s) - h_1(s') = \frac{\text{dist}(s) - \text{dist}(s')}{2} \le \frac{2}{2} = 1 = c(s, a, s')$$
Hence, $h_1$ satisfies the triangle inequality and is **monotonically consistent**. Consistent heuristics guarantee that the first time A* expands a state, it has found the optimal path to it!
