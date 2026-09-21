def test_admin_can_create_station(client, auth):
    headers = auth("admin@x.com", role="ADMIN")
    r = client.post("/api/stations", json={"name": "Bengaluru", "code": "BNC",
                                            "city": "Bengaluru", "state": "Karnataka"},
                    headers=headers)
    assert r.status_code == 201


def test_passenger_cannot_create_station(client, auth):
    headers = auth("pax@x.com", role="PASSENGER")
    r = client.post("/api/stations", json={"name": "Bengaluru", "code": "BNC",
                                            "city": "Bengaluru", "state": "Karnataka"},
                    headers=headers)
    assert r.status_code == 403


def test_duplicate_station_code(client, auth):
    headers = auth("admin@x.com", role="ADMIN")
    client.post("/api/stations", json={"name": "A", "code": "AAA", "city": "c", "state": "s"}, headers=headers)
    r = client.post("/api/stations", json={"name": "B", "code": "AAA", "city": "c", "state": "s"}, headers=headers)
    assert r.status_code == 409
