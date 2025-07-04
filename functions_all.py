import pygame
import random
import time
from pygame.constants import (K_SPACE, K_m, K_k, K_ESCAPE, K_a, K_d, K_s, K_w, K_LEFT, K_RIGHT, K_UP, K_DOWN)
from typing import Optional, Union
from resource_load import (myFont, RED, score_font, WHITE, info_font, BLACK, WIDTH, HEIGHT, bg0, start, NORMAL_TO_BOSS1, BOSS1_TO_BOSS2, enemy_images, FPS, bg1, YELLOW, plane, boss_1_img, boss_2_img)
from high_score import save_high_score, load_high_score

# 创建游戏窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("智能雷电")

# ====================== 游戏函数 ======================

def check_collision(rect1, rect2, radius1=None, radius2=None):
    """
    检查两个矩形或对象之间是否发生碰撞，使用圆形碰撞检测。
    :param rect1: 第一个矩形或对象
    :param rect2: 第二个矩形或对象
    :param radius1: 第一个对象的半径，默认为矩形短边的一半
    :param radius2: 第二个对象的半径，默认为矩形短边的一半
    :return: 如果发生碰撞返回True，否则返回False
    """
    # 提前计算中心点和半径
    if isinstance(rect1, (tuple, list)):
        x1, y1, w1, h1 = rect1
        center1 = (x1 + w1 / 2, y1 + h1 / 2)
        r1 = radius1 if radius1 is not None else min(w1, h1) / 2
    else:
        center1 = (rect1.x + rect1.width / 2, rect1.y + rect1.height / 2)
        r1 = radius1 if radius1 is not None else min(rect1.width, rect1.height) / 2

    if isinstance(rect2, (tuple, list)):
        x2, y2, w2, h2 = rect2
        center2 = (x2 + w2 / 2, y2 + h2 / 2)
        r2 = radius2 if radius2 is not None else min(w2, h2) / 2
    else:
        center2 = (rect2.x + rect2.width / 2, rect2.y + rect2.height / 2)
        r2 = radius2 if radius2 is not None else min(rect2.width, rect2.height) / 2

    # 计算距离平方
    dx = center1[0] - center2[0]
    dy = center1[1] - center2[1]
    distance_squared = dx * dx + dy * dy
    radius_sum = r1 + r2
    return distance_squared <= radius_sum * radius_sum

def show_game_over(score: Union[int, float], high_score: int) -> None:
    """
    显示游戏结束界面，包括最终得分、最高分和重新开始提示。
    :param score: 本次游戏的最终得分
    :param high_score: 历史最高分
    """
    # 填充背景颜色
    screen.fill(BLACK)

    # 检查是否打破最高分记录
    if score > high_score:
        high_score = score
        save_high_score(score)

    # 渲染文本
    title = myFont.render("游戏结束", True, RED)
    score_text = score_font.render(f"最终得分: {int(score)}", True, WHITE)
    high_score_text = score_font.render(f"最高分: {high_score}", True, WHITE)
    restart_text = info_font.render("按空格键或鼠标左键重新开始", True, WHITE)

    # 布局文本
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit(0)

def show_start_screen() -> Optional[bool]:
    """
    显示开始界面，等待用户选择控制方式（鼠标或键盘）。
    :return: 如果用户选择鼠标控制返回True，键盘控制返回False，退出返回None
    """
    # 绘制背景图片
    screen.blit(bg0, (0, 0))
    high_score = load_high_score()

    # 渲染文本
    title = myFont.render("智能雷电", True, RED)
    high_score_text = score_font.render(f"最高分: {high_score}", True, WHITE)
    instructions = [
        info_font.render("游戏说明：按M键使用鼠标控制开始游戏", True, BLACK),
        info_font.render("按K键使用键盘控制开始游戏", True, BLACK),
    ]

    # 布局文本
    screen.blit(title, (170, 100))
    screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, 200))
    for i, inst in enumerate(instructions):
        screen.blit(inst, (50, 350 + i * 40))
    screen.blit(start, (180, 500))

    running = True
    selected_control = None
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_m or event.key == K_k:
                    selected_control = (event.key == K_m)
                    running = False
                elif event.key == K_ESCAPE:
                    exit(0)
            elif event.type == pygame.QUIT:
                running = False
        pygame.display.update()

    return selected_control

