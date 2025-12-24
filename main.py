# Made by Oscar Horrobin
# GitHub: https://github.com/NoOne20104
# ------------------ IMPORTS ------------------
import pygame          # Pygame library for graphics, input, and game loop
import sys             # System functions, like exiting the program
import time            # For timing and delays
import math            # Math functions like hypot
import glob            # File searching for terminal commands like CPU temp
import shutil          # For disk usage commands
from collections import deque  # Double-ended queue for terminal output history

# Initialize Pygame
pygame.init()

# ------------------ SETTINGS ------------------
WIDTH, HEIGHT = 800, 600  # Window dimensions
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Create game window
pygame.display.set_caption("PyCraft 10.5 - ")  # Window title

# ------------------ COLORS ------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BROWN = (139, 69, 19)
GREEN = (34, 139, 34)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
SAND = (194, 178, 128)
WOOD = (160, 82, 45)
WATER_COLOR = (0, 0, 255)
ORANGE = (255, 140, 0)
LIGHT_GREEN = (144, 238, 144)
RED = (255, 0, 0)
ARROW_COLOR = (0, 0, 0)

# ------------------ GRID ------------------
TILE_SIZE = 40                # Size of each tile in pixels
WORLD_WIDTH = 100             # Width of the world in tiles
WORLD_HEIGHT = 50             # Height of the world in tiles
SCREEN_TILES_X = WIDTH // TILE_SIZE  # Number of tiles visible horizontally
SCREEN_TILES_Y = HEIGHT // TILE_SIZE # Number of tiles visible vertically

# ------------------ MINI-MAP ------------------
MINIMAP_WIDTH = 200
MINIMAP_HEIGHT = 100
MINIMAP_X = WIDTH - MINIMAP_WIDTH - 10  # X position of minimap
MINIMAP_Y = 10                          # Y position of minimap

# ------------------ PLAYER ------------------
player_x_pos = WORLD_WIDTH * TILE_SIZE // 2    # Starting X position
player_y_pos = (WORLD_HEIGHT - 15) * TILE_SIZE  # Starting Y position
player_width = TILE_SIZE
player_height = TILE_SIZE
player_velocity_y = 0       # Vertical speed
on_ground = False           # If the player is touching the ground
speed = 5                   # Horizontal movement speed
jump_strength = -12         # Negative value to jump up

# ------------------ INVENTORY ------------------
inventory_open = False                      # Whether the inventory is currently open
hotbar = [None] * 9                         # Player hotbar with 9 slots
selected_slot = 0                           # Currently selected hotbar slot

# All available block IDs for the player
inventory_blocks = [1,2,3,4,5,6,7,8,9,10,11,12]

# Display names for each block
inventory_names = {
    1: "Dirt",
    2: "Grass",
    3: "Stone",
    4: "Gold",
    5: "Sand",
    6: "Wood",
    7: "Water",
    8: "Lava",
    9: "Leaves",
    10: "TNT",
    11: "Bow",
    12: "Deepslate"  #  New dark stone block
}

# Dragging controls
dragging_item = None            # Item currently being dragged in inventory
drag_offset_x = 0               # Mouse offset for dragging
drag_offset_y = 0

# ------------------ TNT / ARROWS ------------------
tnt_list = []                   # List of TNT blocks that have been placed
arrows = []                     # List of arrows currently flying

# ------------------ COMMAND SYSTEM ------------------
command_mode = False            # Whether player is typing a command
command_text = ""               # Current command input
time_of_day = "day"             # Game time
commands = {}                   # Command function dictionary
command_descriptions = {        # Descriptions for command help
    "time": "/time set day/night - Changes the time of day",
    "box": "/box surround - Builds a 3x3 box around the player using the selected block",
    "build": "/build tower [height] -l/-r - Builds a tower next to the player"
}
show_commands = False           # Whether to show the command help panel

# ------------------ TERMINAL ------------------
terminal_active = False
terminal_input = ""             # Current text in terminal
terminal_output = deque(maxlen=50)  # Terminal output history (max 50 lines)
terminal_rect = pygame.Rect(50, 50, WIDTH-100, 200)  # Rectangle for terminal display
terminal_history = []           # For scrolling through previous commands with ↑/↓
terminal_history_index = -1

