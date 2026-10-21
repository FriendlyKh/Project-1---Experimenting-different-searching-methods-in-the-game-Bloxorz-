# CSC14003 - Artificial Intelligence: Project 1 - Bloxorz Solver

Welcome to your group project repository! This repository contains a modular Python framework designed for a **team of 4 students** to collaborate seamlessly.

---

## 📁 Repository Directory Overview

```
Project 1/
├── Source/                         # Source code directory (matches Section 4 submission format)
│   ├── main.py                     # Main application entry point (GUI, CLI, benchmarks)
│   ├── requirements.txt            # Python dependencies (pygame, matplotlib)
│   ├── README.md                   # How to install, run, and test the project
│   ├── config.py                   # Game configurations, display colors, limits
│   ├── game/                       # [Member 1] Board model, block physics, state hashing
│   ├── solvers/                    # [Members 2 & 3] BFS, DFS/IDS, UCS, A*, heuristics
│   ├── gui/                        # [Member 4] Pygame interface, animations, replay controls
│   ├── stages/                     # JSON stage definitions (levels 1-5 + classic)
│   ├── experiments/                # Benchmark automation & matplotlib plotting
│   └── tests/                      # Unit test suite (all 13 tests passing)
│
├── docs/                           # Team documentation & report resources
│   ├── TEAM_WORKFLOW.md            # 4-member task allocation, Git branching, 3-week roadmap
│   ├── ARCHITECTURE.md             # System design, state representation, transition tables
│   ├── ALGORITHMS_GUIDE.md         # Problem formalization, UCS cost functions, heuristic proofs
│   └── REPORT_TEMPLATE.md          # 30-point report outline & 10-point demo video script
│
└── .gitignore                      # Git ignore patterns for Python, venv, and cache
```

---

## 🚀 Quick Commands

### 1. Run Unit Tests (100% Passing)
```bash
python3 -m unittest discover -s Source/tests -p "test_*.py"
```

### 2. Run Headless CLI Solver
```bash
python3 Source/main.py --cli --stage Source/stages/stage_classic_01.json --solver astar
```

### 3. Run Automated Benchmarks Across All 5 Stages
```bash
python3 Source/main.py --benchmark
```

### 4. Launch Pygame GUI (Requires Display & Pygame installed)
```bash
pip install -r Source/requirements.txt
python3 Source/main.py
```

---

## 👥 Team Quicklinks

- Check out **[TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md)** to see the recommended division of labor and Git workflow for 4 people.
- Check out **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** for details on the 12 orientation transitions and state hashing.
- Check out **[ALGORITHMS_GUIDE.md](docs/ALGORITHMS_GUIDE.md)** for formal mathematical definitions and heuristic proofs.
- Check out **[REPORT_TEMPLATE.md](docs/REPORT_TEMPLATE.md)** to draft your 30-pt report and prepare your demo video.
