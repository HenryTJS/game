import pygame
from pygame.constants import (K_SPACE, K_ESCAPE, K_a, K_d, K_w, K_s, K_LEFT, K_RIGHT, K_UP, K_DOWN)
from pygame.locals import *
import random
import time
import os
import json

# ====================== 初始化设置 ======================
WIDTH, HEIGHT = 512, 768
pygame.init()

if pygame.display.mode_ok((WIDTH, HEIGHT)) == 0:
    print("屏幕显示不支持！")
    exit(0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("智能雷电")

# ====================== 资源加载 ======================
bg0 = pygame.image.load("start_bg0.jpg")
bg1 = pygame.image.load("map1.jpg")
start = pygame.image.load("start.png")
plane = pygame.image.load("plane.png").convert_alpha()
boss_1_img = pygame.image.load("boss_1.png")
boss_2_img = pygame.transform.scale(pygame.image.load("boss_2.png"), (577 // 2, 374 // 2))

# 预加载敌人图片
enemy_images = [pygame.image.load(f"alien_{i}.png") for i in range(1, 6)]

myFont = pygame.font.SysFont("simhei", 45)
info_font = pygame.font.SysFont("simhei", 25)
score_font = pygame.font.SysFont("simhei", 36)

RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# ====================== 最高分系统 ======================
HIGH_SCORE_FILE = "high_score.json"


def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return json.load(f).get("high_score", 0)
        except:
            return 0
    return 0


def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": int(score)}, f)
    except:
        pass


# ====================== 游戏函数 ======================
def check_collision(rect1, rect2):
    if isinstance(rect1, (tuple, list)):
        rect1 = pygame.Rect(rect1[0], rect1[1], rect1[2], rect1[3])
    if isinstance(rect2, (tuple, list)):
        rect2 = pygame.Rect(rect2[0], rect2[1], rect2[2], rect2[3])
    return rect1.colliderect(rect2)


def show_start_screen():
    screen.blit(bg0, (0, 0))
    high_score = load_high_score()
    title = myFont.render("智能雷电", True, RED)
    high_score_text = score_font.render(f"最高分: {high_score}", True, WHITE)
    instructions = [
        info_font.render("游戏说明：WASD控制方向", True, BLACK),
        info_font.render("空格键发射子弹", True, BLACK),
    ]

    screen.blit(title, (170, 100))
    screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, 200))
    for i, inst in enumerate(instructions):
        screen.blit(inst, (110, 350 + i * 40))
    screen.blit(start, (180, 500))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[K_SPACE]:
                    running = False
                elif keys[K_ESCAPE]:
                    exit(0)
            elif event.type == pygame.QUIT:
                running = False
        pygame.display.update()


def show_game_over(score, high_score):
    screen.fill(BLACK)
    if score > high_score:
        high_score = score
        save_high_score(score)

    title = myFont.render("游戏结束", True, RED)
    score_text = score_font.render(f"最终得分: {int(score)}", True, WHITE)
    high_score_text = score_font.render(f"最高分: {high_score}", True, WHITE)
    restart_text = info_font.render("按空格键重新开始", True, WHITE)

    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 150))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2 + 50))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 150))

    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == K_SPACE:
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit(0)


