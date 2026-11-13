import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="localemesh")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_site = sub.add_parser("site", help="run local fixture site")
    p_site.add_argument("--port", type=int, default=8761)
    p_site.add_argument("--root", default="fixtures/catalog")
    p_site.add_argument("--host", default="127.0.0.1")

    p_crawl = sub.add_parser("crawl", help="crawl fixture site and build clusters")
    p_crawl.add_argument("--base", required=True)
    p_crawl.add_argument("--out", required=True)
    p_crawl.add_argument("--checkpoint", required=True)
    p_crawl.add_argument("--accept-language", default="en,fr;q=0.8,de;q=0.6,ja;q=0.4")

    p_verify = sub.add_parser("verify", help="compare crawl output with expected file")
    p_verify.add_argument("--out", required=True)
    p_verify.add_argument("--expect", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "site":
        from localemesh.site import serve
        serve(host=args.host, port=args.port, root=args.root)
        return 0
    if args.cmd == "crawl":
        from localemesh.crawl import run_crawl
        return run_crawl(args)
    if args.cmd == "verify":
        from localemesh.verify import run_verify
        return run_verify(args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
