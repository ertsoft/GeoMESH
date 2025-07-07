from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from typing import Dict, List
import sqlite3
import json
from datetime import datetime
import uvicorn

app = FastAPI()

active_teams: Dict[str, List[WebSocket]] = {}
active_locations: Dict[str, Dict[str, dict]] = {}
DB_FILE = "teams.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id TEXT UNIQUE NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vector_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('point', 'line', 'polygon')),
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_team_to_db(team_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO teams (team_id) VALUES (?)", (team_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def save_vector_feature(team_id: str, user_id: str, vtype: str, data: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO vector_features (team_id, user_id, type, data) VALUES (?, ?, ?, ?)",
        (team_id, user_id, vtype, json.dumps(data))
    )
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()
    teams = []
    # preîncărcăm echipele deja create (dacă există) ca să avem chei în active_teams
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT team_id FROM teams")
    teams = [row[0] for row in c.fetchall()]
    conn.close()
    for team_id in teams:
        active_teams[team_id] = []
        active_locations[team_id] = {}

@app.post("/create_team/{team_id}")
async def create_team(team_id: str):
    if team_id in active_teams:
        return {"error": "Team already exists"}
    active_teams[team_id] = []
    active_locations[team_id] = {}
    save_team_to_db(team_id)
    return {"message": f"Team '{team_id}' created"}

@app.post("/join_team/{team_id}")
async def join_team(team_id: str, user_id: str = Query(...)):
    if team_id not in active_teams:
        raise HTTPException(status_code=404, detail="Team does not exist")
    if user_id in active_locations.get(team_id, {}):
        raise HTTPException(status_code=400, detail="user_id already exists in the team")
    return {"message": f"Joined team '{team_id}' with user_id '{user_id}'"}

@app.websocket("/ws/{team_id}")
async def websocket_endpoint(websocket: WebSocket, team_id: str):
    await websocket.accept()
    if team_id not in active_teams:
        active_teams[team_id] = []
        active_locations[team_id] = {}

    # primim mesajul de init
    init_data = await websocket.receive_json()
    user_id = init_data.get("user_id")
    if init_data.get("type") != "init" or not user_id:
        await websocket.close(code=1008)
        return

    # marcăm userul
    active_teams[team_id].append(websocket)
    active_locations[team_id][user_id] = {}

    # trimitem toate elementele existente
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT type, data FROM vector_features WHERE team_id = ?", (team_id,))
    existing = [{"type": row[0], "data": json.loads(row[1])} for row in c.fetchall()]
    conn.close()

    await websocket.send_json({"type": "team_elements", "data": existing})

    try:
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")
            data = msg.get("data")

            if mtype in ("point", "line", "polygon"):
                # salvăm în DB
                save_vector_feature(team_id, user_id, mtype, data)
                # broadcast la toți membri
                for member in active_teams[team_id]:
                    await member.send_json({"type": mtype, "data": data})
            # alte tipuri (location, get_elements) pot fi tratate aici...
    except WebSocketDisconnect:
        active_teams[team_id].remove(websocket)
        active_locations[team_id].pop(user_id, None)

@app.get("/team/{team_id}/features")
async def get_team_features(team_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, type, data, created_at FROM vector_features WHERE team_id = ?", (team_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "user_id": r[0],
            "type": r[1],
            "data": json.loads(r[2]),
            "created_at": r[3]
        } for r in rows
    ]


