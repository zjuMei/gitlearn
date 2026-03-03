import json
import pathlib
import random
import sys
from collections import deque

import pygame

pygame.init()

# Window and grid settings
CELL_SIZE = 24
GRID_WIDTH = 26
GRID_HEIGHT = 26
HUD_HEIGHT = 56
BOARD_TOP = HUD_HEIGHT
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = HUD_HEIGHT + GRID_HEIGHT * CELL_SIZE

FPS = 60
MOVE_EVENT = pygame.USEREVENT + 1

# Color palette
BG_DARK = (18, 25, 32)
BG_LIGHT = (24, 34, 43)
BG_MENU = (12, 18, 25)
SNAKE_HEAD = (115, 224, 123)
SNAKE_BODY = (63, 176, 84)
FOOD_COLOR = (239, 85, 96)
OBSTACLE_COLOR = (57, 117, 174)
OBSTACLE_EDGE = (99, 161, 221)
TEXT_PRIMARY = (242, 246, 249)
TEXT_ACCENT = (255, 214, 102)
TEXT_MUTED = (163, 177, 191)
PANEL_BG = (13, 18, 24)
PANEL_EDGE = (56, 72, 88)
CARD_BG = (24, 35, 46)
CARD_ACTIVE = (37, 59, 78)
CARD_EDGE = (75, 108, 134)
OVERLAY = (0, 0, 0, 165)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake Arena")
clock = pygame.time.Clock()

font_small = pygame.font.SysFont("consolas", 22)
font_medium = pygame.font.SysFont("consolas", 28, bold=True)
font_large = pygame.font.SysFont("consolas", 64, bold=True)
font_title = pygame.font.SysFont("consolas", 38, bold=True)

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "base_interval": 220,
        "min_interval": 100,
        "accel_every": 6,
        "accel_step": 8,
        "obstacle_base": 2,
        "obstacle_growth": 4,
        "obstacle_max": 10,
    },
    "normal": {
        "label": "Normal",
        "base_interval": 170,
        "min_interval": 70,
        "accel_every": 4,
        "accel_step": 8,
        "obstacle_base": 4,
        "obstacle_growth": 3,
        "obstacle_max": 14,
    },
    "hard": {
        "label": "Hard",
        "base_interval": 130,
        "min_interval": 50,
        "accel_every": 3,
        "accel_step": 10,
        "obstacle_base": 6,
        "obstacle_growth": 2,
        "obstacle_max": 20,
    },
}

MODES = {
    "classic": "Classic",
    "wrap": "Wrap",
}

SAVE_FILE = pathlib.Path("save.json")


