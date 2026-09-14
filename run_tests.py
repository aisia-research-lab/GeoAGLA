import sys
import unittest
from pathlib import Path

# Add src to sys.path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "src"))

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover all test files in tests/
    test_dir = root / "tests"
    for py_file in sorted(test_dir.glob("test_*.py")):
        module_name = py_file.stem
        # Load module
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Look for test functions or TestCase classes
        for name in dir(mod):
            if name.startswith("test_") and callable(getattr(mod, name)):
                fn = getattr(mod, name)
                # Wrap standalone function as a TestCase
                class StandaloneTest(unittest.TestCase):
                    pass
                test_case = StandaloneTest()
                setattr(test_case, name, fn)
                test_case._testMethodName = name
                suite.addTest(test_case)

    print(f"Running {suite.countTestCases()} tests from tests/ directory...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
