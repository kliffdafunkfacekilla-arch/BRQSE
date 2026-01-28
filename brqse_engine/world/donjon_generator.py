import random
import math
from enum import IntFlag

class Cell(IntFlag):
    NOTHING     = 0
    BLOCKED     = 1
    ROOM        = 2
    CORRIDOR    = 4
    PERIMETER   = 8
    ENTRANCE    = 16
    ROOM_ID     = 0xFFC0 
    
    # Extended Feature Flags (Donjon Port)
    ARCH        = 0x10000
    DOOR        = 0x20000
    LOCKED      = 0x40000
    TRAPPED     = 0x80000
    SECRET      = 0x100000
    PORTC       = 0x200000
    STAIR_DN    = 0x400000
    STAIR_UP    = 0x800000
    
    # Masks
    DOORSPACE   = ARCH | DOOR | LOCKED | TRAPPED | SECRET | PORTC

class DonjonGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed else random.randint(0, 999999)
        random.seed(self.seed)
        self.grid = []
        self.rooms = {} 
        self.cols = 0
        self.rows = 0

    def generate(self, width=41, height=41):
        self.cols = width if width % 2 else width - 1
        self.rows = height if height % 2 else height - 1
        self.grid = [[Cell.NOTHING for _ in range(self.cols)] for _ in range(self.rows)]
        self.rooms = {}
        
        self._scatter_rooms()
        self._generate_corridors()
        self._open_rooms()
        self._remove_deadends() # This removes SOME, but leaves others.
        self._emplace_stairs()
        
        return {
            "width": self.cols, "height": self.rows,
            "grid": self.grid, "rooms": self.rooms,
            "seed": self.seed
        }

    def _emplace_stairs(self):
        # Place Up/Down stairs at dead ends if possible
        dead_ends = []
        for r in range(1, self.rows-1):
            for c in range(1, self.cols-1):
                if self.grid[r][c] & Cell.CORRIDOR:
                    # Count corridor neighbors
                    neighbors = 0
                    for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                        if self.grid[r+dr][c+dc] & Cell.CORRIDOR: neighbors += 1
                        if self.grid[r+dr][c+dc] & Cell.ENTRANCE: neighbors += 1
                    
                    if neighbors == 1:
                        dead_ends.append((c,r))
        
        random.shuffle(dead_ends)
        
        # Place Down Stair (Exit)
        if dead_ends:
            c, r = dead_ends.pop()
            self.grid[r][c] |= Cell.STAIR_DN
        else:
            # Fallback: Random Room center
            rid = random.choice(list(self.rooms.keys()))
            c, r = self.rooms[rid]["center"]
            self.grid[r][c] |= Cell.STAIR_DN

        # Place Up Stair (Entrance)
        if dead_ends:
            c, r = dead_ends.pop()
            self.grid[r][c] |= Cell.STAIR_UP
        else:
            # Fallback
            rid = random.choice(list(self.rooms.keys()))
            c, r = self.rooms[rid]["center"]
            self.grid[r][c] |= Cell.STAIR_UP

    def _scatter_rooms(self):
        # Density: 1 room per 100 tiles roughly
        n_rooms = (self.cols * self.rows) // 100
        for _ in range(n_rooms):
            w = random.randint(3, 9)
            h = random.randint(3, 9)
            # Force odd coords
            x = random.randint(0, (self.cols - w) // 2) * 2 + 1
            y = random.randint(0, (self.rows - h) // 2) * 2 + 1
            
            if not self._check_collision(x, y, w, h):
                room_id = len(self.rooms) + 1
                self.rooms[room_id] = {
                    "id": room_id, "x": x, "y": y, "w": w, "h": h,
                    "center": (x + w//2, y + h//2), "exits": []
                }
                for r in range(y, y+h):
                    for c in range(x, x+w):
                        self.grid[r][c] = Cell.ROOM | (room_id << 6)
                # Mark perimeter
                for r in range(y-1, y+h+1):
                    for c in range(x-1, x+w+1):
                        if 0 <= r < self.rows and 0 <= c < self.cols:
                            if not (self.grid[r][c] & Cell.ROOM):
                                self.grid[r][c] |= Cell.PERIMETER

    def _check_collision(self, x, y, w, h):
        if x < 1 or y < 1 or x+w >= self.cols or y+h >= self.rows: return True
        for r in range(y, y+h):
            for c in range(x, x+w):
                if self.grid[r][c] & Cell.ROOM: return True
        return False

    def _generate_corridors(self):
        for r in range(1, self.rows, 2):
            for c in range(1, self.cols, 2):
                if self.grid[r][c] == Cell.NOTHING:
                    self._tunnel(c, r)

    def _tunnel(self, x, y, last_dir=None):
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(dirs)
        if last_dir and random.randint(0, 100) < 50: dirs.insert(0, last_dir) # Straightness bias
        
        for dx, dy in dirs:
            nx, ny = x + dx*2, y + dy*2
            if 0 < nx < self.cols-1 and 0 < ny < self.rows-1:
                if self.grid[ny][nx] == Cell.NOTHING: # Only dig into empty space
                    # Carve bridge + target
                    self.grid[y+dy][x+dx] = Cell.CORRIDOR
                    self.grid[ny][nx] = Cell.CORRIDOR
                    # Clear potential perimeter/entrance flags if overlapping
                    self.grid[y+dy][x+dx] &= ~Cell.PERIMETER
                    self._tunnel(nx, ny, (dx, dy))

    def _open_rooms(self):
        for rid, room in self.rooms.items():
            # Scan perimeter for spots touching a corridor
            sills = []
            x, y, w, h = room['x'], room['y'], room['w'], room['h']
            for c in range(x, x+w):
                self._check_sill(y-1, c, sills); self._check_sill(y+h, c, sills)
            for r in range(y, y+h):
                self._check_sill(r, x-1, sills); self._check_sill(r, x+w, sills)
            
            if sills:
                door_count = max(1, int(math.sqrt(w*h)//4))
                for _ in range(door_count):
                    if not sills: break
                    ds = sills.pop(random.randint(0, len(sills)-1))
                    
                    # Determine Door Type
                    dtype = self._door_type()
                    self.grid[ds[1]][ds[0]] = Cell.ENTRANCE | dtype
                    self.grid[ds[1]][ds[0]] &= ~Cell.PERIMETER # Clear perimeter

    def _door_type(self):
        # Ported from donjonsdungeongen.pl
        # 15% Arch, 45% Door, 15% Locked, 15% Trapped, 10% Secret, Rest Portcullis
        r = random.randint(0, 109)
        if r < 15: return Cell.ARCH
        elif r < 60: return Cell.DOOR
        elif r < 75: return Cell.LOCKED
        elif r < 90: return Cell.TRAPPED
        elif r < 100: return Cell.SECRET
        else: return Cell.PORTC

    def _check_sill(self, r, c, sills):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            if self.grid[r][c] & Cell.PERIMETER:
                # Check neighbors for corridor
                is_touching = False
                for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if self.grid[nr][nc] & Cell.CORRIDOR: is_touching = True
                if is_touching: sills.append((c, r))

    def _remove_deadends(self):
        # Simple loop to fill in dead ends
        for _ in range(50): 
            found = False
            for r in range(1, self.rows-1):
                for c in range(1, self.cols-1):
                    if self.grid[r][c] & Cell.CORRIDOR:
                        walls = 0
                        if self.grid[r+1][c] & (Cell.BLOCKED|Cell.PERIMETER): walls+=1
                        if self.grid[r-1][c] & (Cell.BLOCKED|Cell.PERIMETER): walls+=1
                        if self.grid[r][c+1] & (Cell.BLOCKED|Cell.PERIMETER): walls+=1
                        if self.grid[r][c-1] & (Cell.BLOCKED|Cell.PERIMETER): walls+=1
                        if walls >= 3:
                            self.grid[r][c] = Cell.NOTHING
                            found = True
            if not found: break
