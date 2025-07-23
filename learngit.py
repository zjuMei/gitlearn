import pygame
import random
import sys

# 初始化pygame
pygame.init()

# 游戏配置
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
CELL_SIZE = 20
CELL_NUMBER_X = WINDOW_WIDTH // CELL_SIZE
CELL_NUMBER_Y = WINDOW_HEIGHT // CELL_SIZE

# 颜色定义
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('贪吃蛇小游戏')
clock = pygame.time.Clock()

# 字体设置 - 使用系统默认字体
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)

class Snake:
    def __init__(self):
        # 蛇的初始位置
        self.body = [pygame.Vector2(5, 10), pygame.Vector2(4, 10), pygame.Vector2(3, 10)]
        self.direction = pygame.Vector2(1, 0)
        self.new_block = False

    def draw_snake(self):
        # 绘制蛇
        for block in self.body:
            x_pos = int(block.x * CELL_SIZE)
            y_pos = int(block.y * CELL_SIZE)
            block_rect = pygame.Rect(x_pos, y_pos, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, GREEN, block_rect)

    def move_snake(self):
        # 移动蛇
        if self.new_block:
            body_copy = self.body[:]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy[:]
            self.new_block = False
        else:
            body_copy = self.body[:-1]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy[:]

    def add_block(self):
        # 增加蛇的长度
        self.new_block = True

    def reset(self):
        # 重置蛇
        self.body = [pygame.Vector2(5, 10), pygame.Vector2(4, 10), pygame.Vector2(3, 10)]
        self.direction = pygame.Vector2(1, 0)
        self.new_block = False

class Food:
    def __init__(self):
        # 食物的初始位置
        self.randomize()

    def draw_food(self):
        # 绘制食物
        food_rect = pygame.Rect(int(self.pos.x * CELL_SIZE), int(self.pos.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, RED, food_rect)

    def randomize(self):
        # 随机生成食物位置
        self.x = random.randint(0, CELL_NUMBER_X - 1)
        self.y = random.randint(0, CELL_NUMBER_Y - 1)
        self.pos = pygame.Vector2(self.x, self.y)

class Obstacle:
    def __init__(self):
        self.positions = []
        self.generate_obstacles()

    def generate_obstacles(self):
        # 生成随机障碍物（减少数量）
        self.positions = []
        obstacle_count = random.randint(3, 8)  # 减少障碍物数量到3-8个
        for _ in range(obstacle_count):
            x = random.randint(0, CELL_NUMBER_X - 1)
            y = random.randint(0, CELL_NUMBER_Y - 1)
            pos = pygame.Vector2(x, y)
            # 确保障碍物不与蛇和食物重叠
            self.positions.append(pos)

    def draw_obstacles(self):
        # 绘制障碍物
        for pos in self.positions:
            x_pos = int(pos.x * CELL_SIZE)
            y_pos = int(pos.y * CELL_SIZE)
            obstacle_rect = pygame.Rect(x_pos, y_pos, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, BLUE, obstacle_rect)

    def reset(self):
        # 重新生成障碍物
        self.generate_obstacles()

class Main:
    def __init__(self):
        self.snake = Snake()
        self.food = Food()
        self.obstacle = Obstacle()
        self.score = 0
        self.game_over_flag = False

    def update(self):
        # 更新游戏状态
        if not self.game_over_flag:
            self.snake.move_snake()
            self.check_collision()
            self.check_fail()

    def draw_elements(self):
        # 绘制游戏元素
        screen.fill(BLACK)
        self.food.draw_food()
        self.obstacle.draw_obstacles()
        self.snake.draw_snake()
        self.draw_score()
        
        if self.game_over_flag:
            self.draw_game_over()

    def check_collision(self):
        # 检查蛇是否吃到食物
        if self.food.pos == self.snake.body[0]:
            self.food.randomize()
            self.obstacle.reset()  # 吃到食物后重新生成障碍物
            self.snake.add_block()
            self.score += 1

        # 确保食物不会生成在蛇身或障碍物上
        for block in self.snake.body[1:]:
            if block == self.food.pos:
                self.food.randomize()
                
        for pos in self.obstacle.positions:
            if pos == self.food.pos:
                self.food.randomize()

    def check_fail(self):
        # 检查游戏是否结束
        # 检查蛇是否撞墙
        if not 0 <= self.snake.body[0].x < CELL_NUMBER_X or not 0 <= self.snake.body[0].y < CELL_NUMBER_Y:
            self.game_over()

        # 检查蛇是否撞到自己
        for block in self.snake.body[1:]:
            if block == self.snake.body[0]:
                self.game_over()
                
        # 检查蛇是否撞到障碍物
        for pos in self.obstacle.positions:
            if pos == self.snake.body[0]:
                self.game_over()

    def game_over(self):
        # 游戏结束
        self.game_over_flag = True

    def draw_game_over(self):
        # 显示游戏结束界面（简化版本）
        # 绘制纯色背景
        pygame.draw.rect(screen, BLACK, (WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 - 100, 400, 200))
        pygame.draw.rect(screen, WHITE, (WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 - 100, 400, 200), 2)
        
        game_over_surface = big_font.render("GAME OVER", True, WHITE)
        game_over_rect = game_over_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 30))
        screen.blit(game_over_surface, game_over_rect)
        
        score_surface = font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
        screen.blit(score_surface, score_rect)
        
        restart_surface = font.render("Press SPACE to restart", True, YELLOW)
        restart_rect = restart_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 60))
        screen.blit(restart_surface, restart_rect)

    def draw_score(self):
        # 显示分数
        score_text = str(self.score)
        score_surface = font.render(score_text, True, WHITE)
        score_x = int(WINDOW_WIDTH - 60)
        score_y = int(WINDOW_HEIGHT - 40)
        score_rect = score_surface.get_rect(center=(score_x, score_y))
        screen.blit(score_surface, score_rect)

    def reset(self):
        # 重置游戏
        self.snake.reset()
        self.food.randomize()
        self.obstacle.reset()
        self.score = 0
        self.game_over_flag = False

# 创建游戏主循环
main_game = Main()

# 游戏主循环
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if main_game.game_over_flag and event.key == pygame.K_SPACE:
                # 游戏结束后按空格键重新开始
                main_game.reset()
            elif not main_game.game_over_flag:
                # 游戏进行中处理方向键
                if event.key == pygame.K_UP:
                    if main_game.snake.direction.y != 1:
                        main_game.snake.direction = pygame.Vector2(0, -1)
                if event.key == pygame.K_DOWN:
                    if main_game.snake.direction.y != -1:
                        main_game.snake.direction = pygame.Vector2(0, 1)
                if event.key == pygame.K_RIGHT:
                    if main_game.snake.direction.x != -1:
                        main_game.snake.direction = pygame.Vector2(1, 0)
                if event.key == pygame.K_LEFT:
                    if main_game.snake.direction.x != 1:
                        main_game.snake.direction = pygame.Vector2(-1, 0)

    main_game.update()
    main_game.draw_elements()
    pygame.display.update()
    clock.tick(8)  # 8帧每秒