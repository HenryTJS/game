import pygame
import random
import time
import cv2
from pygame.constants import (K_SPACE, K_m, K_k, K_f, K_ESCAPE, K_a, K_d, K_s, K_w, K_LEFT, K_RIGHT, K_UP, K_DOWN)
from resource_load import (myFont, COLORS, score_font, info_font, WIDTH, HEIGHT, bg0, start, NORMAL_TO_BOSS1,
                           BOSS1_TO_BOSS2, enemy_images, FPS, bg1, plane, boss_1_img, boss_2_img)
from high_score import save_high_score, load_high_score
from threading import Thread
from collections import deque

# 人脸控制相关变量
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 摄像头设置
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 坐标映射参数
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
GAME_WIDTH = WIDTH
GAME_HEIGHT = HEIGHT

# 人脸检测线程
face_detection_running = True
current_face_pos = None
face_positions = deque(maxlen=5)


def map_camera_to_game(camera_x, camera_y):
    # 水平翻转x坐标
    flipped_x = CAMERA_WIDTH - camera_x

    # 线性映射
    game_x = flipped_x * (GAME_WIDTH / CAMERA_WIDTH)
    game_y = camera_y * (GAME_HEIGHT / CAMERA_HEIGHT)

    return game_x, game_y


def face_detection_thread():
    global current_face_pos
    while face_detection_running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        # 左右翻转摄像头画面
        frame = cv2.flip(frame, 1)

        # 显示摄像头窗口
        cv2.imshow("Camera (Face Control)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # 检测人脸
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))

        if len(faces) > 0:
            main_face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = main_face
            face_center_x = x + w // 2
            face_center_y = y + h // 2

            # 坐标转换
            game_x, game_y = map_camera_to_game(CAMERA_WIDTH - face_center_x, face_center_y)
            game_x = max(0, min(game_x, GAME_WIDTH))
            game_y = max(0, min(game_y, GAME_HEIGHT))

            current_face_pos = (game_x, game_y)
            face_positions.append((game_x, game_y))
        else:
            current_face_pos = None
            face_positions.clear()


# 启动人脸检测线程
face_thread = Thread(target=face_detection_thread, daemon=True)
face_thread.start()

# 创建游戏窗口
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("智能雷电")


# 碰撞检测函数
def get_center_and_radius(rect, radius):
    if isinstance(rect, (tuple, list)):
        x, y, w, h = rect
        center = (x + w / 2, y + h / 2)
        r = radius if radius is not None else min(w, h) / 2
    else:
        center = (rect.x + rect.width / 2, rect.y + rect.height / 2)
        r = radius if radius is not None else min(rect.width, rect.height) / 2
    return center, r


def check_collision(rect1, rect2, radius1=None, radius2=None):
    center1, r1 = get_center_and_radius(rect1, radius1)
    center2, r2 = get_center_and_radius(rect2, radius2)

    dx = center1[0] - center2[0]
    dy = center1[1] - center2[1]
    distance_squared = dx * dx + dy * dy
    radius_sum = r1 + r2
    return distance_squared <= radius_sum * radius_sum


