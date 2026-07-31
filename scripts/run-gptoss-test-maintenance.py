#!/usr/bin/env python3
"""Run frozen Markdig prompts through OpenRouter GPT-OSS exactly once."""

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MAX_TRANSPORT_ATTEMPTS = 3
INITIAL_BACKOFF_SECONDS = 5


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load_json(path):
    with path.open() as f:
        return json.load(f)


def case_directory(exp, case):
    archive_id = (
        case["case_id"].lower().replace("-", "")
        + "-"
        + case["upstream_sha"][:8]
    )
    return exp / "cases" / archive_id


def validate_completed(case_dir, expected):
    response_path = case_dir / "gptoss-response.md"
    run_path = case_dir / "gptoss-run.json"
    usage_path = case_dir / "gptoss-usage.json"
    if not all(path.is_file() for path in (response_path, run_path, usage_path)):
        return False
    run = load_json(run_path)
    response = response_path.read_text()
    return (run.get("status") == "response_received"
            and run.get("case_id") == expected["case_id"]
            and run.get("prompt_sha256") == expected["prompt_sha256"]
            and run.get("response_sha256") == sha256_text(response))


def request_once(api_key, model, temperature, prompt):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://local-thesis-experiment",
            "X-Title": "markdig-maintenance-week5",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        raw = response.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        text = raw.decode("utf-8", errors="replace")
        stripped = "\n".join(
            line for line in text.splitlines() if not line.startswith(":"))
        return json.loads(stripped)


def run_case(exp, expected, api_key, resume):
    case_id = expected["case_id"]
    case_dir = case_directory(exp, expected)
    if validate_completed(case_dir, expected):
        if resume:
            print(f"MODEL: SKIP {case_id} validated-complete", flush=True)
            return "skipped"
        raise RuntimeError(f"{case_id}: response already exists; use --resume")

    prompt = (case_dir / "gptoss-prompt.md").read_text()
    if sha256_text(prompt) != expected["prompt_sha256"]:
        raise RuntimeError(f"{case_id}: prompt digest mismatch")
    attempts = []
    started = time.monotonic()
    data = None
    for attempt in range(1, MAX_TRANSPORT_ATTEMPTS + 1):
        try:
            data = request_once(
                api_key, expected["model"], expected["temperature"], prompt)
            attempts.append({"attempt": attempt, "result": "response_received"})
            break
        except urllib.error.HTTPError as error:
            attempts.append({
                "attempt": attempt,
                "result": "http_error",
                "status": error.code,
            })
            retryable = error.code == 429 or 500 <= error.code < 600
            if not retryable or attempt == MAX_TRANSPORT_ATTEMPTS:
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            attempts.append({
                "attempt": attempt,
                "result": "transport_error",
                "error_type": type(error).__name__,
            })
            if attempt == MAX_TRANSPORT_ATTEMPTS:
                break
        time.sleep(INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1)))

    if data is None:
        error_doc = {
            "case_id": case_id,
            "status": "no_response",
            "model_requested": expected["model"],
            "attempts": attempts,
        }
        with (case_dir / "gptoss-error.json").open("w") as f:
            json.dump(error_doc, f, indent=2)
            f.write("\n")
        raise RuntimeError(f"{case_id}: no assistant response after transport retries")

    choices = data.get("choices") or []
    if not choices or not isinstance(choices[0].get("message", {}).get("content"), str):
        raise RuntimeError(f"{case_id}: API response missing assistant content")
    content = choices[0]["message"]["content"]
    usage = data.get("usage", {})
    first_line = content.splitlines()[0] if content.splitlines() else ""
    elapsed = round(time.monotonic() - started, 3)

    (case_dir / "gptoss-response.md").write_text(content)
    with (case_dir / "gptoss-usage.json").open("w") as f:
        json.dump(usage, f, indent=2)
        f.write("\n")
    run_doc = {
        "case_id": case_id,
        "status": "response_received",
        "model_requested": expected["model"],
        "model_returned": data.get("model"),
        "temperature": expected["temperature"],
        "response_id": data.get("id"),
        "created": data.get("created"),
        "finish_reason": choices[0].get("finish_reason"),
        "attempt_count": len(attempts),
        "attempts": attempts,
        "elapsed_seconds": elapsed,
        "prompt_sha256": expected["prompt_sha256"],
        "response_sha256": sha256_text(content),
        "first_line": first_line,
    }
    with (case_dir / "gptoss-run.json").open("w") as f:
        json.dump(run_doc, f, indent=2)
        f.write("\n")
    total_tokens = usage.get("total_tokens", "unknown")
    print(f"MODEL: OK {case_id} {first_line[:80]} tokens={total_tokens}", flush=True)
    return "completed"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", default="experiments/test-maintenance")
    parser.add_argument("--case")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if bool(args.case) == bool(args.all):
        raise SystemExit("select exactly one of --case or --all")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("missing required env var: OPENROUTER_API_KEY")
    exp = Path(args.exp).resolve()
    manifest = load_json(exp / "cases.json")
    if manifest.get("case_count") != 23:
        raise SystemExit("unexpected frozen case count")
    by_id = {}
    for case in manifest["cases"]:
        item = load_json(case_directory(exp, case) / "input.json")
        if item.get("case_id") != case["case_id"]:
            raise SystemExit(f"{case['case_id']}: input metadata mismatch")
        by_id[case["case_id"]] = item
    selected = (
        [case["case_id"] for case in manifest["cases"]]
        if args.all else [args.case]
    )
    if any(case_id not in by_id for case_id in selected):
        raise SystemExit("unknown case selected")

    completed = 0
    skipped = 0
    for case_id in selected:
        result = run_case(exp, by_id[case_id], api_key, args.resume)
        completed += result == "completed"
        skipped += result == "skipped"
    print(f"MODEL RUNS COMPLETE completed={completed} skipped={skipped}")


if __name__ == "__main__":
    main()
