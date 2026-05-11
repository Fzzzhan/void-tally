#!/usr/bin/env python3
"""
ANSI-aware Character Counter
Counts only meaningful characters, excluding ANSI escape sequences
"""


def count_meaningful_chars(data: bytes) -> int:
    """
    Count non-whitespace, non-control characters, excluding ANSI escape sequences.

    ANSI escape sequences follow these patterns:
    - ESC [ ... m  (SGR - Select Graphic Rendition, e.g., colors)
    - ESC [ ... H  (CUP - Cursor Position)
    - ESC [ ... J  (ED - Erase Display)
    - ESC [ ... K  (EL - Erase Line)
    - ESC [ ... A/B/C/D  (CUU/CUD/CUF/CUB - Cursor movement)
    - ESC ] ... BEL  (OSC - Operating System Command)
    - ESC ] ... ESC \\  (OSC alternative terminator)

    Args:
        data: Raw bytes from PTY output

    Returns:
        Count of meaningful (non-ANSI, non-whitespace) characters
    """
    count = 0
    i = 0

    while i < len(data):
        byte = data[i]

        # Skip ANSI CSI sequences: ESC [ ... <terminator>
        if byte == 27 and i + 1 < len(data) and data[i + 1] == ord('['):
            # Found CSI sequence, skip until terminator
            i += 2  # Skip ESC [
            while i < len(data):
                byte = data[i]
                i += 1
                # CSI terminators: A-Z, a-z, @, `
                if (65 <= byte <= 90) or (97 <= byte <= 122) or byte == 64 or byte == 96:
                    break
            continue

        # Skip ANSI OSC sequences: ESC ] ... BEL or ESC ] ... ESC \
        if byte == 27 and i + 1 < len(data) and data[i + 1] == ord(']'):
            # Found OSC sequence
            i += 2  # Skip ESC ]
            while i < len(data):
                byte = data[i]
                i += 1
                # OSC terminators: BEL (0x07) or ESC \ (0x1B 0x5C)
                if byte == 7:  # BEL
                    break
                if byte == 27 and i < len(data) and data[i] == 0x5C:  # ESC \
                    i += 1
                    break
            continue

        # Skip other ESC sequences (simple ones like ESC c)
        if byte == 27:
            i += 1
            # Skip next char if it's a simple escape
            if i < len(data) and data[i] not in (ord('['), ord(']')):
                i += 1
            continue

        # Skip whitespace and control characters
        if byte in (ord(' '), ord('\t'), ord('\n'), ord('\r'), 0):
            i += 1
            continue

        # Skip other control characters (0x00-0x1F except those handled above)
        if byte < 32:
            i += 1
            continue

        # This is a meaningful character
        count += 1
        i += 1

    return count


def test_count_meaningful_chars():
    """Test cases for ANSI-aware character counting"""

    # Test 1: Plain text
    assert count_meaningful_chars(b"Hello") == 5
    assert count_meaningful_chars(b"Hello World") == 10  # Space doesn't count

    # Test 2: Text with ANSI color codes
    # ESC[31m = red color, ESC[0m = reset
    text_with_color = b"\x1b[31mHello\x1b[0m"
    assert count_meaningful_chars(text_with_color) == 5  # Only "Hello"

    # Test 3: Just ANSI codes (no real content)
    just_ansi = b"\x1b[2K\x1b[1G\x1b[?25h"  # Clear line, move cursor, show cursor
    assert count_meaningful_chars(just_ansi) == 0

    # Test 4: Complex ANSI with text
    complex_output = b"\x1b[2K\x1b[1G\x1b[?25hThinking...\x1b[2K"
    # "Thinking..." = 11 chars (T-h-i-n-k-i-n-g-.-.-.)
    assert count_meaningful_chars(complex_output) == 11

    # Test 5: OSC sequences (e.g., setting window title)
    osc_sequence = b"\x1b]0;My Title\x07"  # OSC 0 ; title ; BEL
    assert count_meaningful_chars(osc_sequence) == 0

    # Test 6: Mixed content
    mixed = b"AI: \x1b[32mYes\x1b[0m, I can help."
    # "AI:" = 3, "Yes" = 3, "Icanhelp" = 9 (commas/periods count, spaces don't)
    # Total: 3 + 3 + 1 + 1 + 8 = 16
    actual = count_meaningful_chars(mixed)
    assert actual == 16, f"Expected 16, got {actual}"

    # Test 7: Empty and whitespace
    assert count_meaningful_chars(b"") == 0
    assert count_meaningful_chars(b"   \n\t  ") == 0

    # Test 8: Control characters
    assert count_meaningful_chars(b"\x01\x02\x03") == 0  # Control chars

    print("✅ All tests passed!")


if __name__ == "__main__":
    test_count_meaningful_chars()
