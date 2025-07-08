import pygame

# 游戏窗口尺寸
WIDTH, HEIGHT = 512, 768
pygame.init()

# 资源文件路径
IMAGE_PATHS = {
    "bg0": "start_bg0.jpg",
    "bg1": "map1.jpg",
    "start": "start.png",
    "plane": "plane.png",
    "boss_1": "boss_1.png",
    "boss_2": "boss_2.png",
    "bullet": "alien_bullet.png",
    "missile": "feidan.png",
    "enemies": [f"alien_{i}.png" for i in range(1, 6)]
}

# 加载图片资源
def load_image(path):
    return pygame.image.load(path)

# 背景图片
bg0 = load_image(IMAGE_PATHS["bg0"])
bg1 = load_image(IMAGE_PATHS["bg1"])
start = load_image(IMAGE_PATHS["start"])

# 玩家飞机
plane = load_image(IMAGE_PATHS["plane"])

# BOSS图片
boss_1_img = load_image(IMAGE_PATHS["boss_1"])
boss_2_img = pygame.transform.scale(load_image(IMAGE_PATHS["boss_2"]), (577 // 2, 374 // 2))

# 敌人图片
enemy_images = [load_image(path) for path in IMAGE_PATHS["enemies"]]

# 字体
FONT_SIZES = {
    "large": 45,
    "medium": 36,
    "small": 25
}
myFont = pygame.font.SysFont("simhei", FONT_SIZES["large"])
info_font = pygame.font.SysFont("simhei", FONT_SIZES["small"])
score_font = pygame.font.SysFont("simhei", FONT_SIZES["medium"])

# 颜色定义
COLORS = {
    "RED": (255, 0, 0),
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "YELLOW": (255, 255, 0)
}

# 其它
FPS = 60
NORMAL_TO_BOSS1 = 5
BOSS1_TO_BOSS2 = 5