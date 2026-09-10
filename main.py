from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import engine, Base, get_db

import models
import schemas


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Crate Tracker backend is running"
    }


@app.get("/db-test")
def test_database():

    # Otvaramo konekciju prema PostgreSQL-u.
    with engine.connect() as connection:

        # SELECT 1 je najjednostavniji moguci SQL upit.
        # Ne cita nikakvu tabelu.
        # Samo proveravamo da PostgreSQL odgovara.
        result = connection.execute(
            text("SELECT 1")
        )

        value = result.scalar()

    return {
        "database": "connected",
        "result": value
    }

@app.post(
    "/api/scans",
    status_code=201
)
def create_scan(
    payload: list[schemas.PayloadItem],
    db: Session = Depends(get_db)
):

    # ========================================================
    # 1. PRONADJI SUPERNODE OBJEKAT
    # ========================================================

    supernodes = [
        item
        for item in payload
        if isinstance(
            item,
            schemas.SuperNodeCreate
        )
    ]


    nodes = [
        item
        for item in payload
        if isinstance(
            item,
            schemas.BleNodeCreate
        )
    ]


    # Ocekujemo tacno jedan SuperNode po scan request-u.
    if len(supernodes) != 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "Payload must contain exactly "
                "one supernode."
            )
        )


    supernode = supernodes[0]


    # Maksimalno 20 BLE nodova.
    if len(nodes) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum number of BLE nodes is 20."
        )


    # ========================================================
    # 2. PROVERI REF KOD SVIH NODOVA
    # ========================================================

    for node in nodes:

        if node.ref != supernode.message_id:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Node {node.id} has invalid ref."
                )
            )


    # ========================================================
    # 3. NAPRAVI SCAN
    # ========================================================

    new_scan = models.Scan(
        message_id=supernode.message_id,
        device_id=supernode.device_id,
        hw_version=supernode.hw_version,
        sw_version=supernode.sw_version,
        timestamp=supernode.timestamp,
        temperature=supernode.temperature,
        humidity=supernode.humidity
    )


    try:

        db.add(new_scan)

        db.flush()


        # ====================================================
        # 4. WIFI MREZE
        # ====================================================

        for wifi in supernode.wifi:

            new_wifi = models.WifiNetwork(
                scan_message_id=supernode.message_id,
                ssid=wifi.ssid,
                bssid=wifi.bssid,
                rssi=wifi.rssi,
                channel=wifi.channel
            )

            db.add(new_wifi)


        # ====================================================
        # 5. BLE NODOVI
        # ====================================================

        for node in nodes:

            new_node = models.BleNode(
                scan_message_id=supernode.message_id,

                # U ESP32 JSON-u polje se zove "id",
                # dok se u bazi kolona zove "mac".
                mac=node.id,

                rssi=node.rssi,
                data=node.data,
                timestamp=node.timestamp
            )

            db.add(new_node)


        # ====================================================
        # 6. COMMIT SVEGA
        # ====================================================

        db.commit()


    except IntegrityError:

        # Ako PostgreSQL odbije transakciju,
        # vracamo je unazad.
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Scan with this message_id "
                "already exists."
            )
        )


    except Exception:

        # Ako se desi neka druga greska,
        # takodje ne zelimo polovicno sacuvane podatke.
        db.rollback()

        raise


    # ========================================================
    # 7. ODGOVOR ESP32-U
    # ========================================================

    return {
        "status": "success",
        "message": "Scan saved",
        "message_id": supernode.message_id,
        "wifi_networks_saved": len(supernode.wifi),
        "ble_nodes_saved": len(nodes)
    }
# ============================================================
# GET ALL SCANS
# ============================================================

@app.get("/api/scans")
def get_scans(
    db: Session = Depends(get_db)
):

    # Uzimamo sve scanove iz baze.
    # Najnoviji ide prvi.
    scans = (
        db.query(models.Scan)
        .order_by(models.Scan.timestamp.desc())
        .all()
    )

    result = []

    for scan in scans:

        # ----------------------------------------------------
        # WIFI MREZE KOJE PRIPADAJU OVOM SCAN-U
        # ----------------------------------------------------

        wifi_networks = (
            db.query(models.WifiNetwork)
            .filter(
                models.WifiNetwork.scan_message_id
                == scan.message_id
            )
            .all()
        )


        wifi_result = []

        for wifi in wifi_networks:

            wifi_result.append(
                {
                    "ssid": wifi.ssid,
                    "bssid": wifi.bssid,
                    "rssi": wifi.rssi,
                    "channel": wifi.channel
                }
            )


        # ----------------------------------------------------
        # BLE NODOVI KOJI PRIPADAJU OVOM SCAN-U
        # ----------------------------------------------------

        ble_nodes = (
            db.query(models.BleNode)
            .filter(
                models.BleNode.scan_message_id
                == scan.message_id
            )
            .all()
        )


        ble_result = []

        for node in ble_nodes:

            ble_result.append(
                {
                    "id": node.mac,
                    "rssi": node.rssi,
                    "data": node.data,
                    "timestamp": node.timestamp
                }
            )


        # ----------------------------------------------------
        # CEO SCAN
        # ----------------------------------------------------

        result.append(
            {
                "message_id": scan.message_id,
                "device_id": scan.device_id,
                "hw_version": scan.hw_version,
                "sw_version": scan.sw_version,
                "timestamp": scan.timestamp,
                "temperature": scan.temperature,
                "humidity": scan.humidity,

                "wifi": wifi_result,
                "ble_nodes": ble_result
            }
        )


    return result