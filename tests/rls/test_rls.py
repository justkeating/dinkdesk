import os
import pytest
from dotenv import load_dotenv
from supabase import create_client
from postgrest.exceptions import APIError

load_dotenv()

JAMIE_CLIENT = "11111111-1111-1111-1111-111111111111"
RILEY_CLIENT = "22222222-2222-2222-2222-222222222222"

def login(name):
    """Return a Supabase client signed in as e.g. 'client-jamie'."""
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    sb.auth.sign_in_with_password({
        "email": f"{name}@test.com",
        "password": os.environ["TEST_PASSWORD"],
    })
    return sb

def test_jamie_sees_only_own_notes():
    jamie = login("client-jamie")
    rows = jamie.table("notes").select("*").execute().data
    assert len(rows) == 1
    assert rows[0]["client_id"] == JAMIE_CLIENT

def test_jamie_cannot_update_own_rating():
    jamie = login("client-jamie")
    rows = jamie.table("assessments").select("*").execute().data
    assert rows[0]["rating"] == 2
    update_rows = jamie.table("assessments").update({"rating": 5}).eq("client_id", JAMIE_CLIENT).execute()
    assert update_rows.data == [] #no rows returned becuase update did not happen bc of rls 
    result = jamie.table("assessments").select("*").execute().data
    assert result[0]["rating"] == 2

def test_sam_cannot_insert_note_for_riley():
    sam = login("coachsam")
    with pytest.raises(APIError) as err:
        sam.table("notes").insert({"client_id": RILEY_CLIENT, "body": "test note Riley"}).execute()
    assert err.value.code == "42501"
    
def test_sam_can_create_and_delete_note_for_jamie():
    sam = login("coachsam")
    note_id = None
    try:
        result = sam.table("notes").insert({"client_id": JAMIE_CLIENT, "body": "test note Jamie - keep your head down"}).execute()
        assert len(result.data) == 1
        note_id = result.data[0]["id"]
        delete_result = sam.table("notes").delete().eq("id", note_id).execute()
        assert len(delete_result.data) == 1 
        remaining = sam.table("notes").select("id").eq("id", note_id).execute().data
        assert remaining == []      
    finally:
        if note_id:
            sam.table("notes").delete().eq("id", note_id).execute()
