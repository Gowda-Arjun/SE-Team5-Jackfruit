"""Create the HMS backlog on GitHub from backlog.csv.

Creates labels, the two sprint milestones, a GitHub Project (linked to the repo)
with Story Points / Sprint / Priority fields, and one issue per backlog row,
assigned to its owner and added to the project with its fields filled in.

Safe to re-run: issues whose "[HMS-xx]" title already exists are skipped.

Prerequisites:
    gh auth refresh -s project          # gh needs the "project" scope
    Arjun has created the project, linked it to the repo and made you an Admin on it
    (all four members must have accepted the repo invite to be assignable)

Usage (from the repo root):
    python docs/backlog/create_backlog.py --dry-run
    python docs/backlog/create_backlog.py
"""

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = "Gowda-Arjun/SE-Team5-Jackfruit"
# Must be the repo owner: GitHub only links a project to repos of the same owner.
# Arjun creates the project and gives the person running this script Admin access.
PROJECT_OWNER = "Gowda-Arjun"
PROJECT_TITLE = "HMS - Team 5 Backlog"

# GitHub usernames of each owner key used in backlog.csv.
MEMBERS = {
    "ARJAV": "arjav188",
    "ARJUN": "Gowda-Arjun",
    "ARMAAN": "armaanyt07-jpg",
    "ARNAV": "Arnav060706",
}

MILESTONES = {
    "Sprint 1": ("2026-10-23T23:59:59Z",
                 "Sprint 1 (19-23 Oct): foundation, auth, room allocation, fee setup, complaints"),
    "Sprint 2": ("2026-10-30T23:59:59Z",
                 "Sprint 2 (26-30 Oct): payments, room change, complaint workflow, reports, NFRs"),
}

LABELS = {
    "user-story": "1d76db", "nfr": "5319e7", "security": "b60205", "chore": "c5def5",
    "priority:high": "d93f0b", "priority:medium": "fbca04", "priority:low": "0e8a16",
    "module:auth": "bfd4f2", "module:allocation": "bfd4f2", "module:fees": "bfd4f2",
    "module:complaints": "bfd4f2", "module:reports": "bfd4f2", "module:audit": "bfd4f2",
    "module:infra": "bfd4f2",
}

DRY_RUN = False


NETWORK_ERRORS = ("error connecting", "timeout", "forcibly closed", "connection reset", "EOF", "TLS handshake",
                  "502", "503", "504")


def gh(*args, retries=6):
    """Run a gh command and return stdout. In --dry-run, write commands are only printed.

    Transient network failures are retried with backoff (flaky campus Wi-Fi).
    """
    if DRY_RUN and _is_write(args):
        print("  [dry-run] gh", " ".join(args[:4]), "...")
        return ""
    for attempt in range(1, retries + 1):
        result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0:
            return result.stdout.strip()
        err = result.stderr.strip()
        if attempt < retries and any(e.lower() in err.lower() for e in NETWORK_ERRORS):
            wait = min(2 ** attempt, 30)
            print(f"  network error, retrying in {wait}s ({attempt}/{retries - 1})...")
            time.sleep(wait)
            continue
        raise RuntimeError(f"gh {' '.join(args[:3])} failed: {err}")


def _is_write(args):
    if args[0] == "api":
        return "-X" in args
    reads = {("issue", "list"), ("project", "list"), ("project", "view"), ("project", "field-list")}
    return tuple(args[:2]) not in reads


def ensure_labels():
    for name, color in LABELS.items():
        gh("label", "create", name, "--color", color, "--force", "-R", REPO)


def ensure_milestones():
    existing = json.loads(gh("api", f"repos/{REPO}/milestones?state=all") or "[]")
    titles = {m["title"] for m in existing}
    for title, (due, desc) in MILESTONES.items():
        if title not in titles:
            gh("api", "-X", "POST", f"repos/{REPO}/milestones",
               "-f", f"title={title}", "-f", f"due_on={due}", "-f", f"description={desc}")


def ensure_project():
    """Return (number, node_id, fields_by_name) for the backlog project."""
    projects = json.loads(gh("project", "list", "--owner", PROJECT_OWNER, "--format", "json") or '{"projects": []}')
    proj = next((p for p in projects["projects"] if p["title"] == PROJECT_TITLE), None)
    if proj is None:
        if DRY_RUN:
            print("  [dry-run] would create project", PROJECT_TITLE)
            return None, None, {}
        sys.exit(
            f'\nProject "{PROJECT_TITLE}" not found under {PROJECT_OWNER}.\n'
            f"{PROJECT_OWNER} must create it (Profile -> Projects -> New project, exact title above), "
            "link it to the repo, and add you as Admin under the project's Settings -> Manage access. "
            "Then re-run this script."
        )
    number = str(proj["number"])

    fields = {f["name"]: f for f in json.loads(
        gh("project", "field-list", number, "--owner", PROJECT_OWNER, "--format", "json"))["fields"]}
    wanted = {
        "Story Points": ["--data-type", "NUMBER"],
        "Sprint": ["--data-type", "SINGLE_SELECT", "--single-select-options", "Sprint 1,Sprint 2"],
        "Priority": ["--data-type", "SINGLE_SELECT", "--single-select-options", "High,Medium,Low"],
    }
    created = False
    for name, spec in wanted.items():
        if name not in fields:
            gh("project", "field-create", number, "--owner", PROJECT_OWNER, "--name", name, *spec)
            created = True
    if created and not DRY_RUN:
        fields = {f["name"]: f for f in json.loads(
            gh("project", "field-list", number, "--owner", PROJECT_OWNER, "--format", "json"))["fields"]}
    return number, proj.get("id"), fields