def load_high_score() -> int:
    try:
        return json.loads(SAVE_FILE.read_text()).get("high_score", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_high_score(score: int) -> None:
    SAVE_FILE.write_text(json.dumps({"high_score": score}))


def is_opposite(d1: pygame.Vector2, d2: pygame.Vector2) -> bool:
    return d1.x == -d2.x and d1.y == -d2.y


def is_pause_key(event: pygame.event.Event) -> bool:
    return event.key in (pygame.K_p, pygame.K_PAUSE)


# Snake head eye offsets per direction (dx, dy) -> (eye1_offset, eye2_offset)
_EYE_OFFSETS = {
    (1,  0): (( 4, -4), ( 4,  4)),
    (-1, 0): ((-4, -4), (-4,  4)),
    (0,  1): ((-4,  4), ( 4,  4)),
    (0, -1): ((-4, -4), ( 4, -4)),
}


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [
            pygame.Vector2(7, 12),
            pygame.Vector2(6, 12),
            pygame.Vector2(5, 12),
        ]
        self.direction = pygame.Vector2(1, 0)
        self._dir_queue = deque(maxlen=2)  # type: deque

    def queue_direction(self, new_direction: pygame.Vector2):
        # Use the last queued direction (or current) to check for reversal
        last = self._dir_queue[-1] if self._dir_queue else self.direction
        if not is_opposite(last, new_direction):
            self._dir_queue.append(new_direction)

    def next_head(self) -> pygame.Vector2:
        if self._dir_queue:
            self.direction = self._dir_queue.popleft()
        return self.body[0] + self.direction


class Game:
    def __init__(self):
        self.high_score = load_high_score()
        self.snake = Snake()
        self.food = pygame.Vector2(0, 0)
        self.obstacles = set()
        self.score = 0
        self.paused = False
        self.game_over = False
        self.in_menu = True
        self.difficulty = "normal"
        self.mode = "classic"
        self._board_surface = self._build_board_surface()
        self._overlay_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self._overlay_surface.fill(OVERLAY)
        self.spawn_food()
        self.generate_obstacles(self.target_obstacle_count())
        pygame.time.set_timer(MOVE_EVENT, 0)

    @staticmethod
    def _build_board_surface() -> pygame.Surface:
        surf = pygame.Surface((WINDOW_WIDTH, GRID_HEIGHT * CELL_SIZE))
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                color = BG_LIGHT if (x + y) % 2 == 0 else BG_DARK
                pygame.draw.rect(surf, color, pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        return surf

    def movement_interval(self) -> int:
        config = DIFFICULTIES[self.difficulty]
        speedups = self.score // config["accel_every"]
        interval = config["base_interval"] - speedups * config["accel_step"]
        return max(config["min_interval"], interval)

    def set_timer_for_current_speed(self):
        pygame.time.set_timer(MOVE_EVENT, self.movement_interval())

    def start_round(self):
        self.snake.reset()
        self.score = 0
        self.paused = False
        self.game_over = False
        self.in_menu = False
        self.obstacles.clear()
        self.spawn_food()
        self.generate_obstacles(self.target_obstacle_count())
        self.set_timer_for_current_speed()

    def back_to_menu(self):
        self.in_menu = True
        self.paused = False
        self.game_over = False
        pygame.time.set_timer(MOVE_EVENT, 0)

    def target_obstacle_count(self) -> int:
        config = DIFFICULTIES[self.difficulty]
        return min(
            config["obstacle_max"],
            config["obstacle_base"] + self.score // config["obstacle_growth"],
        )

    def random_free_cell(self, extra_blocked=None) -> pygame.Vector2:
        blocked = {tuple(map(int, part)) for part in self.snake.body}
        blocked.update(self.obstacles)
        if extra_blocked:
            blocked.update(extra_blocked)

        free_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in blocked
        ]

        if not free_cells:
            return self.snake.body[0]

        x, y = random.choice(free_cells)
        return pygame.Vector2(x, y)

    def spawn_food(self):
        self.food = self.random_free_cell()

    def generate_obstacles(self, count: int):
        self.obstacles.clear()
        blocked = {tuple(map(int, part)) for part in self.snake.body}
        blocked.add((int(self.food.x), int(self.food.y)))

        # Safety zone: exclude cells within Manhattan distance 2 of the snake head
        hx, hy = int(self.snake.body[0].x), int(self.snake.body[0].y)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if abs(dx) + abs(dy) <= 2:
                    blocked.add((hx + dx, hy + dy))

        all_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in blocked
        ]
        random.shuffle(all_cells)
        for x, y in all_cells[:count]:
            self.obstacles.add((x, y))

    def step(self):
        if self.in_menu or self.game_over or self.paused:
            return

        next_head = self.snake.next_head()

        # Wall behavior depends on selected mode.
        if self.mode == "classic":
            if not (0 <= next_head.x < GRID_WIDTH and 0 <= next_head.y < GRID_HEIGHT):
                self.game_over = True
                return
        else:
            next_head.x %= GRID_WIDTH
            next_head.y %= GRID_HEIGHT

        # Hit self — exclude tail only when the snake won't grow this step,
        # because the tail will be removed before the new head occupies its cell.
        eating = next_head == self.food
        body_to_check = self.snake.body if eating else self.snake.body[:-1]
        if next_head in body_to_check:
            self.game_over = True
            return

        # Hit obstacle
        if (int(next_head.x), int(next_head.y)) in self.obstacles:
            self.game_over = True
            return

        self.snake.body.insert(0, next_head)

        if eating:
            self.score += 1
            self.high_score = max(self.high_score, self.score)
            save_high_score(self.high_score)
            self.spawn_food()
            self.generate_obstacles(self.target_obstacle_count())
            self.set_timer_for_current_speed()
        else:
            self.snake.body.pop()

    def draw_board(self):
        screen.blit(self._board_surface, (0, BOARD_TOP))

    def draw_food(self):
        center = (
            int(self.food.x * CELL_SIZE + CELL_SIZE / 2),
            int(BOARD_TOP + self.food.y * CELL_SIZE + CELL_SIZE / 2),
        )
        pygame.draw.circle(screen, FOOD_COLOR, center, CELL_SIZE // 2 - 3)

    def draw_obstacles(self):
        for x, y in self.obstacles:
            rect = pygame.Rect(
                int(x * CELL_SIZE + 2),
                int(BOARD_TOP + y * CELL_SIZE + 2),
                CELL_SIZE - 4,
                CELL_SIZE - 4,
            )
            pygame.draw.rect(screen, OBSTACLE_COLOR, rect, border_radius=5)
            pygame.draw.rect(screen, OBSTACLE_EDGE, rect, width=1, border_radius=5)

    def draw_snake(self):
        for index, block in enumerate(self.snake.body):
            rect = pygame.Rect(
                int(block.x * CELL_SIZE + 2),
                int(BOARD_TOP + block.y * CELL_SIZE + 2),
                CELL_SIZE - 4,
                CELL_SIZE - 4,
            )
            color = SNAKE_HEAD if index == 0 else SNAKE_BODY
            pygame.draw.rect(screen, color, rect, border_radius=7)

        # Add simple "eyes" to make the head easier to track.
        head = self.snake.body[0]
        head_center_x = int(head.x * CELL_SIZE + CELL_SIZE / 2)
        head_center_y = int(BOARD_TOP + head.y * CELL_SIZE + CELL_SIZE / 2)
        dir_key = (int(self.snake.direction.x), int(self.snake.direction.y))
        (ox1, oy1), (ox2, oy2) = _EYE_OFFSETS[dir_key]
        pygame.draw.circle(screen, PANEL_BG, (head_center_x + ox1, head_center_y + oy1), 2)
        pygame.draw.circle(screen, PANEL_BG, (head_center_x + ox2, head_center_y + oy2), 2)

    def draw_hud(self):
        panel = pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT)
        pygame.draw.rect(screen, PANEL_BG, panel)
        pygame.draw.line(screen, PANEL_EDGE, (0, HUD_HEIGHT - 1), (WINDOW_WIDTH, HUD_HEIGHT - 1), 2)

        score_text = font_medium.render(f"Score: {self.score}", True, TEXT_PRIMARY)
        high_text = font_small.render(f"Best: {self.high_score}", True, TEXT_ACCENT)
        meta_text = font_small.render(
            f"{DIFFICULTIES[self.difficulty]['label']} | {MODES[self.mode]}",
            True,
            TEXT_ACCENT,
        )
        state = "MENU" if self.in_menu else ("PAUSED" if self.paused else ("GAME OVER" if self.game_over else "RUNNING"))
        state_text = font_small.render(f"State: {state}", True, TEXT_MUTED)
        hint_text = font_small.render("Arrows: Move  P: Pause  R/Esc: Menu", True, TEXT_PRIMARY)

        screen.blit(score_text, (12, 12))
        screen.blit(high_text, (180, 16))
        screen.blit(meta_text, (310, 16))
        screen.blit(state_text, (510, 16))
        screen.blit(hint_text, (12, 34))

    def draw_overlay(self, title: str, subtitle: str):
        screen.blit(self._overlay_surface, (0, 0))

        title_surf = font_large.render(title, True, TEXT_PRIMARY)
        subtitle_surf = font_small.render(subtitle, True, TEXT_ACCENT)

        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 22))
        subtitle_rect = subtitle_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 26))

        screen.blit(title_surf, title_rect)
        screen.blit(subtitle_surf, subtitle_rect)

    def draw_menu_card(self, rect: pygame.Rect, title: str, subtitle: str, active: bool):
        bg = CARD_ACTIVE if active else CARD_BG
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, CARD_EDGE, rect, width=2, border_radius=10)
        title_color = TEXT_ACCENT if active else TEXT_PRIMARY
        subtitle_color = TEXT_PRIMARY if active else TEXT_MUTED
        title_surf = font_medium.render(title, True, title_color)
        subtitle_surf = font_small.render(subtitle, True, subtitle_color)
        screen.blit(title_surf, (rect.x + 16, rect.y + 10))
        screen.blit(subtitle_surf, (rect.x + 16, rect.y + 44))

    def draw(self):
        self.draw_board()
        self.draw_food()
        self.draw_obstacles()
        self.draw_snake()
        self.draw_hud()

        if self.paused and not self.game_over:
            self.draw_overlay("PAUSED", "Press P to continue  |  Press R/Esc to menu")
        if self.game_over:
            self.draw_overlay("GAME OVER", "Press Space to restart  |  Press R/Esc to menu")

    def draw_menu(self):
        screen.fill(BG_MENU)
        self.draw_board()
        self.draw_hud()

        title = font_title.render("SNAKE ARENA", True, TEXT_PRIMARY)
        subtitle = font_small.render("Choose difficulty and mode, then press Enter", True, TEXT_MUTED)
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 120)))
        screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 156)))

        left = WINDOW_WIDTH // 2 - 250
        top = 205
        width = 500
        card_h = 82
        gap = 14

        self.draw_menu_card(
            pygame.Rect(left, top, width, card_h),
            "[1] Easy",
            "Slower speed, fewer obstacles",
            self.difficulty == "easy",
        )
        self.draw_menu_card(
            pygame.Rect(left, top + (card_h + gap), width, card_h),
            "[2] Normal",
            "Balanced speed and obstacle growth",
            self.difficulty == "normal",
        )
        self.draw_menu_card(
            pygame.Rect(left, top + 2 * (card_h + gap), width, card_h),
            "[3] Hard",
            "Fast pace, denser obstacle field",
            self.difficulty == "hard",
        )
        self.draw_menu_card(
            pygame.Rect(left, top + 3 * (card_h + gap), width, card_h),
            "[M] Mode",
            f"Current: {MODES[self.mode]}  (Classic = wall death, Wrap = pass through)",
            True,
        )

        foot = font_small.render("Enter: Start   Esc: Quit", True, TEXT_ACCENT)
        screen.blit(foot, foot.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 34)))


