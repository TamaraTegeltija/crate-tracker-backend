from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey

from database import Base


class Scan(Base):

    # Ovo ce biti ime tabele u PostgreSQL-u.
    __tablename__ = "scans"

    # Jedinstveni ID jednog SuperNode scan ciklusa.
    # Koristicemo tvoj ESP32 message_id kao primary key.
    message_id = Column(
        String,
        primary_key=True,
        index=True
    )

    # MAC adresa SuperNode-a.
    device_id = Column(
        String,
        nullable=False
    )

    # Verzije hardvera i softvera.
    hw_version = Column(
        String,
        nullable=False
    )

    sw_version = Column(
        String,
        nullable=False
    )

    # Timestamp skeniranja.
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False
    )

    # DHT11 podaci.
    # nullable=True jer senzor nekada moze da ne vrati vrednost.
    temperature = Column(
        Float,
        nullable=True
    )

    humidity = Column(
        Float,
        nullable=True
    )

class WifiNetwork(Base):

    __tablename__ = "wifi_networks"

    # Interni ID reda u bazi.
    # PostgreSQL/SQLAlchemy ce ga automatski povecavati.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Govori kom scan-u ova Wi-Fi mreza pripada.
    scan_message_id = Column(
        String,
        ForeignKey("scans.message_id"),
        nullable=False
    )

    ssid = Column(
        String,
        nullable=False
    )

    bssid = Column(
        String,
        nullable=False
    )

    rssi = Column(
        Integer,
        nullable=False
    )

    channel = Column(
        Integer,
        nullable=False
    )


class BleNode(Base):

    __tablename__ = "ble_nodes"

    # Interni ID reda u bazi.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Povezuje node sa konkretnim scan ciklusom.
    scan_message_id = Column(
        String,
        ForeignKey("scans.message_id"),
        nullable=False
    )

    # BLE MAC adresa noda.
    mac = Column(
        String,
        nullable=False
    )

    rssi = Column(
        Integer,
        nullable=False
    )

    # Npr. GAMARS537.
    data = Column(
        String,
        nullable=False
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False
    )