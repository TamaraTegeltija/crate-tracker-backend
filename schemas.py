from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# ============================================================
# WIFI NETWORK
# ============================================================

class WifiNetworkCreate(BaseModel):

    ssid: str
    bssid: str
    rssi: int
    channel: int


# ============================================================
# SUPERNODE
# ============================================================

class SuperNodeCreate(BaseModel):

    # Literal znaci:
    # ovo polje sme da bude samo "supernode".
    type: Literal["supernode"]

    device_id: str
    hw_version: str
    sw_version: str

    message_id: str
    timestamp: datetime

    temperature: float | None = None
    humidity: float | None = None

    # SuperNode moze da posalje vise Wi-Fi mreza.
    wifi: list[WifiNetworkCreate] = Field(
        default_factory=list,
        max_length=10
    )


# ============================================================
# BLE NODE
# ============================================================

class BleNodeCreate(BaseModel):

    type: Literal["node"]

    # ref pokazuje na message_id SuperNode scan-a.
    ref: str

    # Ovo je BLE MAC adresa.
    id: str

    rssi: int

    # Npr. GAMARS537.
    data: str

    timestamp: datetime


# ============================================================
# JEDAN ELEMENT ESP32 JSON NIZA
# ============================================================

PayloadItem = Annotated[
    Union[
        SuperNodeCreate,
        BleNodeCreate
    ],
    Field(discriminator="type")
]