def run_game():
    clock = pygame.time.Clock()
    FPS = 60
    score = 0
    game_over = False

    # ========== 关键计数器 ==========
    normal_enemy_killed = 0
    boss1_killed = 0
    boss2_killed = 0

    speed_multiplier = 1.0

    # ========== 状态标志 ==========
    current_boss = None
    boss_active = False
    enemy_active = False

    # ========== 修改点：添加独立的逃跑计时器 ==========
    boss_escape_timer = 0

    # ========== 玩家飞机设置 ==========
    plane_w, plane_h = 100, 148
    plane_x = float((WIDTH - plane_w) / 2)
    plane_y = float(HEIGHT - plane_h - 20)
    max_speed = 8.0
    acceleration = 1.0
    deceleration = 0.8
    move_speed = 0.0

    # ========== 敌机设置 ==========
    enemy_w, enemy_h = 128, 128
    enemy_x, enemy_y = random.randint(0, WIDTH - enemy_w), -enemy_h
    enemy_img = enemy_images[random.randint(0, 4)]
    enemy_speed = 2.0
    enemy_spawn_time = 0
    enemy_alive_time = 0

    # ========== 敌机子弹设置 ==========
    bullet_img = pygame.image.load("alien_bullet.png")
    bullet_w, bullet_h = 44, 48
    bullet_x, bullet_y = 0, 0
    bullet_speed = 5.0
    bullet_active = False
    last_bullet_time = 0
    bullet_cooldown = 2
    bullet_delay = random.uniform(0.5, 1.5)
    can_shoot = False

    # ========== 玩家导弹设置 ==========
    missile_img = pygame.image.load("feidan.png")
    missile_w, missile_h = 21, 59
    missile_x, missile_y = 0, -missile_h
    missile_speed = 10.0
    missile_active = False

    # ========== Boss设置 ==========
    boss_1_w, boss_1_h = 270, 175
    boss_2_w, boss_2_h = 577 // 2, 374 // 2
    boss_x, boss_y = (WIDTH - boss_1_w) // 2, -boss_1_h
    boss_speed = 1.0
    boss_health = 100
    boss_max_health = 100

    running = True
    while running and not game_over:
        current_time = time.time()
        if enemy_active:
            enemy_alive_time = current_time - enemy_spawn_time

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE and not missile_active:
                    missile_x = plane_x + (plane_w - missile_w) / 2
                    missile_y = plane_y - missile_h
                    missile_active = True
            elif event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        moving_left = keys[K_a] or keys[K_LEFT]
        moving_right = keys[K_d] or keys[K_RIGHT]
        moving_up = keys[K_w] or keys[K_UP]
        moving_down = keys[K_s] or keys[K_DOWN]

        # ========== 游戏逻辑更新 ==========
        current_max_speed = max_speed * speed_multiplier
        current_acceleration = acceleration * speed_multiplier
        current_deceleration = deceleration * speed_multiplier
        current_enemy_speed = enemy_speed * speed_multiplier
        current_bullet_speed = bullet_speed * speed_multiplier
        current_missile_speed = missile_speed * speed_multiplier
        current_boss_speed = boss_speed * speed_multiplier

        # 玩家移动
        if moving_left and not moving_right:
            move_speed = max(move_speed - current_acceleration, -current_max_speed)
        elif moving_right and not moving_left:
            move_speed = min(move_speed + current_acceleration, current_max_speed)
        else:
            if move_speed > 0:
                move_speed = max(move_speed - current_deceleration, 0)
            elif move_speed < 0:
                move_speed = min(move_speed + current_deceleration, 0)
        plane_x += move_speed
        plane_x = max(0, min(plane_x, WIDTH - plane_w))

        if moving_up and not moving_down:
            plane_y = max(plane_y - current_max_speed * 0.7, 0)
        elif moving_down and not moving_up:
            plane_y = min(plane_y + current_max_speed * 0.7, HEIGHT - plane_h)

        # ========== 敌人生成逻辑 ==========
        if not enemy_active and not boss_active:
            if normal_enemy_killed >= 3 > boss1_killed:
                if current_boss != 1:
                    current_boss = 1
                    boss_active = True
                    boss_x = (WIDTH - boss_1_w) // 2
                    boss_y = -boss_1_h
                    boss_health = 100
                    boss_max_health = boss_health
                    print(f"Boss1生成！进度: {boss1_killed}/3")
            elif boss1_killed >= 3 and boss2_killed < 1:
                if current_boss != 2:
                    current_boss = 2
                    boss_active = True
                    boss_x = (WIDTH - boss_2_w) // 2
                    boss_y = -boss_2_h
                    boss_health = 200
                    boss_max_health = boss_health
                    print(f"Boss2生成！击落后将提升速度")
            else:
                enemy_active = True
                enemy_x = random.randint(0, WIDTH - enemy_w)
                enemy_y = -enemy_h
                enemy_img = enemy_images[random.randint(0, 4)]
                enemy_spawn_time = current_time
                can_shoot = False
                bullet_delay = random.uniform(0.5, 1.5)
                print(f"普通敌机生成！还需{3 - normal_enemy_killed % 3}架到Boss1")

        # ========== 普通敌机逻辑 ==========
        enemy_rect = pygame.Rect(0, 0, 0, 0)
        if enemy_active:
            enemy_y += current_enemy_speed
            enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_w, enemy_h)

            if enemy_y > HEIGHT:
                score = score - 1
                print(f"普通敌机逃脱！当前分数: {int(score)}")
                enemy_active = False

            if not can_shoot and enemy_alive_time >= bullet_delay:
                can_shoot = True
            if bullet_active:
                bullet_y += current_bullet_speed
                if bullet_y > HEIGHT:
                    bullet_active = False
            if can_shoot and not bullet_active and (current_time - last_bullet_time) >= bullet_cooldown:
                if random.random() < 0.7:
                    bullet_x = enemy_x + enemy_w / 2 - bullet_w / 2
                    bullet_y = enemy_y + enemy_h
                    bullet_active = True
                    last_bullet_time = current_time

        # ========== Boss逻辑（修正逃跑计时器） ==========
        boss_rect = None
        if boss_active:
            boss_y += current_boss_speed
            boss_rect = pygame.Rect(
                boss_x, boss_y,
                boss_1_w if current_boss == 1 else boss_2_w,
                boss_1_h if current_boss == 1 else boss_2_h
            )

            if boss_y > 100:
                boss_y = 100
                boss_escape_timer += 1 / FPS

                if boss_escape_timer > 10:
                    # 保存当前Boss类型
                    escaping_boss_type = current_boss
                    boss_active = False
                    boss_escape_timer = 0
                    current_boss = None

                    if escaping_boss_type == 1:
                        score = score - 2
                        print("Boss1逃跑！分数-2")
                        normal_enemy_killed = 0
                    elif escaping_boss_type == 2:
                        score = score - 3
                        print("Boss2逃跑！分数-3")
                        normal_enemy_killed = 0
                        boss1_killed = 0

            if boss_health <= 0:
                if current_boss == 1:
                    score += 3
                    boss1_killed += 1
                    normal_enemy_killed = 0
                    print(f"Boss1被击落！进度: {boss1_killed}/3")
                elif current_boss == 2:
                    score += 5
                    boss2_killed += 1
                    speed_multiplier *= 1.2
                    normal_enemy_killed = 0
                    boss1_killed = 0
                    print(f"Boss2被击落！速度提升至{speed_multiplier:.1f}x")

                boss_active = False
                current_boss = None
                boss_escape_timer = 0

        # ========== 导弹移动 ==========
        if missile_active:
            missile_y -= current_missile_speed
            if missile_y < -missile_h:
                missile_active = False

        # ========== 碰撞检测 ==========
        player_rect = pygame.Rect(int(plane_x), int(plane_y), plane_w, plane_h)
        missile_rect = pygame.Rect(int(missile_x), int(missile_y), missile_w, missile_h) if missile_active else None
        bullet_rect = pygame.Rect(bullet_x, bullet_y, bullet_w, bullet_h) if bullet_active else None

        missile_hit = False

        if boss_active and boss_rect is not None:
            # 玩家与Boss碰撞检测
            if check_collision(player_rect, boss_rect):
                print("玩家与Boss碰撞！游戏结束")
                game_over = True

        if enemy_active and missile_active and missile_rect:
            if check_collision(missile_rect, enemy_rect):
                score += 2
                normal_enemy_killed += 1
                enemy_active = False
                bullet_active = False
                missile_hit = True
                print(f"普通敌机被击落！进度: {normal_enemy_killed}/3")

        if boss_active and missile_active and missile_rect:
            if check_collision(missile_rect, boss_rect):
                damage = random.randint(10, 20)
                boss_health -= damage
                print(f"导弹击中Boss{current_boss}！伤害:{damage} 剩余血量:{boss_health}")
                missile_hit = True

        if missile_active and missile_rect and bullet_rect:
            if check_collision(missile_rect, bullet_rect):
                score += 1
                bullet_active = False
                missile_hit = True

        if missile_hit:
            missile_active = False

        if (bullet_active and bullet_rect and check_collision(bullet_rect, player_rect)) or \
                (enemy_active and check_collision(enemy_rect, player_rect)) or \
                (boss_active and check_collision(boss_rect, player_rect)):
            print("玩家被击中！游戏结束")
            game_over = True

        if score < 0:
            print("分数已耗尽，游戏结束")
            game_over = True
            score = 0

        # ========== 画面渲染 ==========
        screen.blit(bg1, (0, 0))
        screen.blit(plane, (int(plane_x), int(plane_y)))

        if enemy_active:
            screen.blit(enemy_img, (enemy_x, enemy_y))

        if bullet_active:
            screen.blit(bullet_img, (bullet_x, bullet_y))

        if missile_active:
            screen.blit(missile_img, (int(missile_x), int(missile_y)))

        if boss_active:
            screen.blit(boss_1_img if current_boss == 1 else boss_2_img, (boss_x, boss_y))
            health_width = int((boss_health / boss_max_health) * (200 if current_boss == 1 else 300))
            pygame.draw.rect(screen, RED, (boss_x, boss_y - 10, health_width, 5))

        score_text = score_font.render(f"分数: {int(score)}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.update()
        clock.tick(FPS)

    if game_over:
        final_score = max(0, score)
        high_score = load_high_score()

        if final_score <= 0:
            print("游戏结束，最终得分为0")

        show_game_over(final_score, high_score)

if __name__ == '__main__':
    while True:
        show_start_screen()
        run_game()