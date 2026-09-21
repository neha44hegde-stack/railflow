from datetime import date, timedelta


def setup_train(client, admin):
    s1 = client.post("/api/stations", json={"name": "A", "code": "AAA", "city": "c", "state": "s"}, headers=admin).get_json()["station"]
    s2 = client.post("/api/stations", json={"name": "B", "code": "BBB", "city": "c", "state": "s"}, headers=admin).get_json()["station"]
    t = client.post("/api/trains", json={"train_number": "10001", "train_name": "T1", "train_type": "Express"}, headers=admin).get_json()["train"]
    client.post(f"/api/trains/{t['id']}/route",
                json={"station_id": s1["id"], "stop_number": 1, "departure_time": "08:00"}, headers=admin)
    client.post(f"/api/trains/{t['id']}/route",
                json={"station_id": s2["id"], "stop_number": 2, "arrival_time": "10:00"}, headers=admin)
    client.post(f"/api/trains/{t['id']}/classes",
                json={"class_name": "Sleeper", "total_seats": 5, "fare": 100, "seat_prefix": "S"}, headers=admin)
    return s1, s2, t


def test_booking_decreases_availability_and_cancel_restores(client, auth):
    admin = auth("admin@x.com", role="ADMIN")
    pax   = auth("pax@x.com", role="PASSENGER")
    s1, s2, t = setup_train(client, admin)
    jd = (date.today() + timedelta(days=1)).isoformat()

    r = client.get(f"/api/trains/search?source={s1['id']}&destination={s2['id']}&date={jd}&class=Sleeper")
    assert r.status_code == 200
    assert r.get_json()["trains"][0]["classes"][0]["available_seats"] == 5

    r = client.post("/api/bookings", json={
        "train_id": t["id"], "journey_date": jd,
        "source_station_id": s1["id"], "destination_station_id": s2["id"],
        "class_name": "Sleeper",
        "passengers": [{"name": "P1", "age": 30, "gender": "MALE"}],
    }, headers=pax)
    assert r.status_code == 201
    booking = r.get_json()["booking"]

    r = client.get(f"/api/trains/search?source={s1['id']}&destination={s2['id']}&date={jd}&class=Sleeper")
    assert r.get_json()["trains"][0]["classes"][0]["available_seats"] == 4

    r = client.post(f"/api/bookings/{booking['id']}/cancel", headers=pax)
    assert r.status_code == 200

    r = client.get(f"/api/trains/search?source={s1['id']}&destination={s2['id']}&date={jd}&class=Sleeper")
    assert r.get_json()["trains"][0]["classes"][0]["available_seats"] == 5


def test_user_isolation(client, auth):
    admin = auth("admin@x.com", role="ADMIN")
    a = auth("a@x.com", role="PASSENGER")
    b = auth("b@x.com", role="PASSENGER")
    s1, s2, t = setup_train(client, admin)
    jd = (date.today() + timedelta(days=1)).isoformat()

    r = client.post("/api/bookings", json={
        "train_id": t["id"], "journey_date": jd,
        "source_station_id": s1["id"], "destination_station_id": s2["id"],
        "class_name": "Sleeper",
        "passengers": [{"name": "P1", "age": 30, "gender": "MALE"}],
    }, headers=a)
    bid = r.get_json()["booking"]["id"]

    r = client.get(f"/api/bookings/{bid}", headers=b)
    assert r.status_code == 403


def test_overbooking_prevented(client, auth):
    admin = auth("admin@x.com", role="ADMIN")
    pax   = auth("pax@x.com", role="PASSENGER")
    s1, s2, t = setup_train(client, admin)
    jd = (date.today() + timedelta(days=1)).isoformat()
    # capacity 5 -> try to book 6
    r = client.post("/api/bookings", json={
        "train_id": t["id"], "journey_date": jd,
        "source_station_id": s1["id"], "destination_station_id": s2["id"],
        "class_name": "Sleeper",
        "passengers": [{"name": f"P{i}", "age": 20, "gender": "MALE"} for i in range(6)],
    }, headers=pax)
    assert r.status_code in (400, 409)
