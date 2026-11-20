"""Reset the dinkdesk-test project to the known state the RLS tests expect.

Run before the test suite:  python seed.py && pytest -v

This script uses the SERVICE ROLE key, which bypasses RLS entirely. That is
correct for setup (we need to write rows no single user is allowed to write),
and exactly why the tests themselves must never use it.

Safe to re-run: it creates missing users, resets their passwords, and replaces
the test clients (and, via ON DELETE CASCADE, all their notes/assessments/
recommendations) with fresh copies.
"""
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Guard: a service-role script that deletes rows must never hit the wrong project.
TEST_PROJECT_REF = "mnhlpggvbuijyejwkkqh"  # dinkdesk-test
URL = os.environ["SUPABASE_URL"]
if TEST_PROJECT_REF not in URL:
    sys.exit(f"Refusing to seed: SUPABASE_URL is not the dinkdesk-test project ({TEST_PROJECT_REF}).")

admin = create_client(URL, os.environ["SUPABASE_SERVICE_ROLE_KEY"])
PASSWORD = os.environ["TEST_PASSWORD"]

# Same UIDs as the original project, so the constants in test_rls.py still match.
SAM = "44795a22-87da-43ad-9cf5-2670252ba744"
ALEX = "9feac428-ba8a-4964-a1e1-2440a3da9d40"
JAMIE = "a93ae219-d661-40b2-a726-760c7ce0d2e5"
RILEY = "2c62fe91-2eea-4520-a230-3a7acc9eedc3"

USERS = {  # login name (email is <name>@test.com) -> UID
    "coachsam": SAM,
    "coach-alex": ALEX,
    "client-jamie": JAMIE,
    "client-riley": RILEY,
}

JAMIE_CLIENT = "11111111-1111-1111-1111-111111111111"
RILEY_CLIENT = "22222222-2222-2222-2222-222222222222"


def seed_users():
    existing = {u.id for u in admin.auth.admin.list_users(per_page=1000)}
    for name, uid in USERS.items():
        if uid in existing:
            admin.auth.admin.update_user_by_id(uid, {"password": PASSWORD})
            print(f"  user {name}: exists, password reset")
        else:
            admin.auth.admin.create_user({
                "id": uid,
                "email": f"{name}@test.com",
                "password": PASSWORD,
                "email_confirm": True,
            })
            print(f"  user {name}: created")


def seed_data():
    # Deleting the clients cascades to their notes, assessments and recommendations,
    # which also removes anything a failed test run left behind.
    admin.table("clients").delete().in_("id", [JAMIE_CLIENT, RILEY_CLIENT]).execute()

    admin.table("clients").insert([
        {"id": JAMIE_CLIENT, "coach_id": SAM, "user_id": JAMIE, "name": "Jamie"},
        {"id": RILEY_CLIENT, "coach_id": ALEX, "user_id": RILEY, "name": "Riley"},
    ]).execute()

    admin.table("notes").insert([
        {"client_id": JAMIE_CLIENT, "body": "Jamie: soften the dink grip"},
        {"client_id": RILEY_CLIENT, "body": "Riley: work on third-shot drop"},
    ]).execute()

    admin.table("assessments").insert([
        {"client_id": JAMIE_CLIENT, "skill": "dink", "rating": 2},
        {"client_id": RILEY_CLIENT, "skill": "serve", "rating": 3},
    ]).execute()

    admin.table("recommendations").insert([
        {"client_id": JAMIE_CLIENT, "drill": "Cross-court dink rally", "focus_area": "Soft game"},
        {"client_id": RILEY_CLIENT, "drill": "Drop-shot ladder", "focus_area": "Transition"},
    ]).execute()
    print("  data: 2 clients, 2 notes, 2 assessments, 2 recommendations")


if __name__ == "__main__":
    print(f"Seeding {TEST_PROJECT_REF}...")
    seed_users()
    seed_data()
    print("Done.")
