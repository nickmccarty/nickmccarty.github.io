"""
keyword_suggest.py — use Ollama to suggest / improve SEO keywords for blog posts.

Usage:
    python keyword_suggest.py                         # suggest for all posts, save to keyword-suggestions.json
    python keyword_suggest.py --model qwen2.5:7b      # use a different model
    python keyword_suggest.py --apply                 # write to posts that have NO existing keywords
    python keyword_suggest.py --apply --update        # also overwrite existing keywords with suggestions

Output:
    keyword-suggestions.json   one entry per post with existing + suggested + diff flag
"""
import argparse
import json
import re
import time
from pathlib import Path

import requests

BLOG_DIR = Path("blog")
OLLAMA   = "http://localhost:11434/api/chat"
OUT_FILE = Path("keyword-suggestions.json")


def jld(html, field):
    m = re.search(rf'"{re.escape(field)}"\s*:\s*"([^"]+)"', html)
    return m.group(1) if m else ""


def ask_ollama(model: str, title: str, desc: str, section: str, existing: str) -> list[str]:
    prompt = (
        f"Title: {title}\n"
        f"Category: {section}\n"
        f"Description: {desc}\n"
        f"Current keywords: {existing or 'none'}\n\n"
        "Output ONLY a JSON array of exactly 3 keyword phrases (1–4 words each). "
        "They must be specific, technically accurate, and have real search demand. "
        "Prefer exact tool/method names over generic terms. "
        'Format: ["phrase one", "phrase two", "phrase three"]'
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an SEO keyword specialist. "
                    "Reply with ONLY a JSON array of keyword strings — no prose, no markdown, no thinking."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.1, "num_predict": 100},
    }
    r = requests.post(OLLAMA, json=payload, timeout=120)
    r.raise_for_status()
    content = r.json()["message"]["content"].strip()
    # Strip Qwen3 <think> blocks if present
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    m = re.search(r"\[.*?\]", content, re.DOTALL)
    if not m:
        return []
    try:
        return [k.strip() for k in json.loads(m.group()) if isinstance(k, str) and k.strip()][:4]
    except (json.JSONDecodeError, ValueError):
        return []


def write_keywords(path: Path, html: str, existing: str, new_kws: list[str]) -> bool:
    kw_str = ", ".join(new_kws)
    if existing:
        old = f'"keywords":"{existing}"'
        if old not in html:
            return False
        updated = html.replace(old, f'"keywords":"{kw_str}"', 1)
    else:
        # Insert before "author" which is present in every post's JSON-LD
        if '"author":' not in html:
            return False
        updated = html.replace('"author":', f'"keywords":"{kw_str}","author":', 1)
    if updated == html:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def kw_list(s: str) -> list[str]:
    return [k.strip() for k in s.split(",") if k.strip()] if s else []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model",  default="qwen3:8b", help="Ollama model tag")
    ap.add_argument("--apply",  action="store_true", help="write keywords to posts with no existing keywords")
    ap.add_argument("--update", action="store_true", help="also overwrite posts that already have keywords")
    args = ap.parse_args()

    posts = sorted(p for p in BLOG_DIR.glob("*.html") if not p.stem.endswith("-embed"))
    print(f"Model : {args.model}")
    print(f"Posts : {len(posts)}")
    print(f"Apply : {'yes (new only)' if args.apply and not args.update else 'yes (all)' if args.apply else 'no (dry run)'}")
    print()

    results = []
    wrote_count = 0

    for i, path in enumerate(posts, 1):
        html     = path.read_text(encoding="utf-8", errors="replace")
        title    = jld(html, "headline") or path.stem
        desc     = jld(html, "description")
        section  = jld(html, "articleSection")
        existing = jld(html, "keywords")

        print(f"[{i:3d}/{len(posts)}] {path.name}", flush=True)
        t0 = time.time()

        try:
            suggested = ask_ollama(args.model, title, desc, section, existing)
        except Exception as e:
            print(f"         ERROR: {e}")
            results.append({"slug": path.name, "title": title, "existing": existing,
                            "suggested": [], "changed": False, "error": str(e)})
            continue

        elapsed = time.time() - t0
        existing_list  = kw_list(existing)
        changed        = suggested != existing_list

        wrote = False
        if args.apply and suggested:
            if not existing or args.update:
                wrote = write_keywords(path, html, existing, suggested)
                if wrote:
                    wrote_count += 1

        # Print comparison lines
        if existing_list:
            print(f"         was : {existing_list}")
        else:
            print(f"         was : (none)")
        marker = "  [same]" if not changed else ("  [diff]" if existing else "  [new]")
        print(f"         now : {suggested}{marker}  [{elapsed:.1f}s]{'  [wrote]' if wrote else ''}")
        print()

        results.append({
            "slug":      path.name,
            "title":     title,
            "existing":  existing_list,
            "suggested": suggested,
            "changed":   changed,
            "wrote":     wrote,
        })

    OUT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Summary
    no_kw     = sum(1 for r in results if not r["existing"])
    has_kw    = sum(1 for r in results if r["existing"])
    improved  = sum(1 for r in results if r["existing"] and r["changed"])
    errors    = sum(1 for r in results if "error" in r)

    print("-" * 60)
    print(f"Posts without existing keywords : {no_kw}")
    print(f"Posts with existing keywords    : {has_kw}  ({improved} have differing suggestions)")
    print(f"Errors                          : {errors}")
    if args.apply:
        print(f"Files written                   : {wrote_count}")
    print(f"Results saved -> {OUT_FILE}")


if __name__ == "__main__":
    main()
