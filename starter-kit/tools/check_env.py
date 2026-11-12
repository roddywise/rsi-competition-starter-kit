import sys


def main():
    if not ((3, 10) <= sys.version_info[:2] <= (3, 12)):
        print(f"Python {sys.version.split()[0]} detected; contest package expects Python 3.10-3.12.")
        return 1
    try:
        import numpy
    except ImportError:
        print("NumPy is missing. Run: python -m pip install -r baselines/requirements.txt")
        return 1
    print(f"Python: {sys.version.split()[0]}")
    print(f"NumPy: {numpy.__version__}")
    if numpy.__version__ != "1.26.4":
        print("Wrong NumPy version. The official package pins numpy==1.26.4.")
        return 1
    print("Environment matches the official package requirement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
