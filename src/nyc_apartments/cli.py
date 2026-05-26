from __future__ import annotations

from argparse import ArgumentParser
import sys

from nyc_apartments.pipeline import run_pipeline


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="nyc-apartments")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the listing pipeline")
    run.add_argument("--config", default="config/search.example.toml")
    run.add_argument("--fixtures-dir", default="data/fixtures")
    run.add_argument("--readme", default="README.md")
    run.add_argument("--listings", default="LISTINGS.md")
    run.add_argument("--json", default="data/current-listings.json")
    run.add_argument(
        "--live",
        action="store_true",
        help="Run live Apify actors instead of local fixtures",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        messages = run_pipeline(
            args.config,
            dry_run=not args.live,
            fixtures_dir=args.fixtures_dir,
            readme_path=args.readme,
            listings_path=args.listings,
            json_path=args.json,
        )
        for message in messages:
            print(message)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
