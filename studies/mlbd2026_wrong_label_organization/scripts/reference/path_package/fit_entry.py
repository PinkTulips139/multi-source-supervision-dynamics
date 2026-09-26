"""Separate-process fit entry. Worker refuses execution without a later authority file."""
import argparse
from consequence_worker import execute


def main():
    parser = argparse.ArgumentParser()
    for name in ("package_root", "project_root", "seed", "order_id", "condition", "output", "authorization"):
        parser.add_argument(name)
    args = parser.parse_args()
    execute(args.package_root, args.project_root, int(args.seed), args.order_id,
            args.condition, args.output, args.authorization)


if __name__ == "__main__":
    main()
