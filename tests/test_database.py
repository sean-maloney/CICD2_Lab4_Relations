import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool,)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
  def override_get_db():
    db = TestingSessionLocal()
    try:
      yield db
    finally:
      db.close()
  app.dependency_overrides[get_db] = override_get_db
  with TestClient(app) as c:
# hand the client to the test
    yield c

def user_payload(name="User",email="user@atu.ie", age=20, sid="S9000001"):
    return{"name": name, "email": email, "age": age, "student_id":sid}


#USER PUT
#Put for student id and takes full user creat body

def test_update_user_ok(client):
    sid = "S9000101"
    email = f"u_put_old_{sid.lower()}@atu.ie"

    #create original user
    r_create = client.post("/api/users", json=user_payload(name="OldUser", email=email, age=20, sid=sid))
    assert r_create.status_code == 201

    #update keeping then unique fields like email and sid the same######################################
    r = client.put(f"/api/users/{sid}",json={"name": "NewUser", "email": email, "age":21,"student_id":sid},)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "NewUser"
    assert data["email"] == email
    assert data["age"] == 21
    assert data["student_id"] == sid


#user patch
#patch is keyed by student_id and allows partial fields.

def test_patch_user_ok(client):
    sid = "S9000102"
    email = f"u_patch_old_{sid.lower()}@atu.ie"

    r_create = client.post("/api/users",json=user_payload(name="OldUser", email=email, age=19, sid=sid))
    assert r_create.status_code == 201

    r = client.patch(f"/api/users/{sid}", json={"name": "PatchedUser", "age":20})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "PatchedUser"
    assert data["age"] == 20
    #unchanged
    assert data["email"] == email
    assert data["student_id"] == sid


#project put
#for projects we must creat an owner user first and use their returned id as owner_id

def test_update_project_ok(client):
    # owner
    owner_sid = "S9000201"
    owner_email = f"owner_put_{owner_sid.lower()}@atu.ie"
    u = client.post("/api/users", json=user_payload(name="owner",email=owner_email,age=22,sid=owner_sid))
    assert u.status_code == 201
    owner_id = u.json()["id"]

    p_create = client.post("/api/projects",json={"name":"OldProj","description":"old","owner_id":owner_id},)
    assert p_create.status_code == 201
    pid = p_create.json()["project_id"]

    r = client.put(f"/api/projects/{pid}",json={"name":"NewProj", "description":"new", "owner_id":owner_id},)

    assert r.status_code == 200
    data = r.json()
    assert data["project_id"] == pid
    assert data ["name"] == "NewProj"
    assert data ["description"] == "new"
    assert data ["owner_id"] == owner_id

#Project Patch
#partial update of a projects info

def test_patch_project_ok(client):
    # owner
    owner_sid = "S9000202"
    owner_email = f"owner_put_{owner_sid.lower()}@atu.ie"
    u = client.post("/api/users", json=user_payload(name="Owner2",email=owner_email,age=23,sid=owner_sid))
    assert u.status_code == 201
    owner_id = u.json()["id"]

    # create a project
    p_create = client.post("/api/projects",json={"name":"PatchProj","description":"init","owner_id":owner_id},)
    assert p_create.status_code == 201
    pid = p_create.json()["project_id"]

    #partial update 
    r = client.patch(f"/api/projects/{pid}", json={"description": "updated desc"})
    assert r.status_code == 200
    data = r.json()
    assert data["project_id"] == pid
    assert data["description"] == "updated desc"
    assert data["name"] == "PatchProj"