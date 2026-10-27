"""Static text review of source references; never imports their Python or JS."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
PATTERNS = {
    "process-execution": r"child_process|\b(?:exec|spawn|subprocess|os\.system|eval\()",
    "network": r"fetch\(|https?://|requests\.|urllib|\bsocket\b",
    "file-mutation": r"writeFile|unlink|rmtree|write_text|write_bytes|Remove-Item",
    "credentials-env": r"process\.env|os\.environ|api[_ -]?key|access[_ -]?token|credentials",
    "account-or-paid-service": r"\bbilling\b|\bpaid\b|\bcredits\b|sign up|create an account",
    "global-install-config": r"npm install -g|--global|settings\.json|\.claude\.json|CLAUDE\.md|\bhooks\b",
    "telemetry-or-data-transfer": r"\btelemetry\b|\banalytics\b|\bupload\b|\bexfiltrat",
    "publish-or-deploy": r"\bdeploy\b|\bpublish\b|git push",
    "global-behavior-override": r"ignore (?:all |previous |prior )?instructions|override.*(?:system|instructions)|MUST.*(?:invoke|use).*skill|before.*ANY.*response",
    "proxy-or-endpoint-change": r"ANTHROPIC_BASE_URL|OPENAI_BASE_URL|api[_-]?base[_-]?url|claude.*proxy",
}
CODE_SUFFIXES = {".py", ".js", ".cjs", ".mjs", ".sh", ".ps1", ".ts", ".bat", ".cmd"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PACKAGE)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    receipt = json.loads((root / "catalog" / "source-receipt.json").read_text(encoding="utf-8"))
    picks = json.loads((root / "catalog" / "selected-skills.json").read_text(encoding="utf-8"))["skills"]
    indexed = json.loads((root / "catalog" / "skills.json").read_text(encoding="utf-8"))["skills"]
    compiled = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}
    results = []
    for record in receipt["sources"]:
        folder = (root / record["path"]).resolve()
        if not folder.is_relative_to(root):
            raise SystemExit("Invalid source receipt path")
        files, counts, examples, skipped = [], Counter(), [], []
        skill_paths = []
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.is_symlink() or ".git" in path.relative_to(folder).parts:
                continue
            relative = path.relative_to(folder).as_posix()
            files.append(relative)
            is_skill = path.name == "SKILL.md"
            if is_skill:
                skill_paths.append(relative)
            if not is_skill and path.suffix.lower() not in CODE_SUFFIXES:
                continue
            if path.stat().st_size > 2_000_000:
                skipped.append(relative)
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), 1):
                tags = [k for k, regex in compiled.items() if regex.search(line)]
                counts.update(tags)
                if tags:
                    examples.append({"path": relative, "line": number, "tags": tags})
        reviewed = []
        mismatches = []
        normalized_count = 0
        for skill in indexed:
            if skill["repository"] != record["repository"]:
                continue
            local = folder / skill["path"]
            if not local.is_file():
                mismatches.append(skill["path"])
                continue
            raw = local.read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False).hexdigest()
            if blob != skill["blob_sha"]:
                normalized = raw.replace(b"\r\n", b"\n")
                lf_blob = hashlib.sha1(b"blob " + str(len(normalized)).encode() + b"\0" + normalized, usedforsecurity=False).hexdigest()
                if lf_blob == skill["blob_sha"]:
                    normalized_count += 1
                else:
                    mismatches.append(skill["path"])
        for pick in picks:
            if pick["repository"] != record["repository"]:
                continue
            path = folder / pick["path"]
            if not path.is_file():
                reviewed.append({"id": pick["id"], "status": "not-present-at-local-commit"})
                continue
            content = path.read_bytes()
            text = content.decode("utf-8", errors="replace")
            front = text.split("---", 2)[1] if text.startswith("---") else ""
            license_line = next((line.strip() for line in front.splitlines() if line.startswith("license:")), None)
            reviewed.append({"id": pick["id"], "status": "static-review", "sha256": hashlib.sha256(content).hexdigest(),
                             "content_chars": len(text), "license_declaration": license_line,
                             "flags": [k for k, regex in compiled.items() if regex.search(text)]})
        inventory = {"repository": record["repository"], "actual_commit": record["actual_commit"],
                     "file_count": len(files), "files": files, "skill_count": len(skill_paths),
                     "flag_counts": dict(counts), "flagged_lines": examples, "skipped_large_files": skipped,
                     "selected_skills": reviewed, "matches_lock": record["matches_lock"]}
        inventory["indexed_skill_mismatches"] = mismatches
        inventory["line_ending_normalized_count"] = normalized_count
        results.append(inventory)
        print(f'{record["repository"]}: {len(files)} files, {len(skill_paths)} skills, {sum(counts.values())} keyword hits')
    payload = {"method": "static keyword screening; not a complete audit or execution test", "sources": results,
               "sync_failures": receipt.get("failures", [])}
    (root / "catalog" / "source-review.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Yerel kaynak incelemesi", "", "Bu rapor dosya envanteri, anahtar kelime taraması ve seçilmiş SKILL.md metinlerinin hash/işaret kayıtlarını içerir. Kaynak kodları çalıştırılmadı. Kelime eşleşmeleri bulguların inceleme adaylarıdır; tek başına zafiyet veya güvenlik onayı değildir.", "",
             "| Kaynak | Dosya | SKILL.md | Commit kilidi | Etkinleştirme |", "|---|---:|---:|---|---|"]
    for r in results:
        lines.append(f'| [{r["repository"]}](https://github.com/{r["repository"]}) | {r["file_count"]} | {r["skill_count"]} | {"aynı" if r["matches_lock"] else "eski yerel sürüm korundu"} | yapılmadı |')
    lines += ["", "## İncelemede dikkat edilecek davranışlar", ""]
    for r in results:
        flags = ", ".join(f"{k}: {v}" for k, v in sorted(r["flag_counts"].items())) or "İşaret yok."
        lines.append(f'- **{r["repository"]}** — {flags}')
    lines += ["", "Kaynakların bazıları API anahtarı, hesap veya ücretli hizmet; bazısı global kurulum, hook/ayar değişikliği, telemetri, veri yükleme, yayınlama veya genel ajan davranışını değiştirme talimatı içerir. Bunlar uygulanmadı. Özellikle iş akışı paketlerinin tümünü otomatik etkinleştirmek yerine görev için gereken tekil beceri incelenmelidir.", "",
              "Tam dosya listesi ve satır bazında eşleşme konumları `catalog/source-review.json` içindedir. Bu JSON kaynak satırlarını veya kimlik bilgilerini kopyalamaz. İki mevcut kaynağın yerel commit'i çevrimiçi kilitten farklı olabilir; bunlara dokunulmaz. Seçili becerilerin içerik değerlendirme notları `catalog/skill-review-notes.json` içindedir; son sürümün tüm talimatları denetlenmiş sayılmaz."]
    if receipt.get("failures"):
        lines += ["", "## Tamamlanamayan kaynaklar", ""] + ["- " + r["repository"] for r in receipt["failures"]]
    notes_path = root / "catalog" / "skill-review-notes.json"
    if notes_path.exists():
        notes = json.loads(notes_path.read_text(encoding="utf-8"))
        lines += ["", "## Etkinleştirme kararı", "", "Aşağıdaki beceriler etkinleştirmeye kapalı olarak işaretlendi:", ""]
        lines += [f'- `{n["repository"]}/{n["path"]}`: {n["reason"]}' for n in notes["blocked_for_activation"]]
    mismatched = sum(len(r["indexed_skill_mismatches"]) for r in results)
    lines += ["", f"Git blob kimliği uyuşmayan veya eksik skill dosyası: {mismatched}. CRLF/LF dönüşümleri ayrı doğrulandı."]
    (root / "SOURCE_REVIEW.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if mismatched or receipt.get("failures"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
