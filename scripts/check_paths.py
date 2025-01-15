#!/usr/bin/env python3
import sys

def main():
    print("Python Path:")
    for path in sys.path:
        print(f"  {path}")

if __name__ == "__main__":
    main()
