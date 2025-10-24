"""
Better test - count actual visible characters without ANSI codes
"""

def test_visible_width():
    """Test the actual visible character count."""
    
    # The content between the ║ borders should be exactly 39 visible chars
    # Format breakdown (visible chars only):
    # "      [{bar}] {progress:3d}%        "
    #  123456 1 20chars 1 1 space 4chars padding
    
    test_cases = [
        (0, "      [░░░░░░░░░░░░░░░░░░░░]   0%"),
        (5, "      [█░░░░░░░░░░░░░░░░░░░]   5%"),
        (20, "      [████░░░░░░░░░░░░░░░░]  20%"),
        (80, "      [████████████████░░░░]  80%"),
        (100, "      [████████████████████] 100%"),
    ]
    
    print("Visible character width analysis:")
    print("=" * 60)
    
    for progress, test_string in test_cases:
        # Count components
        prefix = "      "  # 6 spaces
        bracket_open = "["  # 1
        bar_section = test_string[7:27]  # 20 chars
        bracket_close = "]"  # 1
        space = " "  # 1
        percentage = f"{progress:3d}%"  # 4 chars total
        
        # Calculate needed padding
        used = len(prefix) + 1 + 20 + 1 + 1 + 4  # = 33
        needed_padding = 39 - used  # = 6
        
        full_string = f"{prefix}[{bar_section}] {percentage}" + " " * needed_padding
        
        print(f"\nProgress {progress:3d}%:")
        print(f"  String: |{full_string}|")
        print(f"  Length: {len(full_string)} (should be 39)")
        print(f"  Breakdown: 6 + 1 + 20 + 1 + 1 + 4 + {needed_padding} = {len(full_string)}")
        
        if len(full_string) == 39:
            print(f"  ✅ PERFECT")
        else:
            print(f"  ❌ WRONG by {len(full_string) - 39}")
    
    print("\n" + "=" * 60)
    print("\nCORRECT FORMAT:")
    print('f"      [{bar}] {progress:3d}%      "  # 6 trailing spaces')
    print("Total: 6 + 1 + 20 + 1 + 1 + 4 + 6 = 39 chars")


if __name__ == "__main__":
    test_visible_width()
