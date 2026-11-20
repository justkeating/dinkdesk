import os
import pytest
from dotenv import load_dotenv
from supabase import create_client
from postgrest.exceptions import APIError

load_dotenv()

JAMIE_CLIENT = "11111111-1111-1111-1111-111111111111"
RILEY_CLIENT = "22222222-2222-2222-2222-222222222222"
COACH_ALEX =   "9feac428-ba8a-4964-a1e1-2440a3da9d40"

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
    result = None
    with pytest.raises(APIError) as err:
        result = sam.table("notes").insert(
            {"client_id": RILEY_CLIENT, "body": "test note Riley"},
            returning="minimal").execute()
    assert err.value.code == "42501"
    #clean up if inserted, should raise flag if it is since policy would block this. Mutation testing here. leaving commented out 
   # if result:
    #    sam.table("notes").delete().eq("note_id", result.data[0]["note_id"]).execute()
    
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

@pytest.mark.parametrize("table_to_read",["notes", "assessments", "recommendations"])
def test_sam_cannot_read_rileys_notes(table_to_read):
    sam = login("coachsam")
    results = sam.table(table_to_read).select("*").eq("client_id", RILEY_CLIENT).execute().data
    assert results == []

def test_jamie_sees_only_own_client_row():
    jamie = login("client-jamie")
    result = jamie.table("clients").select("*").execute()
    assert len(result.data) == 1
    assert result.data[0]["id"] == JAMIE_CLIENT
    
def test_jamie_cannot_change_own_coach():
    jamie = login("client-jamie")
    result = jamie.table("clients").select("coach_id").execute()
    coach_id = result.data[0]["coach_id"]
    update_rows = jamie.table("clients").update({"coach_id": COACH_ALEX}).eq("id", JAMIE_CLIENT).execute()
    assert update_rows.data == [] #no rows returned becuase update did not happen bc of rls 
    result_check = jamie.table("clients").select("coach_id").execute()
    assert result_check.data[0]["coach_id"] == coach_id

def anon():
    """A client with the public key but no login, like a stranger hitting your API."""
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

@pytest.mark.parametrize("table", ["clients", "notes", "assessments", "recommendations"])
def test_anonymous_sees_nothing(table):
    rows = anon().table(table).select("*").execute().data
    assert rows == []