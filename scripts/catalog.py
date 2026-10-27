"""Search, validate and refresh the portable public GitHub catalog (stdlib only)."""

import argparse
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / "catalog" / name).read_text(encoding="utf-8"))


def save(name, value):
    path = ROOT / "catalog" / name
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def metric_score(repo, checked):
    days = max(0, (checked - datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")).date()).days)
    activity = 25 if days <= 30 else 20 if days <= 90 else 15 if days <= 180 else 8 if days <= 365 else 0
    value = min(35, 7 * math.log10(repo["stars"] + 1)) + min(15, 3.75 * math.log10(repo["forks"] + 1))
    value += activity + (15 if repo["license"] not in (None, "NOASSERTION") else 0)
    value += 10 if not repo["archived"] and not repo["disabled"] else 0
    return round(value, 1), days


def validate(data):
    errors = []
    repos = data["repositories"]
    skills = read("skills.json")["skills"]
    ids = {s["id"] for s in skills}
    if len(ids) != len(skills):
        errors.append("Duplicate skill ids")
    category_ids = [c["id"] for c in data["categories"]]
    if len(category_ids) != len(set(category_ids)):
        errors.append("Duplicate category ids")
    for key, r in repos.items():
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", key) or r["url"] != "https://github.com/" + r["name"]:
            errors.append("Invalid repository identity: " + key)
        if not isinstance(r["stars"], int) or r["stars"] < 0 or not 0 <= r["score"] <= 100:
            errors.append("Invalid metrics: " + key)
        datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
        expected, _ = metric_score(r, datetime.fromisoformat(r["checked_at"]).date())
        if expected != r["score"]:
            errors.append("Score mismatch: " + key)
    for c in data["categories"]:
        if not c["repositories"]:
            errors.append("Empty category: " + c["id"])
        errors.extend("Missing repository: " + x for x in c["repositories"] if x not in repos)
        errors.extend("Missing skill: " + x for x in c["skills"] if x not in ids)
    selected_ids = {s["id"] for s in read("selected-skills.json")["skills"]}
    if selected_ids != {sid for c in data["categories"] for sid in c["skills"]}:
        errors.append("Selected skill list differs from category references")
    blocked = {s["id"] for s in skills if s.get("activation_policy") == "blocked"}
    if selected_ids & blocked:
        errors.append("A blocked skill is in the selected recommendations")
    for s in skills:
        path = Path(s["path"])
        if path.is_absolute() or ".." in path.parts or not re.fullmatch(r"[a-f0-9]{40}", s["source_commit"]):
            errors.append("Invalid skill reference: " + s["id"])
        if not s["url"].startswith("https://github.com/" + s["repository"] + "/blob/" + s["source_commit"] + "/"):
            errors.append("Unpinned skill URL: " + s["id"])
    for s in read("sources.lock.json")["sources"]:
        if s["tree_truncated"] or not re.fullmatch(r"[a-f0-9]{40}", s["commit"]):
            errors.append("Unverified source lock: " + s["repository"])
    resources_file = ROOT / "catalog/resources.json"
    if resources_file.is_file():
        resources = read("resources.json")["resources"]
        if len({r["id"] for r in resources}) != len(resources):
            errors.append("Duplicate external resource ids")
        for r in resources:
            if (r["provider"] != "huggingface-dataset" or not re.fullmatch(r"[\w.-]+/[\w.-]+", r["id"])
                or r["url"] != "https://huggingface.co/datasets/" + r["id"]
                or not re.fullmatch(r"[a-f0-9]{40}", r["revision"])
                or set(r["categories"]) - set(category_ids)):
                errors.append("Invalid external resource: " + r["id"])
    if errors:
        raise SystemExit("\n".join(errors))
    print(f'OK: {len(data["categories"])} categories, {len(repos)} repositories, {len(skills)} skill paths')


def search(data, args):
    categories = data["categories"]
    if args.category:
        categories = [c for c in categories if c["id"] == args.category]
        if not categories:
            raise SystemExit("Unknown category; use the categories command.")
    query = args.query.casefold()
    if not args.skills and (ROOT / "catalog/resources.json").is_file():
        for r in read("resources.json")["resources"]:
            haystack = " ".join([r["id"], r["description"], *r.get("aliases", [])]).casefold()
            if query in haystack and (not args.category or args.category in r["categories"]):
                print(f'{r["id"]} | {r["provider"]} | {r["status"]}\n  {r["url"]}')
    if args.skills:
        allowed = {x for c in categories for x in c["skills"]} if args.category else None
        for s in read("skills.json")["skills"]:
            text = " ".join([s["name"], s.get("declared_name", ""), s["repository"], s["path"]]).casefold()
            if query in text and (allowed is None or s["id"] in allowed):
                print(f'{s["name"]} | {s["repository"]}\n  {s["url"]}')
                if s.get("activation_policy") == "blocked":
                    print("  BLOCKED FOR ACTIVATION: " + s["activation_reason"])
        installed = read("local-inventory.json")["installed_skills"]
        local_names = {n for c in categories for n in c["existing_skills"]} if args.category else None
        for item in installed:
            if query in item["name"].casefold() and (local_names is None or item["name"] in local_names):
                print(f'{item["name"]} | historical inventory (not checked on this computer) | providers={",".join(item["providers"])}')
        return
    keys = {x for c in categories for x in c["repositories"]}
    for key in sorted(keys, key=lambda k: data["repositories"][k]["score"], reverse=True):
        r = data["repositories"][key]
        if query in (key + " " + (r["description"] or "") + " " + " ".join(r["topics"])).casefold():
            print(f'{key} | stars={r["stars"]:,} | score={r["score"]} | license={r["license"] or "unknown"}\n  {r["url"]}')


def refresh(data, apply):
    checked = datetime.now(timezone.utc).date()
    headers = {"User-Agent": "claude-refs-catalog", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    refreshed = json.loads(json.dumps(data))
    for key in refreshed["repositories"]:
        req = urllib.request.Request("https://api.github.com/repos/" + key, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                current = json.load(response)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"GitHub HTTP {exc.code} for {key}; stopped, original catalog unchanged.") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise SystemExit(f"Network error ({type(exc).__name__}); original catalog unchanged.") from None
        r = refreshed["repositories"][key]
        if current.get("full_name") != r["name"]:
            raise SystemExit(f"Repository moved: {key}; inspect manually. Original catalog unchanged.")
        old_stars = r["stars"]
        r.update(stars=current["stargazers_count"], forks=current["forks_count"], pushed_at=current["pushed_at"],
                 updated_at=current["updated_at"], archived=current["archived"], disabled=current["disabled"],
                 license=(current.get("license") or {}).get("spdx_id"), checked_at=checked.isoformat())
        r["score"], r["days_since_push"] = metric_score(r, checked)
        print(f'{key}: stars {old_stars:,} -> {r["stars"]:,}; score={r["score"]}')
        time.sleep(1)
    refreshed["checked_at"] = checked.isoformat()
    for c in refreshed["categories"]:
        c["repositories"].sort(key=lambda k: refreshed["repositories"][k]["score"], reverse=True)
        c["popularity_order"].sort(key=lambda k: refreshed["repositories"][k]["stars"], reverse=True)
    save("repositories.json" if apply else "refresh-preview.json", refreshed)
    print("Saved. Run render to update KATALOG.md." if apply else "Preview saved; use --apply to change catalog metadata.")


def render(data):
    lines = ["# Kategori bazında repo kataloğu", "", f'Doğrulama: **{data["checked_at"]}**.', "",
             "Sıra aday kümesindeki puana göredir. Yöntem: [YONTEM.md](YONTEM.md).", ""]
    if data.get("latest_additions_checked_at"):
        lines += [f'İstenen ek kaynakların son kontrolü: **{data["latest_additions_checked_at"]}**; '
                  'ayrıntılar [ekleme raporunda](EKLENEN_KAYNAKLAR.md). Diğer kayıtların kendi kontrol tarihi korunur.', ""]
    for c in data["categories"]:
        lines += [f'## {c["name"]}', "", "| Repo | Yıldız | Fork | Son push | Lisans | Puan |", "|---|---:|---:|---|---|---:|"]
        for key in c["repositories"]:
            r = data["repositories"][key]
            lines.append(f'| [{key}]({r["url"]}) | {r["stars"]:,} | {r["forks"]:,} | {r["pushed_at"][:10]} | {r["license"] or "belirsiz"} | {r["score"]} |')
        lines += ["", "Adayların amaçları:", ""]
        for key in c["repositories"]:
            desc = (data["repositories"][key]["description"] or "Açıklama belirtilmemiş.").replace("\n", " ")
            lines.append(f"- **{key}**: {desc}")
        lines += ["", f'Skill eşleştirmesi: [rehber](SKILL_REHBERI.md#{c["id"]}).', ""]
    (ROOT / "KATALOG.md").write_text("\n".join(lines), encoding="utf-8")
    print("KATALOG.md regenerated.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("categories")
    sub.add_parser("validate")
    sub.add_parser("render")
    find = sub.add_parser("search")
    find.add_argument("query", nargs="?", default="")
    find.add_argument("--category")
    find.add_argument("--skills", action="store_true")
    update = sub.add_parser("refresh")
    update.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    data = read("repositories.json")
    if args.command == "categories":
        for c in data["categories"]:
            print(f'{c["id"]}: {c["name"]} ({len(c["repositories"])} repos, {len(c["skills"])} skills)')
    elif args.command == "search":
        search(data, args)
    elif args.command == "validate":
        validate(data)
    elif args.command == "render":
        render(data)
    elif args.command == "refresh":
        refresh(data, args.apply)


if __name__ == "__main__":
    main()