# 显示游戏结束界面
def show_game_over(score, high_score):
    screen.fill(COLORS["BLACK"])

    if score > high_score:
        high_score = score
        save_high_score(score)

    title = myFont.render("游戏结束", True, COLORS["RED"])
    score_text = score_font.render(f"最终得分: {int(score)}", True, COLORS["WHITE"])
    high_score_text = score_font.render(f"最高分: {high_score}", True, COLORS["WHITE"])
    restart_text = info_font.render("按空格键或鼠标左键重新开始", True, COLORS["WHITE"])

    screen.blit(title, (GAME_WIDTH // 2 - title.get_width() // 2, GAME_HEIGHT // 2 - 150))
    screen.blit(score_text, (GAME_WIDTH // 2 - score_text.get_width() // 2, GAME_HEIGHT // 2 - 50))
    screen.blit(high_score_text, (GAME_WIDTH // 2 - high_score_text.get_width() // 2, GAME_HEIGHT // 2 + 50))
    screen.blit(restart_text, (GAME_WIDTH // 2 - restart_text.get_width() // 2, GAME_HEIGHT // 2 + 150))

    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_SPACE:
                    return "restart"
                elif event.key == K_ESCAPE:
                    return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    return "restart"
            elif event.type == pygame.QUIT:
                return "quit"
        pygame.time.wait(10)
    return "quit"


# 显示开始界面
def show_start_screen():
    screen.blit(bg0, (0, 0))
    high_score = load_high_score()

    title = myFont.render("智能雷电", True, COLORS["RED"])
    high_score_text = score_font.render(f"最高分: {high_score}", True, COLORS["WHITE"])
    instructions = [
        info_font.render("游戏说明：WASD或上下左右控制方向", True, COLORS["BLACK"]),
        info_font.render("空格键或左键发射导弹", True, COLORS["BLACK"]),
        info_font.render("按M键使用鼠标控制开始游戏", True, COLORS["BLACK"]),
        info_font.render("按K键使用键盘控制开始游戏", True, COLORS["BLACK"]),
        info_font.render("按F键使用人脸控制开始游戏", True, COLORS["BLACK"]),
    ]

    screen.blit(title, (166, 100))
    screen.blit(high_score_text, (GAME_WIDTH // 2 - high_score_text.get_width() // 2, 200))
    for i, inst in enumerate(instructions):
        screen.blit(inst, (50, 350 + i * 40))
    screen.blit(start, (187, 540))

    running = True
    selected_control = -1
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_m:
                    selected_control = 0  # 鼠标控制
                    running = False
                elif event.key == K_k:
                    selected_control = 1  # 键盘控制
                    running = False
                elif event.key == K_f:
                    selected_control = 2  # 人脸控制
                    running = False
                elif event.key == K_ESCAPE:
                    return -1
            elif event.type == pygame.QUIT:
                return -1
        pygame.display.update()

    return selected_control


# 初始化游戏变量
def init_game_variables(control_type):
    clock = pygame.time.Clock()

    game_vars = {
        'normal_enemy_killed': 0,
        'boss1_killed': 0,
        'boss2_killed': 0,
        'speed_multiplier': 1.0,
        'boss_escape_timer': 0,
        'score': 0,

        'current_boss': None,
        'boss_active': False,
        'enemy_active': False,
        'game_over': False,

        'plane_w': 100, 'plane_h': 148,
        'plane_x': float((GAME_WIDTH - 100) / 2),
        'plane_y': float(GAME_HEIGHT - 148 - 20),
        'max_speed': 8.0,
        'acceleration': 1.0,
        'deceleration': 0.8,
        'move_speed': 0.0,

        'enemy_w': 128, 'enemy_h': 128,
        'enemy_x': 0, 'enemy_y': 0,
        'enemy_img': None,
        'enemy_speed': 2.0,
        'enemy_spawn_time': 0,
        'enemy_alive_time': 0,

        'bullet_img': pygame.image.load("alien_bullet.png"),
        'bullet_w': 44, 'bullet_h': 48,
        'bullet_x': 0, 'bullet_y': 0,
        'bullet_speed': 5.0,
        'bullet_active': False,
        'last_bullet_time': 0,
        'bullet_cooldown': 2,
        'bullet_delay': random.uniform(0.5, 1.5),
        'can_shoot': False,

        'missile_img': pygame.image.load("feidan.png"),
        'missile_w': 21, 'missile_h': 59,
        'missile_x': 0, 'missile_y': -59,
        'missile_speed': 10.0,
        'missile_active': False,

        'boss_1_w': 270, 'boss_1_h': 175,
        'boss_2_w': 577 // 2, 'boss_2_h': 374 // 2,
        'boss_x': 0, 'boss_y': 0,
        'boss_speed': 1.0,
        'boss_health': 100,
        'boss_max_health': 100,

        'control_type': control_type,
        'crosshair': create_crosshair(),

        'combo_window': 0.5,
        'hit_times': [],
        'combo_count': 0,
        'last_combo_score_time': 0,

        'clock': clock,
        'current_time': 0,
        'show_camera': control_type == 2,
    }

    game_vars['enemy_x'] = random.randint(0, GAME_WIDTH - game_vars['enemy_w'])
    game_vars['enemy_y'] = -game_vars['enemy_h']
    game_vars['enemy_img'] = enemy_images[random.randint(0, 4)]

    return clock, game_vars


# 创建鼠标准星
def create_crosshair():
    crosshair = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(crosshair, (255, 255, 255, 180), (16, 16), 16)
    pygame.draw.circle(crosshair, (0, 0, 0, 180), (16, 16), 3)
    pygame.draw.line(crosshair, (0, 0, 0, 180), (16, 0), (16, 8))
    pygame.draw.line(crosshair, (0, 0, 0, 180), (16, 24), (16, 32))
    pygame.draw.line(crosshair, (0, 0, 0, 180), (0, 16), (8, 16))
    pygame.draw.line(crosshair, (0, 0, 0, 180), (24, 16), (32, 16))
    return crosshair


# 处理游戏事件
def handle_events(game_vars):
    running = True
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_SPACE and not game_vars['missile_active']:
                game_vars['missile_x'] = game_vars['plane_x'] + (game_vars['plane_w'] - game_vars['missile_w']) / 2
                game_vars['missile_y'] = game_vars['plane_y'] - game_vars['missile_h']
                game_vars['missile_active'] = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not game_vars['missile_active']:
                game_vars['missile_x'] = game_vars['plane_x'] + (game_vars['plane_w'] - game_vars['missile_w']) / 2
                game_vars['missile_y'] = game_vars['plane_y'] - game_vars['missile_h']
                game_vars['missile_active'] = True

        elif event.type == pygame.QUIT:
            running = False
    return running


# 更新游戏状态
def update_game_state(game_vars):
    game_vars['current_time'] = time.time()

    if game_vars['enemy_active']:
        game_vars['enemy_alive_time'] = game_vars['current_time'] - game_vars['enemy_spawn_time']

    update_combo_system(game_vars)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    update_player_position(game_vars, mouse_x, mouse_y)
    spawn_enemies(game_vars)
    update_enemies_and_bullets(game_vars)
    update_boss_logic(game_vars)

    if game_vars['missile_active']:
        game_vars['missile_y'] -= game_vars['missile_speed'] * game_vars['speed_multiplier']
        if game_vars['missile_y'] < -game_vars['missile_h']:
            game_vars['missile_active'] = False


# 更新连击系统
def update_combo_system(game_vars):
    while game_vars['hit_times'] and game_vars['current_time'] - game_vars['hit_times'][0] > game_vars['combo_window']:
        game_vars['hit_times'].pop(0)

    if len(game_vars['hit_times']) >= 2:
        if game_vars['hit_times'][-1] - game_vars['hit_times'][-2] <= game_vars['combo_window']:
            if game_vars['current_time'] - game_vars['last_combo_score_time'] > game_vars['combo_window']:
                game_vars['score'] += 1
                game_vars['combo_count'] += 1
                game_vars['last_combo_score_time'] = game_vars['current_time']
                print(f"连击成功! 当前分数: {int(game_vars['score'])} (连击数: {game_vars['combo_count']})")


# 更新玩家位置（修改人脸控制部分）
def update_player_position(game_vars, mouse_x, mouse_y):
    if game_vars['control_type'] == 0:  # 鼠标控制
        target_x = mouse_x - game_vars['plane_w'] / 2
        target_y = mouse_y - game_vars['plane_h'] / 2
        game_vars['plane_x'] = max(0, min(target_x, GAME_WIDTH - game_vars['plane_w']))
        game_vars['plane_y'] = max(0, min(target_y, GAME_HEIGHT - game_vars['plane_h']))

    elif game_vars['control_type'] == 1:  # 键盘控制
        keys = pygame.key.get_pressed()
        moving_left = keys[K_a] or keys[K_LEFT]
        moving_right = keys[K_d] or keys[K_RIGHT]
        moving_up = keys[K_w] or keys[K_UP]
        moving_down = keys[K_s] or keys[K_DOWN]

        current_max_speed = game_vars['max_speed'] * game_vars['speed_multiplier']
        current_acceleration = game_vars['acceleration'] * game_vars['speed_multiplier']
        current_deceleration = game_vars['deceleration'] * game_vars['speed_multiplier']

        if moving_left and not moving_right:
            game_vars['move_speed'] = max(game_vars['move_speed'] - current_acceleration, -current_max_speed)
        elif moving_right and not moving_left:
            game_vars['move_speed'] = min(game_vars['move_speed'] + current_acceleration, current_max_speed)
        else:
            if game_vars['move_speed'] > 0:
                game_vars['move_speed'] = max(game_vars['move_speed'] - current_deceleration, 0)
            elif game_vars['move_speed'] < 0:
                game_vars['move_speed'] = min(game_vars['move_speed'] + current_deceleration, 0)

        game_vars['plane_x'] += game_vars['move_speed']
        game_vars['plane_x'] = max(0, min(game_vars['plane_x'], GAME_WIDTH - game_vars['plane_w']))

        if moving_up and not moving_down:
            game_vars['plane_y'] = max(game_vars['plane_y'] - current_max_speed * 0.7, 0)
        elif moving_down and not moving_up:
            game_vars['plane_y'] = min(game_vars['plane_y'] + current_max_speed * 0.7,
                                       GAME_HEIGHT - game_vars['plane_h'])

    elif game_vars['control_type'] == 2:  # 人脸控制
        if current_face_pos and face_positions:
            # 使用最近5个位置的平均值来平滑移动
            avg_x = sum(pos[0] for pos in face_positions) // len(face_positions)
            avg_y = sum(pos[1] for pos in face_positions) // len(face_positions)

            # 将飞机的中心点对准人脸中心点
            target_x = avg_x - game_vars['plane_w'] / 2
            target_y = avg_y - game_vars['plane_h'] / 2
            target_x = max(0, min(target_x, GAME_WIDTH - game_vars['plane_w']))
            target_y = max(0, min(target_y, GAME_HEIGHT - game_vars['plane_h']))

            # 平滑移动到目标位置
            game_vars['plane_x'] += (target_x - game_vars['plane_x']) * 0.2
            game_vars['plane_y'] += (target_y - game_vars['plane_y']) * 0.2
            game_vars['plane_x'] = max(0, min(game_vars['plane_x'], GAME_WIDTH - game_vars['plane_w']))
            game_vars['plane_y'] = max(0, min(game_vars['plane_y'], GAME_HEIGHT - game_vars['plane_h']))


# 生成敌人逻辑
def spawn_enemies(game_vars):
    if not game_vars['enemy_active'] and not game_vars['boss_active']:
        if game_vars['normal_enemy_killed'] >= NORMAL_TO_BOSS1 and game_vars['boss1_killed'] < BOSS1_TO_BOSS2:
            if game_vars['current_boss'] != 1:
                game_vars['current_boss'] = 1
                game_vars['boss_active'] = True
                game_vars['boss_x'] = (GAME_WIDTH - game_vars['boss_1_w']) // 2
                game_vars['boss_y'] = -game_vars['boss_1_h']
                game_vars['boss_health'] = 100
                game_vars['boss_max_health'] = game_vars['boss_health']
                print(f"Boss1生成！进度: {game_vars['boss1_killed']}/{BOSS1_TO_BOSS2}")
        elif game_vars['boss1_killed'] >= BOSS1_TO_BOSS2:
            if game_vars['current_boss'] != 2:
                game_vars['current_boss'] = 2
                game_vars['boss_active'] = True
                game_vars['boss_x'] = (GAME_WIDTH - game_vars['boss_2_w']) // 2
                game_vars['boss_y'] = -game_vars['boss_2_h']
                game_vars['boss_health'] = 200
                game_vars['boss_max_health'] = game_vars['boss_health']
                print(f"Boss2生成！击落后将提升速度")
        else:
            game_vars['enemy_active'] = True
            game_vars['enemy_x'] = random.randint(0, GAME_WIDTH - game_vars['enemy_w'])
            game_vars['enemy_y'] = -game_vars['enemy_h']
            game_vars['enemy_img'] = enemy_images[random.randint(0, 4)]
            game_vars['enemy_spawn_time'] = game_vars['current_time']
            game_vars['can_shoot'] = False
            game_vars['bullet_delay'] = random.uniform(0.5, 1.5)
            print(f"普通敌机生成！还需{NORMAL_TO_BOSS1 - game_vars['normal_enemy_killed']}架到Boss1")


# 更新敌机和子弹位置
def update_enemies_and_bullets(game_vars):
    if game_vars['enemy_active']:
        game_vars['enemy_y'] += game_vars['enemy_speed'] * game_vars['speed_multiplier']

        if game_vars['enemy_y'] > GAME_HEIGHT:
            game_vars['score'] -= 1
            print(f"普通敌机逃脱！当前分数: {int(game_vars['score'])}")
            game_vars['enemy_active'] = False

        if not game_vars['can_shoot'] and game_vars['enemy_alive_time'] >= game_vars['bullet_delay']:
            game_vars['can_shoot'] = True

        if game_vars['bullet_active']:
            game_vars['bullet_y'] += game_vars['bullet_speed'] * game_vars['speed_multiplier']
            if game_vars['bullet_y'] > GAME_HEIGHT:
                game_vars['bullet_active'] = False

        if (game_vars['can_shoot'] and not game_vars['bullet_active'] and
                (game_vars['current_time'] - game_vars['last_bullet_time']) >= game_vars['bullet_cooldown']):
            if random.random() < 0.7:
                game_vars['bullet_x'] = game_vars['enemy_x'] + game_vars['enemy_w'] / 2 - game_vars['bullet_w'] / 2
                game_vars['bullet_y'] = game_vars['enemy_y'] + game_vars['enemy_h']
                game_vars['bullet_active'] = True
                game_vars['last_bullet_time'] = game_vars['current_time']


# 更新Boss逻辑
def update_boss_logic(game_vars):
    if game_vars['boss_active']:
        game_vars['boss_y'] += game_vars['boss_speed'] * game_vars['speed_multiplier']

        if game_vars['boss_y'] > 100:
            game_vars['boss_y'] = 100
            game_vars['boss_escape_timer'] += 1 / FPS

            if game_vars['boss_escape_timer'] > 5:
                escaping_boss_type = game_vars['current_boss']
                game_vars['boss_active'] = False
                game_vars['boss_escape_timer'] = 0
                game_vars['current_boss'] = None
                game_vars['bullet_active'] = False
                game_vars['can_shoot'] = False

                if escaping_boss_type == 1:
                    game_vars['score'] -= 10
                    print("Boss1逃跑！分数-10")
                elif escaping_boss_type == 2:
                    game_vars['score'] -= 20
                    print("Boss2逃跑！分数-20")

                game_vars['normal_enemy_killed'] = 0
                if escaping_boss_type == 2:
                    game_vars['boss1_killed'] = 0

        if game_vars['bullet_active']:
            game_vars['bullet_y'] += game_vars['bullet_speed'] * game_vars['speed_multiplier']
            if game_vars['bullet_y'] > GAME_HEIGHT:
                game_vars['bullet_active'] = False
                game_vars['can_shoot'] = False

        if game_vars['boss_health'] <= 0:
            if game_vars['current_boss'] == 1:
                game_vars['boss1_killed'] += 1
                game_vars['normal_enemy_killed'] = 0
                print(f"Boss1被击落！进度: {game_vars['boss1_killed']}/{BOSS1_TO_BOSS2}")
            elif game_vars['current_boss'] == 2:
                game_vars['boss2_killed'] += 1
                game_vars['speed_multiplier'] *= 1.5
                game_vars['normal_enemy_killed'] = 0
                game_vars['boss1_killed'] = 0
                print(f"Boss2被击落！速度提升至{game_vars['speed_multiplier']:.1f}x")

            game_vars['boss_active'] = False
            game_vars['current_boss'] = None
            game_vars['boss_escape_timer'] = 0
            game_vars['bullet_active'] = False
            game_vars['can_shoot'] = False


# 碰撞检测
def check_collisions(game_vars):
    player_rect = pygame.Rect(int(game_vars['plane_x']), int(game_vars['plane_y']),
                              game_vars['plane_w'], game_vars['plane_h'])

    missile_rect = pygame.Rect(int(game_vars['missile_x']), int(game_vars['missile_y']),
                               game_vars['missile_w'], game_vars['missile_h']) if game_vars['missile_active'] else None

    bullet_rect = pygame.Rect(game_vars['bullet_x'], game_vars['bullet_y'],
                              game_vars['bullet_w'], game_vars['bullet_h']) if game_vars['bullet_active'] else None

    missile_hit = False

    # Boss碰撞检测
    if game_vars['boss_active']:
        boss_rect = pygame.Rect(
            game_vars['boss_x'], game_vars['boss_y'],
            game_vars['boss_1_w'] if game_vars['current_boss'] == 1 else game_vars['boss_2_w'],
            game_vars['boss_1_h'] if game_vars['current_boss'] == 1 else game_vars['boss_2_h']
        )
        boss_radius = min(game_vars['boss_1_w'], game_vars['boss_1_h']) / 2 if game_vars['current_boss'] == 1 else min(
            game_vars['boss_2_w'], game_vars['boss_2_h']) / 2

        if check_collision(player_rect, boss_rect, radius2=boss_radius):
            print("玩家与Boss碰撞！游戏结束")
            game_vars['game_over'] = True

    # 普通敌机碰撞检测
    if game_vars['enemy_active']:
        enemy_rect = pygame.Rect(game_vars['enemy_x'], game_vars['enemy_y'],
                                 game_vars['enemy_w'], game_vars['enemy_h'])

        if game_vars['missile_active'] and missile_rect:
            if check_collision(missile_rect, enemy_rect, radius2=min(game_vars['enemy_w'], game_vars['enemy_h']) / 2):
                game_vars['score'] += 2
                game_vars['normal_enemy_killed'] += 1
                game_vars['enemy_active'] = False
                missile_hit = True
                game_vars['hit_times'].append(game_vars['current_time'])
                print(f"普通敌机被击落！进度: {game_vars['normal_enemy_killed']}/{NORMAL_TO_BOSS1}")

        if check_collision(enemy_rect, player_rect, radius2=min(game_vars['enemy_w'], game_vars['enemy_h']) / 2):
            print("玩家与敌机碰撞！游戏结束")
            game_vars['game_over'] = True

    # Boss导弹碰撞检测
    if game_vars['boss_active'] and game_vars['missile_active'] and missile_rect:
        boss_rect = pygame.Rect(
            game_vars['boss_x'], game_vars['boss_y'],
            game_vars['boss_1_w'] if game_vars['current_boss'] == 1 else game_vars['boss_2_w'],
            game_vars['boss_1_h'] if game_vars['current_boss'] == 1 else game_vars['boss_2_h']
        )
        boss_radius = min(game_vars['boss_1_w'], game_vars['boss_1_h']) / 2 if game_vars['current_boss'] == 1 else min(
            game_vars['boss_2_w'], game_vars['boss_2_h']) / 2

        if check_collision(missile_rect, boss_rect, radius2=boss_radius):
            damage = random.randint(10, 20)
            game_vars['boss_health'] -= damage
            game_vars['score'] += 2
            print(f"导弹击中Boss{game_vars['current_boss']}！伤害:{damage} 剩余血量:{game_vars['boss_health']} 得分+2")
            missile_hit = True

    # 子弹碰撞检测
    if game_vars['missile_active'] and missile_rect and bullet_rect:
        if check_collision(missile_rect, bullet_rect, radius2=min(game_vars['bullet_w'], game_vars['bullet_h']) / 2):
            game_vars['score'] += 1
            game_vars['bullet_active'] = False
            missile_hit = True
            game_vars['hit_times'].append(game_vars['current_time'])
            print(f"击中敌机子弹！当前分数: {int(game_vars['score'])}")

    if missile_hit and game_vars['missile_active']:
        game_vars['missile_active'] = False

    # 玩家被子弹击中检测
    if game_vars['bullet_active'] and bullet_rect:
        if check_collision(bullet_rect, player_rect, radius1=min(game_vars['bullet_w'], game_vars['bullet_h']) / 2):
            print("玩家被敌机子弹击中！游戏结束")
            game_vars['game_over'] = True

    # 分数检查
    if game_vars['score'] < 0:
        print("分数已耗尽，游戏结束")
        game_vars['game_over'] = True
        game_vars['score'] = 0


# 渲染游戏画面
def render_frame(game_vars):
    screen.blit(bg1, (0, 0))
    screen.blit(plane, (int(game_vars['plane_x']), int(game_vars['plane_y'])))

    if game_vars['enemy_active']:
        screen.blit(game_vars['enemy_img'], (game_vars['enemy_x'], game_vars['enemy_y']))

    if game_vars['bullet_active']:
        screen.blit(game_vars['bullet_img'], (game_vars['bullet_x'], game_vars['bullet_y']))

    if game_vars['missile_active']:
        screen.blit(game_vars['missile_img'], (int(game_vars['missile_x']), int(game_vars['missile_y'])))

    if game_vars['boss_active']:
        screen.blit(boss_1_img if game_vars['current_boss'] == 1 else boss_2_img,
                    (game_vars['boss_x'], game_vars['boss_y']))
        health_width = int((game_vars['boss_health'] / game_vars['boss_max_health']) *
                           (200 if game_vars['current_boss'] == 1 else 300))
        pygame.draw.rect(screen, COLORS["RED"], (game_vars['boss_x'], game_vars['boss_y'] - 10, health_width, 5))

    # 显示连击信息
    if game_vars['combo_count'] > 0:
        combo_text = info_font.render(f"连击: {game_vars['combo_count']}", True, (255, 215, 0))
        screen.blit(combo_text, (10, 50))

    # 显示准星
    if game_vars['control_type'] == 0:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        screen.blit(game_vars['crosshair'], (mouse_x - 16, mouse_y - 16))

    # 显示分数和控制方式
    score_text = score_font.render(f"分数: {int(game_vars['score'])}", True, COLORS["WHITE"])
    screen.blit(score_text, (10, 10))

    control_texts = {
        0: "鼠标控制",
        1: "键盘控制",
        2: "人脸控制"
    }
    control_text = info_font.render(control_texts[game_vars['control_type']], True, COLORS["YELLOW"])
    screen.blit(control_text, (GAME_WIDTH - control_text.get_width() - 10, 10))

    pygame.display.update()


# 处理游戏结束
def handle_game_over(game_vars):
    final_score = max(0, game_vars['score'])
    high_score = load_high_score()

    if final_score <= 0:
        print("游戏结束，最终得分为0")

    return show_game_over(final_score, high_score)


# 游戏主循环
def run_game(control_type):
    clock, game_vars = init_game_variables(control_type)

    running = True
    while running and not game_vars['game_over']:
        running = handle_events(game_vars)
        update_game_state(game_vars)
        check_collisions(game_vars)
        render_frame(game_vars)
        clock.tick(FPS)

    if game_vars['game_over']:
        return handle_game_over(game_vars)
    return "quit"


# 在程序退出时清理资源
def cleanup():
    global face_detection_running
    face_detection_running = False
    if 'face_thread' in globals() and face_thread.is_alive():
        face_thread.join()
    if 'cap' in globals() and cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    pygame.quit()