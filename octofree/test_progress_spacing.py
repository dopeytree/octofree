"""
Script to test and calculate the exact spacing for the progress bar line.
The inner box is 39 characters wide (between the ║ borders).
"""

def test_progress_line():
    """Test different progress values to ensure consistent width."""
    
    # 20 character progress bar
    test_values = [0, 5, 20, 50, 95, 100]
    
    print("Testing progress bar spacing:")
    print("=" * 70)
    print("\nInner box should be exactly 39 characters wide")
    print("Format: 6 spaces + '[' + 20 bar chars + ']' + ' ' + '###%' + padding")
    print("=" * 70)
    
    for progress in test_values:
        filled = int((progress / 100) * 20)
        bar = '█' * filled + '░' * (20 - filled)
        
        # Current format: 6 spaces + [bar] + space + progress% + padding
        # "      [████████████████████] 100%         "
        
        line_content = f"      [{bar}] {progress:3d}%         "
        
        print(f"\nProgress: {progress:3d}%")
        print(f"Content: |{line_content}|")
        print(f"Length: {len(line_content)} chars (should be 39)")
        
        if len(line_content) != 39:
            # Calculate needed adjustment
            diff = len(line_content) - 39
            if diff > 0:
                new_padding = 9 - diff  # Current padding is 9 spaces
                print(f"  ⚠️  TOO LONG by {diff} chars! Need padding of {new_padding} spaces")
            else:
                new_padding = 9 + abs(diff)
                print(f"  ⚠️  TOO SHORT by {abs(diff)} chars! Need padding of {new_padding} spaces")
        else:
            print(f"  ✅ CORRECT LENGTH")
    
    print("\n" + "=" * 70)
    print("\nRECOMMENDATION:")
    print("Since {progress:3d}% is 4 characters total (including the % sign),")
    print("the format should be:")
    print('      [{bar}] {progress:3d}%        ')
    print("       ^6    ^1+20+1 ^4       ^8 = 39 chars total")
    print("\nCorrected line:")
    print('print(f"...║      {BLACK}[{color}{bar}{BLACK}]{RESET} {color}{progress:3d}%{RESET}        ║...")')


if __name__ == "__main__":
    test_progress_line()
