
import sys
print(f"Python path: {sys.path}")
try:
    import playwright_stealth
    print(f"Successfully imported playwright_stealth: {playwright_stealth}")
    print(f"Dir: {dir(playwright_stealth)}")
    if hasattr(playwright_stealth, 'stealth'):
        print(f"Stealth object type: {type(playwright_stealth.stealth)}")
        print(f"Is callable? {callable(playwright_stealth.stealth)}")

except ImportError as e:
    print(f"Failed to import playwright_stealth: {e}")
