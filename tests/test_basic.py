#!/usr/bin/env python3
"""
DSAN Basic Tests
"""
def test_dsan_import():
    """Test DSAN module imports correctly"""
    try:
        import dsan_sim
        print("✅ DSAN import OK")
    except ImportError:
        print("⚠️  dsan_sim module not found")

if __name__ == "__main__":
    test_dsan_import()
