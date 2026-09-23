"""Repo-wide leak gate as a test.

The whole working tree (content, src, tests, docs, workflows) must contain
no email / phone / profile URL outside contacts.allowlist.yaml. Rendered
output is covered too, since the tree scan sees every text file — but unlike
the per-adapter assertions, this catches strays anywhere (fixtures, docs,
comments).

History is deliberately NOT covered here: private history still carries
pre-scrub identities by design until the public squash (see docs/PLAN.md
§7). Use scripts/check_contacts.py --mode history for that.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

import check_contacts


def test_working_tree_has_no_nonwhitelisted_contacts() -> None:
    repo = pathlib.Path(check_contacts.REPO)
    allow = check_contacts.load_allowlist(repo / "contacts.allowlist.yaml")
    violations = check_contacts.check(check_contacts.tree_candidates(), allow)
    assert not violations, "non-whitelisted contacts in working tree:\n" + "\n".join(
        f"  - {v}" for v in violations
    )
