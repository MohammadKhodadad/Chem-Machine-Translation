from __future__ import annotations

import argparse
from pathlib import Path

from chem_machine_translation.translation.iate_index import build_local_iate_index

DEFAULT_INPUT = Path("data/iate/IATE_export.csv")
DEFAULT_OUTPUT = Path("data/iate/iate.sqlite")


def main() -> None:
    args = parse_args()
    inserted = build_local_iate_index(input_path=args.input, output_path=args.output)
    print(f"Wrote {inserted} IATE term rows to {args.output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    main()