def option_id(field, name):
    return next((o["id"] for o in field.get("options", []) if o["name"] == name), None)


def set_fields(item_id, project_id, fields, row):
    if DRY_RUN or not item_id:
        return
    base = ["project", "item-edit", "--id", item_id, "--project-id", project_id]
    gh(*base, "--field-id", fields["Story Points"]["id"], "--number", row["points"])
    for field_name, value in (("Sprint", row["sprint"]), ("Priority", row["priority"]), ("Status", "Todo")):
        field = fields.get(field_name)
        opt = option_id(field, value) if field else None
        if opt:
            gh(*base, "--field-id", field["id"], "--single-select-option-id", opt)


def issue_body(row):
    return (
        f"**Backlog ID:** {row['key']}\n"
        f"**Requirement:** {row['requirement']}\n"
        f"**Story points:** {row['points']}\n"
        f"**Priority:** {row['priority']}\n"
        f"**Sprint:** {row['sprint']}\n\n"
        "### Acceptance criteria\n"
        + "\n".join(f"- [ ] {c.strip()}" for c in row["acceptance"].split(";") if c.strip())
        + "\n\n_Source: SRS v1.0 / SAD v1.0 / STP v1.0. Raise the PR from a branch named "
        f"`{row['key'].lower()}-short-name` and write `Closes #<this issue>` in the PR description._\n"
    )


def find_issue_url(key):
    """URL of an existing issue whose title starts with [key], or None."""
    if DRY_RUN:
        return None
    found = json.loads(gh("issue", "list", "-R", REPO, "--state", "all", "--search", f"{key} in:title",
                          "--json", "title,url") or "[]")
    return next((i["url"] for i in found if i["title"].startswith(f"[{key}]")), None)


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print what would be created")
    DRY_RUN = parser.parse_args().dry_run

    rows = list(csv.DictReader(open(Path(__file__).with_name("backlog.csv"), encoding="utf-8")))
    missing = [k for k, v in MEMBERS.items() if not v]
    if missing:
        print(f"WARNING: no GitHub username for {missing}; their issues will be created unassigned.")

    print("Labels...")
    ensure_labels()
    print("Milestones...")
    ensure_milestones()
    print("Project...")
    number, project_id, fields = ensure_project()

    existing = json.loads(gh("issue", "list", "-R", REPO, "--state", "all", "--limit", "500",
                             "--json", "title") or "[]")
    existing_keys = {t["title"].split("]")[0] + "]" for t in existing if t["title"].startswith("[HMS-")}

    for row in rows:
        title = f"[{row['key']}] {row['title']}"
        if f"[{row['key']}]" in existing_keys:
            print(f"skip   {title} (exists)")
            continue
        labels = [row["type"], f"priority:{row['priority'].lower()}", f"module:{row['module']}"]
        args = ["issue", "create", "-R", REPO, "--title", title, "--body", issue_body(row),
                "--milestone", row["sprint"]]
        for label in labels:
            args += ["--label", label]
        assignee = MEMBERS.get(row["owner"])
        try:
            url = gh(*args, *(["--assignee", assignee] if assignee else []), retries=1)
        except RuntimeError as err:
            # The issue may have been created even though the reply was lost - never duplicate it.
            url = find_issue_url(row["key"])
            if not url:
                if assignee and ("not found" in str(err).lower() or "assign" in str(err).lower()):
                    print(f"  could not assign {assignee}; creating unassigned")
                    url = gh(*args, retries=1)
                else:
                    time.sleep(5)
                    url = find_issue_url(row["key"]) or gh(*args, retries=1)
        print(f"create {title} -> {url or '(dry-run)'}")
        if number and url:
            item = json.loads(gh("project", "item-add", number, "--owner", PROJECT_OWNER, "--url", url,
                                 "--format", "json"))
            set_fields(item["id"], project_id, fields, row)

    by_sprint = {}
    for row in rows:
        by_sprint.setdefault(row["sprint"], {}).setdefault(row["owner"], 0)
        by_sprint[row["sprint"]][row["owner"]] += int(row["points"])
    for sprint, owners in by_sprint.items():
        print(f"{sprint}: {sum(owners.values())} pts  " + ", ".join(f"{o} {p}" for o, p in owners.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
