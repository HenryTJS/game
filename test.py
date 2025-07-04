from functions_all import show_start_screen, run_game

if __name__ == '__main__':
    while True:
        # 显示开始界面，获取用户选择的控制方式
        mouse_control = show_start_screen()
        if mouse_control is not None:
            # 启动游戏主循环
            run_game(mouse_control)