# ------------------ CLOCK / FPS ------------------
clock = pygame.time.Clock()     # Game clock to control FPS
font = pygame.font.SysFont(None,24)      # Font for UI
fps_font = pygame.font.SysFont(None,24)  # Font for FPS display
fps_counter = 0
fps_timer = time.time()
current_fps = 0
import random
# ------------------ WORLD GENERATION ------------------
import random

DEPTH = 30  # total depth of the underground
world = [[0 for _ in range(WORLD_WIDTH)] for _ in range(WORLD_HEIGHT)]

for x in range(WORLD_WIDTH):
    # Grass layer = random between 2 and 4 layers
    grass_thickness = random.randint(2, 4)
    # Dirt layer = random between 3 and 6 layers
    dirt_thickness = random.randint(3, 6)
    # Remaining layers = stone + deepslate
    stone_bottom = DEPTH - (grass_thickness + dirt_thickness)

    for i in range(DEPTH):
        y = WORLD_HEIGHT - 1 - i  # bottom-most = WORLD_HEIGHT-1

        #  Bottom few layers = full Deepslate
        if i < 4:
            world[y][x] = 12

        #  Transition zone (between stone and Deepslate)
        elif 4 <= i < 8:
            # Mostly stone, but some random Deepslate patches for realism
            if random.random() < (0.1 * (8 - i)):  # gradually increases chance
                world[y][x] = 12
            else:
                world[y][x] = 3

        #  Rest of the underground (all stone)
        elif i < stone_bottom:
            world[y][x] = 3

        #  Dirt layer (some stone mixed in)
        elif stone_bottom <= i < stone_bottom + dirt_thickness:
            world[y][x] = 3 if random.random() < 0.2 else 1

        #  Grass layer
        else:
            world[y][x] = 2
# ------------------ CLOUDS ------------------
# Stores all cloud objects
clouds = []