def run_game(mouse_control: bool) -> None:
    """
    游戏主循环，处理游戏逻辑、碰撞检测和画面渲染。
    :param mouse_control: 是否使用鼠标控制
    """
    clock = pygame.time.Clock()

    # ========== 计数器和计时器 ==========
    normal_enemy_killed = 0  # 普通敌机击落数量
    boss1_killed = 0  # Boss1击落数量
    boss2_killed = 0  # Boss2击落数量
    speed_multiplier = 1.0  # 速度倍数
    boss_escape_timer = 0  # Boss逃脱计时器
    score = 0  # 得分

    # ========== 状态标志 ==========
    current_boss = None  # 当前激活的Boss类型
    boss_active = False  # Boss是否激活
    enemy_active = False  # 普通敌机是否激活
    game_over = False  # 游戏是否结束

    # ========== 玩家飞机设置 ==========
    plane_w, plane_h = 100, 148  # 玩家飞机宽度和高度
    plane_x = float((WIDTH - plane_w) / 2)  # 玩家飞机初始X坐标
    plane_y = float(HEIGHT - plane_h - 20)  # 玩家飞机初始Y坐标
    max_speed = 8.0  # 最大移动速度
    acceleration = 1.0  # 加速度
    deceleration = 0.8  # 减速度
    move_speed = 0.0  # 当前移动速度

    # ========== 敌机设置 ==========
    enemy_w, enemy_h = 128, 128  # 敌机宽度和高度
    enemy_x, enemy_y = random.randint(0, WIDTH - enemy_w), -enemy_h  # 敌机初始位置
    enemy_img = enemy_images[random.randint(0, 4)]  # 敌机图片
    enemy_speed = 2.0  # 敌机移动速度
    enemy_spawn_time = 0  # 敌机生成时间
    enemy_alive_time = 0  # 敌机存活时间

    # ========== 敌机子弹设置 ==========
    bullet_img = pygame.image.load("alien_bullet.png")  # 敌机子弹图片
    bullet_w, bullet_h = 44, 48  # 敌机子弹宽度和高度
    bullet_x, bullet_y = 0, 0  # 敌机子弹初始位置
    bullet_speed = 5.0  # 敌机子弹移动速度
    bullet_active = False  # 敌机子弹是否激活
    last_bullet_time = 0  # 上次发射子弹时间
    bullet_cooldown = 2  # 子弹冷却时间
    bullet_delay = random.uniform(0.5, 1.5)  # 子弹发射延迟
    can_shoot = False  # 是否可以发射子弹

    # ========== 玩家导弹设置 ==========
    missile_img = pygame.image.load("feidan.png")  # 玩家导弹图片
    missile_w, missile_h = 21, 59  # 玩家导弹宽度和高度
    missile_x, missile_y = 0, -missile_h  # 玩家导弹初始位置
    missile_speed = 10.0  # 玩家导弹移动速度
    missile_active = False  # 玩家导弹是否激活

    # ========== Boss设置 ==========
    boss_1_w, boss_1_h = 270, 175  # Boss1宽度和高度
    boss_2_w, boss_2_h = 577 // 2, 374 // 2  # Boss2宽度和高度
    boss_x, boss_y = (WIDTH - boss_1_w) // 2, -boss_1_h  # Boss初始位置
    boss_speed = 1.0  # Boss移动速度
    boss_health = 100  # Boss当前生命值
    boss_max_health = 100  # Boss最大生命值

    # ========== 鼠标相关设置 ==========
    crosshair = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(crosshair, (255, 255, 255, 180), (16, 16), 16)
    pygame.draw.circle(crosshair, (0, 0, 0, 180), (16, 16), 3)
    pygame.draw.line(crosshair, (0, 0, 0, 180), (16, 0), (16, 8))
    pygame.draw.line(crosshair, (0, 0, 0, 180), (16, 24), (16, 32))
    pygame.draw.line(crosshair, (0, 0, 0, 180), (0, 16), (8, 16))
    pygame.draw.line(crosshair, (0, 0, 0, 180), (24, 16), (32, 16))

    # ========== 连击系统 ==========
    combo_window = 0.5  # 连击时间窗口
    hit_times = []  # 击中时间列表
    combo_count = 0  # 连击次数
    last_combo_score_time = 0  # 上次连击得分时间

    running = True
    while running and not game_over:
        current_time = time.time()
        if enemy_active:
            enemy_alive_time = current_time - enemy_spawn_time

        # ========== 处理连击系统 ==========
        while hit_times and current_time - hit_times[0] > combo_window:
            hit_times.pop(0)

        if len(hit_times) >= 2:
            if hit_times[-1] - hit_times[-2] <= combo_window:
                if current_time - last_combo_score_time > combo_window:
                    score += 1
                    combo_count += 1
                    last_combo_score_time = current_time
                    print(f"连击成功! 当前分数: {int(score)} (连击数: {combo_count})")

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE and not missile_active:
                    missile_x = plane_x + (plane_w - missile_w) / 2
                    missile_y = plane_y - missile_h
                    missile_active = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not missile_active:  # 鼠标左键发射导弹
                    missile_x = plane_x + (plane_w - missile_w) / 2
                    missile_y = plane_y - missile_h
                    missile_active = True
            elif event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:  # 按M键切换控制方式
                mouse_control = not mouse_control
                print("鼠标控制" if mouse_control else "键盘控制")

        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # 如果使用鼠标控制，更新飞机位置到鼠标附近
        if mouse_control:
            target_x = mouse_x - plane_w / 2
            target_y = mouse_y - plane_h / 2
            plane_x = max(0, min(target_x, WIDTH - plane_w))
            plane_y = max(0, min(target_y, HEIGHT - plane_h))

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

        # 键盘控制移动
        if not mouse_control:
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
            if normal_enemy_killed >= NORMAL_TO_BOSS1 and boss1_killed < BOSS1_TO_BOSS2:
                if current_boss != 1:
                    current_boss = 1
                    boss_active = True
                    boss_x = (WIDTH - boss_1_w) // 2
                    boss_y = -boss_1_h
                    boss_health = 100
                    boss_max_health = boss_health
                    print(f"Boss1生成！进度: {boss1_killed}/{BOSS1_TO_BOSS2}")
            elif boss1_killed >= BOSS1_TO_BOSS2:
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
                print(f"普通敌机生成！还需{NORMAL_TO_BOSS1 - normal_enemy_killed}架到Boss1")

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

        # ========== Boss逻辑 ==========
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

                if boss_escape_timer > 5:
                    escaping_boss_type = current_boss
                    boss_active = False
                    boss_escape_timer = 0
                    current_boss = None
                    bullet_active = False
                    can_shoot = False

                    # 修改Boss逃跑扣分逻辑
                    if escaping_boss_type == 1:
                        score = score - 10  # Boss1逃跑扣10分
                        print("Boss1逃跑！分数-10")
                    elif escaping_boss_type == 2:
                        score = score - 20  # Boss2逃跑扣20分
                        print("Boss2逃跑！分数-20")
                    normal_enemy_killed = 0
                    if escaping_boss_type == 2:
                        boss1_killed = 0

            if bullet_active:
                bullet_y += current_bullet_speed
                if bullet_y > HEIGHT:
                    bullet_active = False
                    can_shoot = False

            if boss_health <= 0:
                if current_boss == 1:
                    boss1_killed += 1
                    normal_enemy_killed = 0
                    print(f"Boss1被击落！进度: {boss1_killed}/{BOSS1_TO_BOSS2}")
                elif current_boss == 2:
                    boss2_killed += 1
                    speed_multiplier *= 1.2
                    normal_enemy_killed = 0
                    boss1_killed = 0
                    print(f"Boss2被击落！速度提升至{speed_multiplier:.1f}x")

                boss_active = False
                current_boss = None
                boss_escape_timer = 0
                bullet_active = False
                can_shoot = False

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
            boss_radius = min(boss_1_w, boss_1_h) / 2 if current_boss == 1 else min(boss_2_w, boss_2_h) / 2
            if check_collision(player_rect, boss_rect, radius2=boss_radius):
                print("玩家与Boss碰撞！游戏结束")
                game_over = True

        if enemy_active and missile_active and missile_rect:
            if check_collision(missile_rect, enemy_rect, radius2=min(enemy_w, enemy_h) / 2):
                score += 2
                normal_enemy_killed += 1
                enemy_active = False
                missile_hit = True
                hit_times.append(current_time)  # 记录击中时间
                print(f"普通敌机被击落！进度: {normal_enemy_killed}/{NORMAL_TO_BOSS1}")

        if boss_active and missile_active and missile_rect:
            boss_radius = min(boss_1_w, boss_1_h) / 2 if current_boss == 1 else min(boss_2_w, boss_2_h) / 2
            if check_collision(missile_rect, boss_rect, radius2=boss_radius):
                damage = random.randint(10, 20)
                boss_health -= damage
                # 修改击中Boss得分逻辑：每次击中加2分
                score += 2
                print(f"导弹击中Boss{current_boss}！伤害:{damage} 剩余血量:{boss_health} 得分+2")
                missile_hit = True

        if missile_active and missile_rect and bullet_rect:
            if check_collision(missile_rect, bullet_rect, radius2=min(bullet_w, bullet_h) / 2):
                score += 1
                bullet_active = False
                missile_hit = True
                hit_times.append(current_time)
                print(f"击中敌机子弹！当前分数: {int(score)}")

        if missile_hit:
            missile_active = False

        if bullet_active and bullet_rect:
            if check_collision(bullet_rect, player_rect, radius1=min(bullet_w, bullet_h) / 2):
                print("玩家被敌机子弹击中！游戏结束")
                game_over = True

        if enemy_active and check_collision(enemy_rect, player_rect, radius2=min(enemy_w, enemy_h) / 2):
            print("玩家与敌机碰撞！游戏结束")
            game_over = True

        if boss_active and boss_rect is not None:
            boss_radius = min(boss_1_w, boss_1_h) / 2 if current_boss == 1 else min(boss_2_w, boss_2_h) / 2
            if check_collision(player_rect, boss_rect, radius2=boss_radius):
                print("玩家与Boss碰撞！游戏结束")
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

        # 显示连击信息
        if combo_count > 0:
            combo_text = info_font.render(f"连击: {combo_count}", True, (255, 215, 0))  # 金色
            screen.blit(combo_text, (10, 50))

        # 显示准星
        if mouse_control:
            screen.blit(crosshair, (mouse_x - 16, mouse_y - 16))

        score_text = score_font.render(f"分数: {int(score)}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # 显示当前控制方式
        control_text = info_font.render("鼠标控制" if mouse_control else "键盘控制", True, YELLOW)
        screen.blit(control_text, (WIDTH - control_text.get_width() - 10, 10))

        pygame.display.update()
        clock.tick(FPS)

    if game_over:
        final_score = max(0, score)
        high_score = load_high_score()

        if final_score <= 0:
            print("游戏结束，最终得分为0")

        show_game_over(final_score, high_score)