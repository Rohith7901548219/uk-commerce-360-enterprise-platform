import sys

from commerce.cli import main

if __name__ == "__main__":
    sys.argv.insert(1, "pipeline")
    main()
