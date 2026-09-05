from __future__ import annotations

import argparse
import json

import ghostchat_nudge as nudge


def main() -> int:
    p = argparse.ArgumentParser(description="GhostChat Sync Fix v2.2 diagnostic sync nudge")
    p.add_argument("--search-toggle", action="store_true", help="manual-only Ctrl+K then Escape test")
    args = p.parse_args()

    if args.search_toggle:
        result = nudge.search_toggle_if_foreground()
    else:
        result = nudge.reactivate_chatgpt_if_foreground()

    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))
    if not result.attempted:
        print("\nKeep ChatGPT in the foreground, then run this test again.")
    elif result.ok:
        print("\nNudge sent. Wait a few seconds, then check whether the ghost entry disappears.")
    else:
        print("\nNudge failed safely. No database or account data was changed by this test.")
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