# Create clouds at game start
for i in range(20):
    clouds.append({
        # World-space X position (scrolls with camera)
        "x": random.randint(0, WORLD_WIDTH * TILE_SIZE),

        # Vertical position in the sky (top third of screen)
        "y": random.randint(20, HEIGHT // 3.5),

        # Cloud size
        "w": random.randint(80, 140),
        "h": random.randint(30, 50),

        # Horizontal speed (pixels per frame)
        "speed": random.uniform(0.05, 0.08)
    })

# ------------------ TREE GENERATION ------------------
def generate_trees():
    for x in range(2, WORLD_WIDTH-2):  # avoid edges
        # Find topmost grass tile
        for y in range(WORLD_HEIGHT):
            if world[y][x] == 2:  # grass
                if random.random() < 0.05:  # 5% chance for a tree
                    trunk_height = random.randint(3, 5)

                    # Place wood trunk
                    for i in range(trunk_height):
                        if y-1-i >= 0:
                            world[y-1-i][x] = 6  # wood

                    # Place leaves around top
                    leaf_start = y - trunk_height
                    for lx in range(x-2, x+3):
                        for ly in range(leaf_start-2, leaf_start+1):
                            if 0 <= lx < WORLD_WIDTH and 0 <= ly < WORLD_HEIGHT:
                                if random.random() < 0.8:
                                    world[ly][lx] = 9  # leaf
                break  # stop after the topmost grass

# Call tree generation
generate_trees()


# ------------------ PLAYER SPAWN ------------------
# Spawn player on top of the first solid block (grass)
spawn_x = WORLD_WIDTH // 2
for y in range(WORLD_HEIGHT):
    if world[y][spawn_x] != 0:
        player_y_pos = y * TILE_SIZE - player_height
        break
player_x_pos = spawn_x * TILE_SIZE

# ------------------ VIEWPORT SURFACE ------------------
viewport_surface = pygame.Surface(
    ((SCREEN_TILES_X + 1) * TILE_SIZE,
     (SCREEN_TILES_Y + 1) * TILE_SIZE)
)

# ------------------ PENGUIN PLAYER SURFACE ------------------
# Improved penguin surface
penguin_surface = pygame.Surface((player_width, player_height), pygame.SRCALPHA)

# Body
pygame.draw.ellipse(penguin_surface, (0,0,0), (0,0,player_width,player_height))  # Black body
pygame.draw.ellipse(penguin_surface, (255,255,255), (player_width*0.25, player_height*0.3, player_width*0.5, player_height*0.5))  # White belly

# Eyes
eye_radius = player_width//10
pygame.draw.circle(penguin_surface, (255,255,255), (int(player_width*0.3), int(player_height*0.35)), eye_radius)  # Left eye white
pygame.draw.circle(penguin_surface, (255,255,255), (int(player_width*0.7), int(player_height*0.35)), eye_radius)  # Right eye white
pygame.draw.circle(penguin_surface, (0,0,0), (int(player_width*0.3), int(player_height*0.35)), eye_radius//2)  # Left pupil
pygame.draw.circle(penguin_surface, (0,0,0), (int(player_width*0.7), int(player_height*0.35)), eye_radius//2)  # Right pupil

# Beak
pygame.draw.polygon(penguin_surface, (255,165,0), [
    (player_width//2-5, player_height//2),
    (player_width//2+5, player_height//2),
    (player_width//2, player_height//2 + 6)
])

# Wings
pygame.draw.ellipse(penguin_surface, (0,0,0), (0, player_height*0.4, player_width*0.25, player_height*0.5))  # Left wing
pygame.draw.ellipse(penguin_surface, (0,0,0), (player_width*0.75, player_height*0.4, player_width*0.25, player_height*0.5))  # Right wing

# Feet
pygame.draw.polygon(penguin_surface, (255,165,0), [(player_width*0.35, player_height*0.9),
                                                   (player_width*0.45, player_height*0.9),
                                                   (player_width*0.4, player_height)])  # Left foot
pygame.draw.polygon(penguin_surface, (255,165,0), [(player_width*0.55, player_height*0.9),
                                                   (player_width*0.65, player_height*0.9),
                                                   (player_width*0.6, player_height)])  # Right foot
# ------------------ FUNCTIONS ------------------

# Get color for a given tile ID
def get_color(tile):
    if tile == 1: return BROWN
    elif tile == 2: return GREEN
    elif tile == 3: return GRAY
    elif tile == 4: return YELLOW
    elif tile == 5: return SAND
    elif tile == 6: return WOOD
    elif tile == 7: return WATER_COLOR
    elif tile == 8: return ORANGE
    elif tile == 9: return LIGHT_GREEN
    elif tile == 10: return RED
    elif tile == 11: return BLACK
    elif tile == 12: return (50, 50, 50)  # Deepslate
    else: return LIGHT_GRAY


# Draw the world using tile offsets (pixel shift handled by blit)
def draw_world(surface, offset_x, offset_y):
    # Fill background sky color
    surface.fill(BLUE if time_of_day == "day" else (20, 20, 50))

    # ------------------ DRAW CLOUDS (SKY LAYER) ------------------
    for cloud in clouds:
        base_x = cloud["x"] - offset_x * TILE_SIZE
        base_y = cloud["y"] + pixel_y
        w = cloud["w"]
        h = cloud["h"]

        # Choose colors based on time of day
        if time_of_day == "night":
            main_col = (110, 110, 125)
            puff_col = (140, 140, 155)
        else:
            main_col = (245, 245, 245)
            puff_col = (255, 255, 255)

        pygame.draw.ellipse(
            surface, main_col,
            (base_x, base_y, w, h)
        )

        pygame.draw.ellipse(
            surface, puff_col,
            (base_x - w * 0.3, base_y + h * 0.2, w * 0.6, h * 0.6)
        )

        pygame.draw.ellipse(
            surface, puff_col,
            (base_x + w * 0.4, base_y + h * 0.25, w * 0.6, h * 0.6)
        )

        pygame.draw.ellipse(
            surface, puff_col,
            (base_x + w * 0.15, base_y - h * 0.3, w * 0.7, h * 0.7)
        )

    # ------------------ DRAW TERRAIN (NO TRUNKS / LEAVES) ------------------

    for y in range(SCREEN_TILES_Y + 1):
        for x in range(SCREEN_TILES_X + 1):
            world_x = x + offset_x
            world_y = y + offset_y

            if 0 <= world_x < WORLD_WIDTH and 0 <= world_y < WORLD_HEIGHT:
                tile = world[world_y][world_x]

                # Draw everything EXCEPT tree trunks (6) and leaves (9)
                if tile != 0 and tile not in (6, 9):
                    pygame.draw.rect(
                        surface,
                        get_color(tile),
                        (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    )



# Draw the player's hotbar
def draw_hotbar():
    for i, block in enumerate(hotbar):
        x = i * (TILE_SIZE + 5) + 10
        y = HEIGHT - TILE_SIZE - 10
        color = get_color(block) if block else LIGHT_GRAY
        pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))

        if block:
            text_color = WHITE if block in [10, 11] else BLACK
            num_text = font.render(str(i + 1), True, text_color)
            screen.blit(num_text, (x + 15, y + 10))

        if i == selected_slot:
            pygame.draw.rect(screen, RED, (x, y, TILE_SIZE, TILE_SIZE), 3)


# Draw inventory panel
def draw_inventory():
    rows, cols = 2, 6
    slot_size = 50
    margin_x = 12
    margin_y = 22
    start_x = 100
    start_y = 40

    for i, block in enumerate(inventory_blocks):
        row = i // cols
        col = i % cols
        x = start_x + col * (slot_size + margin_x)
        y = start_y + row * (slot_size + margin_y)

        pygame.draw.rect(screen, get_color(block), (x, y, slot_size, slot_size))
        pygame.draw.rect(screen, BLACK, (x, y, slot_size, slot_size), 3)

        name_text = font.render(
            inventory_names[block],
            True,
            WHITE if block in [10, 11] else BLACK
        )
        text_rect = name_text.get_rect(
            center=(x + slot_size // 2, y + slot_size + 10)
        )
        screen.blit(name_text, text_rect)


# Draw item being dragged
def draw_drag_item():
    if dragging_item:
        mx, my = pygame.mouse.get_pos()
        pygame.draw.rect(
            screen,
            get_color(dragging_item),
            (mx - drag_offset_x, my - drag_offset_y, 50, 50)
        )


# Handle TNT explosions
def handle_tnt():
    current_time = time.time()
    for t in tnt_list[:]:
        if current_time - t[2] > 2:
            tx, ty = t[0], t[1]
            for y in range(max(0, ty - 1), min(WORLD_HEIGHT, ty + 2)):
                for x in range(max(0, tx - 1), min(WORLD_WIDTH, tx + 2)):
                    world[y][x] = 0
            tnt_list.remove(t)


# Update arrows (frame-based, unchanged)
def update_arrows():
    for arrow in arrows[:]:
        arrow["x"] += arrow["vx"]
        arrow["y"] += arrow["vy"]

        tile_x = int(arrow["x"] // TILE_SIZE)
        tile_y = int(arrow["y"] // TILE_SIZE)

        if 0 <= tile_x < WORLD_WIDTH and 0 <= tile_y < WORLD_HEIGHT:
            if world[tile_y][tile_x] != 0:
                world[tile_y][tile_x] = 0
                arrows.remove(arrow)
        else:
            arrows.remove(arrow)


# Draw arrows using tile offset (pixel handled by camera blit)
def draw_arrows(surface, offset_x, offset_y):
    for arrow in arrows:
        pygame.draw.rect(
            surface,
            ARROW_COLOR,
            (
                arrow["x"] - offset_x * TILE_SIZE,
                arrow["y"] - offset_y * TILE_SIZE,
                8,
                6
            )
        )


# Collision detection
def check_collision(x, y, w, h):
    left = int(x // TILE_SIZE)
    right = int((x + w - 1) // TILE_SIZE)
    top = int(y // TILE_SIZE)
    bottom = int((y + h - 1) // TILE_SIZE)

    for ty in range(top, bottom + 1):
        for tx in range(left, right + 1):
            if 0 <= tx < WORLD_WIDTH and 0 <= ty < WORLD_HEIGHT:
                if world[ty][tx] not in [0, 7]:
                    return True
    return False


# CPU temperature (Linux only)
def get_cpu_temp():
    temps = []
    for zone in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            with open(zone, "r") as f:
                temps.append(int(f.read()) / 1000)
        except:
            continue
    return max(temps) if temps else 0

# ------------------ COMMAND FUNCTIONS ------------------

# Add text to terminal output
def add_terminal_output(text):
    terminal_output.append(text)

# Change time of day
def cmd_time(args):
    global time_of_day
    if len(args) >= 1 and args[0]=="set" and len(args)>=2:
        if args[1]=="night": time_of_day="night"
        elif args[1]=="day": time_of_day="day"

# Build a 3x3 box around player
def cmd_box(args):
    block = hotbar[selected_slot]
    if not block: return
    if len(args)>=1 and args[0]=="surround":
        px = int(player_x_pos // TILE_SIZE)
        py = int(player_y_pos // TILE_SIZE)
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==0 and dy==0: continue
                x = px+dx
                y = py+dy
                if 0<=x<WORLD_WIDTH and 0<=y<WORLD_HEIGHT:
                    world[y][x] = block

# Build a tower command
def cmd_build(args):
    if len(args) < 3 or args[0]!="tower":
        add_terminal_output("Usage: /build tower [height] [-l/-r]")
        return
    try: height = int(args[1])
    except: add_terminal_output("Invalid height"); return
    if height<1 or height>100: add_terminal_output("Height 1-100"); return
    direction = args[2].lower()
    if direction not in ["-l","-r"]: add_terminal_output("Direction must be -l/-r"); return
    block = hotbar[selected_slot] if hotbar[selected_slot] else (inventory_blocks[0] if inventory_blocks else None)
    if not block: add_terminal_output("No blocks available"); return
    px = int(player_x_pos//TILE_SIZE)
    tower_x = px-1 if direction=="-l" else px+1
    tower_x = max(0,min(WORLD_WIDTH-1,tower_x))
    ground_y = -1
    for y in range(WORLD_HEIGHT-1,-1,-1):
        if world[y][tower_x]!=0:
            ground_y=y
            break
    if ground_y==-1: add_terminal_output("No ground to build!"); return
    for i in range(1,height+1):
        build_y = ground_y - i
        if build_y<0: break
        world[build_y][tower_x]=block
    add_terminal_output(f"Built tower {height} high at x={tower_x} with block {block}")

# Change player speed
def cmd_speed(args):
    global speed
    if len(args) >= 1:
        try:
            speed = float(args[0])
        except:
            pass  # Ignore invalid input

# Disk usage
def cmd_df(args=None):
    total, used, free = shutil.disk_usage("/")
    add_terminal_output(f"Disk free: {free//(1024*1024)} MB")

# Place a block at specific coordinates using block name
def cmd_place(args):
    if len(args) < 3:
        add_terminal_output("Usage: /place <block_name> <x> <y>")
        return
    block_name = args[0].lower()
    try:
        x = int(args[1])
        y = int(args[2])
    except:
        add_terminal_output("Invalid coordinates!")
        return

    # Find block ID by name
    block_id = None
    for bid, name in inventory_names.items():
        if name.lower() == block_name:
            block_id = bid
            break
    if not block_id:
        add_terminal_output(f"Block '{block_name}' not found!")
        return

    if 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT:
        world[y][x] = block_id
        add_terminal_output(f"Placed '{block_name}' at ({x}, {y})")
    else:
        add_terminal_output("Coordinates out of bounds!")

# Register commands
commands["speed"] = cmd_speed
command_descriptions["speed"] = "/speed [value] - Sets player movement speed (example: 5-50)"
commands["time"] = cmd_time
commands["box"] = cmd_box
commands["build"] = cmd_build
commands["place"] = cmd_place
command_descriptions["place"] = "/place <block_name> <x> <y> - Place block/item at coordinates"


# ------------------ TERMINAL HANDLER ------------------
def handle_terminal_command(cmd):
    global terminal_active
    c = cmd.strip().lower()

    if c == "date":
        add_terminal_output(time.strftime("%Y-%m-%d %H:%M:%S"))

    elif c == "ls":
        files = ["stone.txt", "pickaxe.sh", "inventory", "README.md"]
        add_terminal_output("  ".join(files))

    elif c == "clear":
        terminal_output.clear()

    elif c in ("exit", "quit", "close"):
        add_terminal_output("Closing terminal...")
        terminal_active = False

    elif c == "df":
        cmd_df()

    elif c == "help":
        help_text = [
            "Available terminal commands:",
            "date   - Show current date/time",
            "ls     - List files",
            "clear  - Clear the terminal",
            "df     - Show disk usage",
            "exit   - Close the terminal"
        ]
        for line in help_text:
            add_terminal_output(line)

    else:
        add_terminal_output(f"Unknown command: {cmd}")

# ------------------ MAIN LOOP ------------------
while True:
    keys = pygame.key.get_pressed()  # Check held keys

    for event in pygame.event.get():  # Event handling
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # ------------------ KEYBOARD INPUT ------------------
        if event.type == pygame.KEYDOWN:
            # Terminal input
            if terminal_active:
                if event.key == pygame.K_RETURN:  # Enter key
                    if terminal_input.strip():
                        handle_terminal_command(terminal_input)
                        terminal_history.append(terminal_input)
                        terminal_history_index = -1
                    terminal_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    terminal_input = terminal_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    terminal_active = False
                elif event.key == pygame.K_UP:
                    if terminal_history:
                        if terminal_history_index == -1:
                            terminal_history_index = len(terminal_history) - 1
                        elif terminal_history_index > 0:
                            terminal_history_index -= 1
                        terminal_input = terminal_history[terminal_history_index]
                elif event.key == pygame.K_DOWN:
                    if terminal_history_index != -1:
                        terminal_history_index += 1
                        if terminal_history_index >= len(terminal_history):
                            terminal_history_index = -1
                            terminal_input = ""
                        else:
                            terminal_input = terminal_history[terminal_history_index]
                else:
                    terminal_input += event.unicode

            # Command mode input
            elif command_mode:
                if event.key == pygame.K_RETURN:
                    parts = command_text.strip().split()
                    if parts and parts[0] in commands:
                        commands[parts[0]](parts[1:])
                    command_text = ""
                    command_mode = False
                elif event.key == pygame.K_BACKSPACE:
                    command_text = command_text[:-1]
                else:
                    command_text += event.unicode

            # Normal gameplay keys
            else:
                if event.key == pygame.K_t:  # Toggle terminal
                    terminal_active = not terminal_active
                elif event.key == pygame.K_SLASH:  # Start command mode
                    command_mode = True
                    command_text = ""
                elif event.key == pygame.K_i:  # Toggle inventory
                    inventory_open = not inventory_open
                elif event.key == pygame.K_c:  # Toggle command dictionary (C instead of D)
                    show_commands = not show_commands
                elif not inventory_open:
                    # Number keys for hotbar
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        selected_slot = event.key - pygame.K_1
                    elif event.key == pygame.K_0:
                        selected_slot = 9

               # ------------------ MOUSE INPUT ------------------
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()

            # Convert mouse -> world tile using pixel-based camera
            tile_x = int((mx + camera_x) // TILE_SIZE)
            tile_y = int((my + camera_y) // TILE_SIZE)

            if inventory_open:
                # Drag inventory items
                rows, cols = 2, 6
                slot_size = 50
                margin = 10
                start_x = 100
                start_y = 50
                for i, block in enumerate(inventory_blocks):
                    row = i // cols
                    col = i % cols
                    x0 = start_x + col * (slot_size + margin)
                    y0 = start_y + row * (slot_size + margin)
                    if x0 <= mx <= x0 + slot_size and y0 <= my <= y0 + slot_size:
                        dragging_item = block
                        drag_offset_x = mx - x0
                        drag_offset_y = my - y0
            else:
                # Right click removes block
                if event.button == 3 and 0 <= tile_y < WORLD_HEIGHT and 0 <= tile_x < WORLD_WIDTH:
                    world[tile_y][tile_x] = 0

                # Left click places block / uses item
                elif event.button == 1 and hotbar[selected_slot]:
                    block = hotbar[selected_slot]

                    if block == 10:  # TNT
                        world[tile_y][tile_x] = 10
                        tnt_list.append([tile_x, tile_y, time.time()])

                    elif block == 11:  # Bow
                        # Mouse position in world space
                        world_mx = mx + camera_x
                        world_my = my + camera_y

                        dx = world_mx - (player_x_pos + player_width / 2)
                        dy = world_my - (player_y_pos + player_height / 2)

                        dist = math.hypot(dx, dy)
                        if dist != 0:
                            vx = dx / dist * 12
                            vy = dy / dist * 12
                            arrows.append({
                                'x': player_x_pos + player_width / 2,
                                'y': player_y_pos + player_height / 2,
                                'vx': vx,
                                'vy': vy
                            })

                    else:
                        world[tile_y][tile_x] = block

        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging_item:
                mx, my = pygame.mouse.get_pos()
                for i in range(9):
                    x0 = i * (TILE_SIZE + 5) + 10
                    y0 = HEIGHT - TILE_SIZE - 10
                    if x0 <= mx <= x0 + TILE_SIZE and y0 <= my <= y0 + TILE_SIZE:
                        hotbar[i] = dragging_item
                        break
                dragging_item = None

    # ------------------ PLAYER MOVEMENT ------------------
    dx=0
    if not inventory_open:
        if keys[pygame.K_a]: dx -= speed
        if keys[pygame.K_d]: dx += speed

    player_velocity_y += 0.8  # Gravity
    if keys[pygame.K_SPACE] and on_ground: player_velocity_y=jump_strength

    # Horizontal movement
    new_x = player_x_pos + dx
    if not check_collision(new_x, player_y_pos, player_width, player_height):
        player_x_pos = new_x

    # Vertical movement
    new_y = player_y_pos + player_velocity_y
    if not check_collision(player_x_pos, new_y, player_width, player_height):
        player_y_pos = new_y
        on_ground=False
    else:
        if player_velocity_y > 0:
            while not check_collision(player_x_pos, player_y_pos+1, player_width, player_height):
                player_y_pos += 1
            on_ground=True
        else:
            while not check_collision(player_x_pos, player_y_pos-1, player_width, player_height):
                player_y_pos -= 1
        player_velocity_y=0

    # ------------------ TNT & ARROWS ------------------
    handle_tnt()
    update_arrows()



    # ------------------ UPDATE CLOUDS ------------------
    for cloud in clouds:
        cloud["x"] += cloud["speed"]
        if cloud["x"] > WORLD_WIDTH * TILE_SIZE + 200:
            cloud["x"] = -cloud["w"]

    # ------------------ DRAW ------------------

    # Pixel-based camera
    camera_x = player_x_pos - WIDTH // 2
    camera_y = player_y_pos - HEIGHT // 2

    camera_x = max(0, min(camera_x, WORLD_WIDTH * TILE_SIZE - WIDTH))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT * TILE_SIZE - HEIGHT))

    ix = int(camera_x)
    iy = int(camera_y)

    offset_x = ix // TILE_SIZE
    offset_y = iy // TILE_SIZE

    pixel_x = ix % TILE_SIZE
    pixel_y = iy % TILE_SIZE

    # ------------------ WORLD (SKY + CLOUDS + TERRAIN) ------------------
    draw_world(viewport_surface, offset_x, offset_y)
    screen.blit(viewport_surface, (-pixel_x, -pixel_y))

    # ------------------ TREE TRUNKS (FOREGROUND) ------------------

    for y in range(SCREEN_TILES_Y + 1):
        for x in range(SCREEN_TILES_X + 1):
            wx = x + offset_x
            wy = y + offset_y

            if 0 <= wx < WORLD_WIDTH and 0 <= wy < WORLD_HEIGHT:
                if world[wy][wx] == 6:  # trunk
                    pygame.draw.rect(
                        screen,
                        get_color(6),
                        (
                            x * TILE_SIZE - pixel_x,
                            y * TILE_SIZE - pixel_y,
                            TILE_SIZE,
                            TILE_SIZE
                        )
                    )

    # ------------------ TREE LEAVES (FOREGROUND) ------------------
    for y in range(SCREEN_TILES_Y + 1):
        for x in range(SCREEN_TILES_X + 1):
            wx = x + offset_x
            wy = y + offset_y

            if 0 <= wx < WORLD_WIDTH and 0 <= wy < WORLD_HEIGHT:
                if world[wy][wx] == 9:  # leaves
                    pygame.draw.rect(
                        screen,
                        get_color(9),
                        (
                            x * TILE_SIZE - pixel_x,
                            y * TILE_SIZE - pixel_y,
                            TILE_SIZE,
                            TILE_SIZE
                        )
                    )

    # ------------------ ENTITIES ------------------
    draw_arrows(screen, offset_x, offset_y)
    screen.blit(
        penguin_surface,
        (player_x_pos - camera_x, player_y_pos - camera_y)
    )

    # ------------------ UI ------------------
    draw_hotbar()
    if inventory_open:
        draw_inventory()
    draw_drag_item()

    # ------------------ MINI-MAP ------------------
    mini_tile_w = MINIMAP_WIDTH / WORLD_WIDTH
    mini_tile_h = MINIMAP_HEIGHT / WORLD_HEIGHT

    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):
            pygame.draw.rect(
                screen,
                get_color(world[y][x]),
                (
                    MINIMAP_X + x * mini_tile_w,
                    MINIMAP_Y + y * mini_tile_h,
                    mini_tile_w,
                    mini_tile_h
                )
            )

    mini_px = MINIMAP_X + (player_x_pos / TILE_SIZE) * mini_tile_w
    mini_py = MINIMAP_Y + (player_y_pos / TILE_SIZE) * mini_tile_h
    pygame.draw.rect(
        screen,
        RED,
        (mini_px, mini_py, mini_tile_w, mini_tile_h)
    )


    # ------------------ HUD ------------------
    coord_text=font.render(f"X:{int(player_x_pos//TILE_SIZE)} Y:{int(player_y_pos//TILE_SIZE)}",True,BLACK)
    screen.blit(coord_text,(10,10))

    # FPS display
    fps_counter += 1
    if time.time() - fps_timer >= 1:
        current_fps = fps_counter
        fps_counter = 0
        fps_timer = time.time()
    fps_text = fps_font.render(f"FPS: {current_fps}", True, RED)
    screen.blit(fps_text, (WIDTH-100, 10))

    # CPU temperature
    cpu_temp = get_cpu_temp()
    temp_text = fps_font.render(f"CPU: {cpu_temp:.1f}°C", True, RED)
    screen.blit(temp_text, (WIDTH-100, 30))

    # Command input
    if command_mode:
        pygame.draw.rect(screen, BLACK, (50, HEIGHT-40, WIDTH-100, 30))
        text_surf = font.render("/"+command_text, True, WHITE)
        screen.blit(text_surf, (60, HEIGHT-35))

    # Show commands
    if show_commands:
        pygame.draw.rect(screen, BLACK, (50, 50, WIDTH-100, 150))
        y_offset = 60
        for cmd, desc in command_descriptions.items():
            text_surf = font.render(desc, True, WHITE)
            screen.blit(text_surf, (60, y_offset))
            y_offset += 25

    # Terminal window
    if terminal_active:
        pygame.draw.rect(screen, BLACK, terminal_rect)
        pygame.draw.rect(screen, WHITE, terminal_rect, 2)
        y = terminal_rect.top + 5
        for line in terminal_output:
            text_surf = font.render(line, True, WHITE)
            screen.blit(text_surf, (terminal_rect.left+5, y))
            y += 20
        input_surf = font.render("> " + terminal_input, True, WHITE)
        screen.blit(input_surf, (terminal_rect.left+5, terminal_rect.bottom - 25))

    pygame.display.flip()
    clock.tick(60)  # Limit to 60 FPS