"""
Check ALL lines inside the box for exact width of 39 characters
"""

def check_all_lines():
    """Verify every line between ║ borders is exactly 39 chars."""
    
    lines = [
        ("OCTOFREE title", "              OCTOFREE                 "),
        ("LOADING text", "             LOADING...                "),
        ("Empty line", "                                       "),
        ("Octopus line 1", "          ,'\"\"`.                     "),
        ("Octopus line 2", "         / _  _ \\                    "),
        ("Octopus line 3", "         |(@)(@)|                    "),
        ("Octopus line 4", "         )  __  (                    "),
        ("Octopus line 5", "        /,')))((`.\\.                 "),
        ("Octopus line 6", "       (( ((  )) ))                  "),
        ("Octopus line 7", "        `\\ `)(' /'                   "),
        ("Progress 0%", "      [░░░░░░░░░░░░░░░░░░░░]   0%      "),
        ("Progress 50%", "      [██████████░░░░░░░░░░]  50%      "),
        ("Progress 100%", "      [████████████████████] 100%      "),
    ]
    
    print("Line width verification:")
    print("=" * 70)
    print("All lines should be exactly 39 characters\n")
    
    all_good = True
    for name, line in lines:
        length = len(line)
        status = "✅" if length == 39 else "❌"
        print(f"{status} {name:20s}: {length:2d} chars |{line}|")
        if length != 39:
            diff = length - 39
            print(f"   {'TOO LONG' if diff > 0 else 'TOO SHORT'} by {abs(diff)} chars")
            all_good = False
    
    print("\n" + "=" * 70)
    if all_good:
        print("✅ ALL LINES ARE PERFECT!")
    else:
        print("❌ SOME LINES NEED ADJUSTMENT")
        print("\nLet me generate the corrected versions...\n")
        
        # Show corrections
        print("CORRECTED LINES:")
        print("-" * 70)
        for name, line in lines:
            if len(line) != 39:
                corrected = line.rstrip().ljust(39)
                print(f"{name}:")
                print(f'  OLD ({len(line):2d}): "{line}"')
                print(f'  NEW ({len(corrected):2d}): "{corrected}"')
                print()


if __name__ == "__main__":
    check_all_lines()
