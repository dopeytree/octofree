"""
Script to analyze and fix octopus ASCII art spacing for perfect alignment.
Each line should be exactly 37 characters to fit within the box borders.
"""

def analyze_frames():
    """Analyze current frames and show their lengths."""
    frames = [
        # Frame 0 - neutral
        [
            "          ,'\"\"`.                     ",
            "         / _  _ \\                    ",
            "         |(@)(@)|                    ",
            "         )  __  (                    ",
            "        /,')))((`.\\.                   ",
            "       (( ((  )) ))                  ",
            "        `\\ `)(' /'                    ",
        ],
        # Frame 1 - tentacles wave
        [
            "          ,'\"\"`.                     ",
            "         / _  _ \\                    ",
            "         |(@)(@)|                    ",
            "         )  __  (                    ",
            "        /,')))((`.\\.                   ",
            "      ((  ((  ))  ))                 ",
            "       `\\ `)(' /'                     ",
        ],
        # Frame 2 - tentacles spread
        [
            "          ,'\"\"`.                     ",
            "         / _  _ \\                    ",
            "         |(@)(@)|                    ",
            "         )  __  (                    ",
            "        /,')))((`.\\.                   ",
            "     ((   ((  ))   ))                ",
            "      `\\ `)(' /'                      ",
        ],
        # Frame 3 - tentacles wave other direction
        [
            "          ,'\"\"`.                     ",
            "         / _  _ \\                    ",
            "         |(@)(@)|                    ",
            "         )  __  (                    ",
            "        /,')))((`.\\.                   ",
            "       ((  ((  ))  ))                ",
            "        `\\ `)(' /'                    ",
        ],
    ]
    
    print("Current frame analysis:")
    print("=" * 60)
    
    for frame_num, frame in enumerate(frames):
        print(f"\nFrame {frame_num}:")
        for line_num, line in enumerate(frame):
            length = len(line)
            print(f"  Line {line_num}: length={length:2d} |{line}|")
            if length != 37:
                print(f"    ⚠️  Should be 37, but is {length} (diff: {length - 37:+d})")
    
    print("\n" + "=" * 60)
    print("\nGenerating fixed frames...")
    print("=" * 60)
    
    # Generate fixed frames
    fixed_frames = []
    for frame_num, frame in enumerate(frames):
        fixed_frame = []
        print(f"\nFrame {frame_num}:")
        for line in frame:
            # Strip trailing whitespace and pad to exactly 37 characters
            fixed_line = line.rstrip().ljust(37)
            fixed_frame.append(fixed_line)
            print(f'            "{fixed_line}",')
        fixed_frames.append(fixed_frame)
    
    return fixed_frames


def generate_code():
    """Generate the corrected Python code for the frames."""
    fixed_frames = analyze_frames()
    
    print("\n" + "=" * 60)
    print("CORRECTED CODE TO PASTE:")
    print("=" * 60)
    print("""
def get_octopus_frame(frame_num):
    \"\"\"
    Get an octopus animation frame with animated tentacles.
    
    Args:
        frame_num: Frame number (0-3) for animation cycle
    
    Returns:
        List of strings representing the octopus art
    \"\"\"
    frames = [
        # Frame 0 - neutral
        [""")
    
    for frame_num, frame in enumerate(fixed_frames):
        if frame_num > 0:
            print(f"        ],")
            print(f"        # Frame {frame_num} - ", end="")
            if frame_num == 1:
                print("tentacles wave")
            elif frame_num == 2:
                print("tentacles spread")
            elif frame_num == 3:
                print("tentacles wave other direction")
            print("        [")
        
        for line in frame:
            print(f'            "{line}",')
    
    print("""        ],
    ]
    return frames[frame_num % len(frames)]
""")


if __name__ == "__main__":
    generate_code()
