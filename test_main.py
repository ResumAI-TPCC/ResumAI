def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def test_add_positive_numbers():
    # Test case 1: Positive numbers
    assert add_numbers(1, 2) == 3

def test_add_negative_numbers():
    # Test case 2: Negative numbers
    assert add_numbers(-1, -1) == -2
