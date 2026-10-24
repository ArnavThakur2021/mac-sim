"""Run the project experiment suite; use --fast for a short demonstration."""
from run_all import run
if __name__ == '__main__':
 import sys
 run('--fast' in sys.argv)
