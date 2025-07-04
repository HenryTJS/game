import pygame

# 游戏窗口尺寸
WIDTH, HEIGHT = 512, 768
pygame.init()

# ====================== 资源加载 ======================

# 背景图片
bg0 = pygame.image.load("start_bg0.jpg")
bg1 = pygame.image.load("map1.jpg")
start = pygame.image.load("start.png")

# 玩家飞机
plane = pygame.image.load("plane.png")

# BOSS图片
boss_1_img = pygame.image.load("boss_1.png")
boss_2_img = pygame.transform.scale(pygame.image.load("boss_2.png"), (577 // 2, 374 // 2))

# 敌人图片
enemy_images = [pygame.image.load(f"alien_{i}.png") for i in range(1, 6)]

# 字体
myFont = pygame.font.SysFont("simhei", 45)
info_font = pygame.font.SysFont("simhei", 25)
score_font = pygame.font.SysFont("simhei", 36)

# 颜色定义
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# 其它
FPS = 60  # 游戏帧率
NORMAL_TO_BOSS1 = 5  # 击落普通敌机数量达到该值生成Boss1
BOSS1_TO_BOSS2 = 5  # 击落Boss1数量达到该值生成Boss2