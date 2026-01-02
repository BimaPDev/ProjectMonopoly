
import sys
print(f"Python path: {sys.path}")
try:
    import playwright_stealth
    print(f"Successfully imported playwright_stealth: {playwright_stealth}")
    print(f"Dir: {dir(playwright_stealth)}")
except ImportError as e:
    print(f"Failed to import playwright_stealth: {e}")