def main():
    game = Game()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == MOVE_EVENT:
                game.step()

            if event.type == pygame.KEYDOWN:
                if game.in_menu:
                    if event.key == pygame.K_1:
                        game.difficulty = "easy"
                    elif event.key == pygame.K_2:
                        game.difficulty = "normal"
                    elif event.key == pygame.K_3:
                        game.difficulty = "hard"
                    elif event.key == pygame.K_m:
                        game.mode = "wrap" if game.mode == "classic" else "classic"
                    elif event.key == pygame.K_RETURN:
                        game.start_round()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    continue

                if event.key in (pygame.K_r, pygame.K_ESCAPE):
                    game.back_to_menu()
                    continue

                if event.key == pygame.K_SPACE and game.game_over:
                    game.start_round()
                    continue

                if is_pause_key(event) and not game.game_over:
                    game.paused = not game.paused
                    continue

                if game.game_over:
                    continue

                if event.key == pygame.K_UP:
                    game.snake.queue_direction(pygame.Vector2(0, -1))
                elif event.key == pygame.K_DOWN:
                    game.snake.queue_direction(pygame.Vector2(0, 1))
                elif event.key == pygame.K_LEFT:
                    game.snake.queue_direction(pygame.Vector2(-1, 0))
                elif event.key == pygame.K_RIGHT:
                    game.snake.queue_direction(pygame.Vector2(1, 0))

        if game.in_menu:
            game.draw_menu()
        else:
            game.draw()
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
