"""
Loading screen module for Octofree application.
Displays an animated ASCII art octopus with colors and movement during startup.
"""

import time
import sys
import random


# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_BLUE = '\033[44m'
    BG_CYAN = '\033[46m'


def clear_screen():
    """Clear the console screen."""
    print("\033[2J\033[H", end='')


def get_octopus_frame(frame_num):
    """
    Get an octopus animation frame with animated tentacles.
    
    Args:
        frame_num: Frame number (0-3) for animation cycle
    
    Returns:
        List of strings representing the octopus art
    """
    frames = [
        # Frame 0 - neutral
        [
            "          ,'\"\"`.                       ",
            "         / _  _ \\                      ",
            "         (@)(@)                       ",
            "         )  __  (                      ",
            "        /,')))((`.\\.                   ",
            "       (( ((  )) ))                    ",
            "        `\\ `)(' /'                     ",
        ],
        # Frame 1 - tentacles wave
        [
            "          ,'\"\"`.                       ",
            "         / _  _ \\                      ",
            "         (@)(@)                       ",
            "         )  __  (                      ",
            "        /,')))((`.\\.                   ",
            "      ((  ((  ))  ))                   ",
            "       `\\ `)(' /'                      ",
        ],
        # Frame 2 - tentacles spread
        [
            "          ,'\"\"`.                       ",
            "         / _  _ \\                      ",
            "         (@)(@)                       ",
            "         )  __  (                      ",
            "        /,')))((`.\\.                   ",
            "     ((   ((  ))   ))                  ",
            "      `\\ `)(' /'                       ",
        ],
        # Frame 3 - tentacles wave other direction
        [
            "          ,'\"\"`.                       ",
            "         / _  _ \\                      ",
            "         (@)(@)                       ",
            "         )  __  (                      ",
            "        /,')))((`.\\.                   ",
            "       ((  ((  ))  ))                  ",
            "        `\\ `)(' /'                     ",
        ],
    ]
    return frames[frame_num % len(frames)]


def get_loading_message(frame_num):
    """
    Get animated loading message.
    
    Args:
        frame_num: Frame number for animation
    
    Returns:
        String with animated loading text
    """
    messages = [
        "LOADING.  ",
        "LOADING.. ",
        "LOADING...",
        "LOADING.. ",
    ]
    return messages[frame_num % len(messages)]


def display_loading_screen(duration=4.0, steps=20):
    """
    Display an animated loading screen with colored ASCII art octopus.
    
    Args:
        duration: Total duration of the loading animation in seconds
        steps: Number of progress bar update steps
    """
    try:
        clear_screen()
        
        for i in range(steps + 1):
            progress = int((i / steps) * 100)
            filled = int((progress / 100) * 20)  # 20 character progress bar
            bar = '█' * filled + '░' * (20 - filled)
            
            # Get current animation frame
            frame = i % 4
            octopus_lines = get_octopus_frame(frame)
            loading_msg = get_loading_message(frame)
            
            # Color scheme based on progress
            if progress < 33:
                progress_color = Colors.BRIGHT_RED
            elif progress < 66:
                progress_color = Colors.BRIGHT_YELLOW
            else:
                progress_color = Colors.BRIGHT_GREEN
            
            # Move cursor to top
            print("\033[H", end='')
            
            # Display the loading screen with colors
            print(f"{Colors.CYAN}┌{'─'*99}{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}{' '*99}")
            print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}╔{'═'*77}{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}              {Colors.BOLD}{Colors.BRIGHT_MAGENTA}OCTOFREE{Colors.RESET}{' '*65}")
            print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}             {Colors.BRIGHT_WHITE}{loading_msg}{Colors.RESET}{' '*64}")
            print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}{' '*77}")
            
            # Octopus with colors
            for idx, line in enumerate(octopus_lines):
                if idx <= 2:  # Head with eyes
                    print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}{line}{Colors.RESET}{' '*35}")
                else:  # Body and tentacles
                    print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.MAGENTA}{line}{Colors.RESET}{' '*35}")
            
            print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}{' '*77}")
            print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BLACK}[{progress_color}{bar}{Colors.BLACK}]{Colors.RESET} {progress_color}{progress:3d}%{Colors.RESET}{' '*46}")
            print(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}╚{'═'*77}{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}{' '*99}")
            print(f"{Colors.CYAN}│{Colors.RESET}  {Colors.BRIGHT_YELLOW}Free Electricity Sessions{Colors.RESET} {Colors.BLACK}Powered by Octopus Energy{Colors.RESET}{' '*47}")
            print(f"{Colors.CYAN}└{'─'*99}{Colors.RESET}")
            
            sys.stdout.flush()
            
            if i < steps:
                time.sleep(duration / steps)
        
        # Hold final screen briefly
        time.sleep(0.5)
        clear_screen()
        
    except KeyboardInterrupt:
        clear_screen()
        raise


def display_static_banner():
    """
    Display a static banner (no animation) for environments where 
    cursor control might not work well (e.g., Docker logs).
    Uses logging instead of print to ensure it appears in log files.
    """
    import logging
    
    # Log each line of the banner
    logging.info(f"{Colors.CYAN}┌{'─'*99}{Colors.RESET}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}{' '*99}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}╔{'═'*77}{Colors.RESET}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}              {Colors.BOLD}{Colors.BRIGHT_MAGENTA}OCTOFREE{Colors.RESET}{' '*65}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}             {Colors.BRIGHT_WHITE}LOADING...{Colors.RESET}{' '*64}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}{' '*77}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}          ,'\"\"`.{Colors.RESET}{' '*62}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}         / _  _ \\{Colors.RESET}{' '*61}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}         |(@)(@)|{Colors.RESET}{' '*61}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.MAGENTA}         )  __  ({Colors.RESET}{' '*61}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.MAGENTA}        /,')))((`.\\{Colors.RESET}{' '*58}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.MAGENTA}       (( ((  )) )){Colors.RESET}{' '*60}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.MAGENTA}        `\\ `)(' /'{Colors.RESET}{' '*61}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}{' '*77}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}[████████████████████] 100%{Colors.RESET}{' '*46}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}                     {Colors.BRIGHT_CYAN}╚{'═'*77}{Colors.RESET}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}{' '*99}")
    logging.info(f"{Colors.CYAN}│{Colors.RESET}  {Colors.BRIGHT_YELLOW}Free Electricity Sessions{Colors.RESET} {Colors.BLACK}Powered by Octopus Energy{Colors.RESET}{' '*47}")
    logging.info(f"{Colors.CYAN}└{'─'*99}{Colors.RESET}")


if __name__ == "__main__":
    # Test the loading screen
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}Testing Animated Loading Screen...{Colors.RESET}\n")
    display_loading_screen(duration=4.0, steps=20)
    print(f"{Colors.BRIGHT_GREEN}✓ Loading complete!{Colors.RESET}\n")
