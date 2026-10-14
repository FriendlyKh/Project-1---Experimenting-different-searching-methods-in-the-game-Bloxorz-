"""
Stage loader for Bloxorz puzzle stages.
Supports loading stages from JSON files or dictionary definitions.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union
from .constants import TileType, SwitchType, SwitchOperation
from .board import Board, Bridge, Switch


class StageLoader:
    """
    Utility class to load and parse stages.
    """

    TILE_CHAR_MAP = {
        "0": TileType.VOID,
        ".": TileType.VOID,
        " ": TileType.VOID,
        "1": TileType.FLOOR,
        "S": TileType.FLOOR,  # Start pos
        "2": TileType.GOAL,
        "G": TileType.GOAL,   # Goal pos
        "3": TileType.FRAGILE,
        "F": TileType.FRAGILE,
        "4": TileType.BRIDGE,
        "B": TileType.BRIDGE,
    }

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> Board:
        """
        Loads a stage configuration from a JSON file.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Stage file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.load_from_dict(data)

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> Board:
        """
        Parses a stage dictionary and constructs a Board object.
        """
        raw_grid = data.get("grid", [])
        if not raw_grid:
            raise ValueError("Stage data must contain a non-empty 'grid'.")

        rows = len(raw_grid)
        cols = max(len(row) for row in raw_grid)

        parsed_grid = []
        found_start = None
        found_goal = None

        for r, row_str in enumerate(raw_grid):
            row_tiles = []
            for c in range(cols):
                char = row_str[c] if c < len(row_str) else "0"
                if char == "S":
                    found_start = (r, c)
                elif char == "G":
                    found_goal = (r, c)

                tile = cls.TILE_CHAR_MAP.get(char, TileType.VOID)
                if tile == TileType.GOAL:
                    found_goal = (r, c)
                row_tiles.append(tile)
            parsed_grid.append(row_tiles)

        # Start position override or parsed
        if "start" in data:
            start_pos = tuple(data["start"])
        elif found_start:
            start_pos = found_start
        else:
            raise ValueError("Start position not specified in stage data.")

        # Goal position override or parsed
        if "goal" in data:
            goal_pos = tuple(data["goal"])
        elif found_goal:
            goal_pos = found_goal
        else:
            raise ValueError("Goal position not specified in stage data.")

        # Bridges
        bridges_dict: Dict[str, Bridge] = {}
        for b_raw in data.get("bridges", []):
            b_id = b_raw["id"]
            cells = [tuple(c) for c in b_raw["cells"]]
            is_open = b_raw.get("initially_open", False)
            bridges_dict[b_id] = Bridge(id=b_id, cells=cells, initially_open=is_open)
            # Ensure bridge tiles are marked as BRIDGE in the grid
            for br, bc in cells:
                if 0 <= br < rows and 0 <= bc < cols:
                    parsed_grid[br][bc] = TileType.BRIDGE

        # Switches
        switches_dict: Dict[tuple, Switch] = {}
        for s_raw in data.get("switches", []):
            pos = tuple(s_raw["pos"])
            s_type = SwitchType(s_raw.get("type", "soft"))
            s_op = SwitchOperation(s_raw.get("operation", "toggle"))
            linked = s_raw.get("linked_bridges", [])
            split_targets = None
            if "split_targets" in s_raw:
                split_targets = (
                    tuple(s_raw["split_targets"][0]),
                    tuple(s_raw["split_targets"][1]),
                )

            switches_dict[pos] = Switch(
                pos=pos,
                type=s_type,
                operation=s_op,
                linked_bridges=linked,
                split_targets=split_targets,
            )

        return Board(
            rows=rows,
            cols=cols,
            grid=parsed_grid,
            goal_pos=goal_pos,
            start_pos=start_pos,
            bridges=bridges_dict,
            switches=switches_dict,
        )
