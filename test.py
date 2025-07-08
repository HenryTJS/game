from functions_all import show_start_screen, run_game, cleanup

def main():
    try:
        while True:
            control_type = show_start_screen()
            if control_type == -1:
                break

            result = run_game(control_type)
            if result == "quit":
                break
            elif result == "menu":
                continue

    finally:
        cleanup()


if __name__ == "__main__":
    main()