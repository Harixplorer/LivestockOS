import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.alert import Alert, AlertSeverity
from app.models.animal import (
    Animal,
    AnimalGender,
    AnimalHealthStatus,
    AnimalSensorStatus,
)
from app.models.health_score import HealthScore
from app.models.reading import SensorReading
from app.models.sensor import Sensor
from app.models.user import User, UserRole


async def seed_database():
    print("Beginning database seed...")

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        existing_user = await session.execute(
            select(User).where(User.email == "maria@livestockos.io")
        )
        if existing_user.scalars().first():
            print("Database already contains seed data. Skipping duplicate seed.")
            return

        now = datetime.now(timezone.utc)
        print("1. Creating demo farmers...")

        # Farmer 1: Maria Garcia
        farmer1 = User(
            id=str(uuid.uuid4()),
            email="maria@livestockos.io",
            hashed_password=get_password_hash("password123"),
            full_name="Maria Garcia",
            phone_number="5551234567",
            role=UserRole.FARMER,
            farm_name="Sunrise Dairy Farm",
            village="Kondapur",
            district="Rangareddy",
            state="Telangana",
            is_active=True,
        )

        # Farmer 2: Ramesh Patel
        farmer2 = User(
            id=str(uuid.uuid4()),
            email="ramesh@livestockos.io",
            hashed_password=get_password_hash("password123"),
            full_name="Ramesh Patel",
            phone_number="9876543210",
            role=UserRole.FARMER,
            farm_name="Green Valley Ranch",
            village="Rampur",
            district="Meerut",
            state="Uttar Pradesh",
            is_active=True,
        )

        session.add_all([farmer1, farmer2])
        await session.flush()

        print("2. Registering IoT BLE sensors...")
        sensors = []
        for i in range(1001, 1016):
            sensor_code = f"LOS-{i}"
            sensor = Sensor(
                sensor_id=sensor_code,
                name="LivestockOS_Sensor",
                mac_address=f"AA:BB:CC:DD:{i%100:02X}:{i%99:02X}",
                battery_level=95 if i != 1005 else 22,
                is_active=True,
            )
            sensors.append(sensor)
            session.add(sensor)
        await session.flush()

        print("3. Seeding 14 cattle herd for Maria Garcia...")
        animals_data = [
            ("Gauri", "TAG-1001", "Gir", 3, AnimalGender.FEMALE, 380.0, AnimalHealthStatus.HEALTHY, "LOS-1001", 92, 38.6, 78, 26),
            ("Lakshmi", "TAG-1002", "Sahiwal", 4, AnimalGender.FEMALE, 420.0, AnimalHealthStatus.HEALTHY, "LOS-1002", 95, 38.5, 72, 28),
            ("Bella", "TAG-1003", "Holstein Friesian", 3, AnimalGender.FEMALE, 510.0, AnimalHealthStatus.HEALTHY, "LOS-1003", 88, 38.8, 68, 24),
            ("Nandi", "TAG-1004", "Murrah Buffalo", 5, AnimalGender.MALE, 560.0, AnimalHealthStatus.HEALTHY, "LOS-1004", 90, 38.4, 60, 25),
            ("Radha", "TAG-1005", "Gir", 2, AnimalGender.FEMALE, 340.0, AnimalHealthStatus.CRITICAL, "LOS-1005", 42, 40.8, 12, 6),
            ("Kamadhenu", "TAG-1006", "Red Sindhi", 4, AnimalGender.FEMALE, 410.0, AnimalHealthStatus.WARNING, "LOS-1006", 62, 39.7, 32, 14),
            ("Surabhi", "TAG-1007", "Tharparkar", 3, AnimalGender.FEMALE, 390.0, AnimalHealthStatus.WARNING, "LOS-1007", 65, 38.7, 18, 8),
            ("Meera", "TAG-1008", "Kankrej", 3, AnimalGender.FEMALE, 430.0, AnimalHealthStatus.HEALTHY, "LOS-1008", 86, 38.5, 65, 22),
            ("Ganga", "TAG-1009", "Rathi", 2, AnimalGender.FEMALE, 320.0, AnimalHealthStatus.HEALTHY, "LOS-1009", 94, 38.6, 74, 26),
            ("Yamuna", "TAG-1010", "Ongole", 4, AnimalGender.FEMALE, 450.0, AnimalHealthStatus.HEALTHY, "LOS-1010", 89, 38.7, 70, 24),
            ("Kalyani", "TAG-1011", "Deoni", 3, AnimalGender.FEMALE, 360.0, AnimalHealthStatus.HEALTHY, "LOS-1011", 91, 38.5, 72, 25),
            ("Daisy", "TAG-1012", "Jersey", 1, AnimalGender.FEMALE, 260.0, AnimalHealthStatus.NOT_MONITORED, None, None, None, None, None),
            ("Veera", "TAG-1013", "Hallikar", 2, AnimalGender.MALE, 400.0, AnimalHealthStatus.NOT_MONITORED, None, None, None, None, None),
            ("Shakti", "TAG-1014", "Amrit Mahal", 3, AnimalGender.MALE, 440.0, AnimalHealthStatus.NOT_MONITORED, None, None, None, None, None),
        ]

        created_animals = []
        for name, tag, breed, age, gender, weight, status, sensor_id, score, temp, act, rum in animals_data:
            animal = Animal(
                farmer_id=farmer1.id,
                tag_id=tag,
                name=name,
                breed=breed,
                age=age,
                age_months=age * 12,
                gender=gender,
                weight=weight,
                status=status,
                sensor_status=AnimalSensorStatus.ONLINE if sensor_id else AnimalSensorStatus.NOT_PAIRED,
                paired_sensor_id=sensor_id,
                paired_sensor_name="LivestockOS_Sensor" if sensor_id else None,
                sensor_paired_at=now - timedelta(days=7) if sensor_id else None,
                qr_code_payload=f"LIVESTOCKOS|{tag}|{name}",
                last_updated=now if sensor_id else None,
            )
            session.add(animal)
            created_animals.append((animal, score, temp, act, rum, sensor_id))

        await session.flush()

        # Update sensor pairing back-references
        for animal, _, _, _, _, sensor_id in created_animals:
            if sensor_id:
                for s in sensors:
                    if s.sensor_id == sensor_id:
                        s.paired_animal_id = animal.id

        print("4. Generating time-series readings and health scores...")
        for animal, score, temp, act, rum, sensor_id in created_animals:
            if sensor_id and temp is not None:
                # Add past 12 hourly readings
                for h in range(12, -1, -1):
                    reading_time = now - timedelta(hours=h)
                    r = SensorReading(
                        animal_id=animal.id,
                        temperature=temp + (0.1 if h % 2 == 0 else -0.1),
                        activity_score=act + (2 if h % 2 == 0 else -2),
                        behavior="Grazing" if act > 40 else "Idle",
                        rumination_mins=rum,
                        is_anomaly=(score < 70),
                        anomaly_score=-0.6 if score < 70 else 0.1,
                        recorded_at=reading_time,
                    )
                    session.add(r)

                # Add HealthScore
                hs = HealthScore(
                    animal_id=animal.id,
                    score=score,
                    temp_component=35 if temp < 39.5 else 10,
                    activity_component=30 if act > 40 else 10,
                    rumination_component=25 if rum > 15 else 10,
                    alert_penalty=20 if score < 70 else 0,
                    calculated_at=now,
                )
                session.add(hs)

        print("5. Generating alerts for herd...")
        # Radha: Critical High Fever
        radha = [a[0] for a in created_animals if a[0].name == "Radha"][0]
        alert_radha = Alert(
            farmer_id=farmer1.id,
            animal_id=radha.id,
            alert_type="HIGH_FEVER",
            severity=AlertSeverity.CRITICAL,
            message="Critical high fever (40.8°C) detected — immediate attention required.",
            is_resolved=False,
            created_at=now - timedelta(hours=2),
        )

        # Kamadhenu: Warning Fever
        kama = [a[0] for a in created_animals if a[0].name == "Kamadhenu"][0]
        alert_kama = Alert(
            farmer_id=farmer1.id,
            animal_id=kama.id,
            alert_type="FEVER",
            severity=AlertSeverity.WARNING,
            message="Elevated body temperature (39.7°C) detected — monitor closely.",
            is_resolved=False,
            created_at=now - timedelta(hours=4),
        )

        # Surabhi: Low Rumination
        surabhi = [a[0] for a in created_animals if a[0].name == "Surabhi"][0]
        alert_surabhi = Alert(
            farmer_id=farmer1.id,
            animal_id=surabhi.id,
            alert_type="LOW_RUMINATION",
            severity=AlertSeverity.WARNING,
            message="Abnormally low rumination (8 min/hr) detected.",
            is_resolved=False,
            created_at=now - timedelta(hours=6),
        )

        # Meera: Resolved historical alert
        meera = [a[0] for a in created_animals if a[0].name == "Meera"][0]
        alert_meera = Alert(
            farmer_id=farmer1.id,
            animal_id=meera.id,
            alert_type="INACTIVITY",
            severity=AlertSeverity.WARNING,
            message="Low activity level resolved after grazing.",
            is_resolved=True,
            resolved_at=now - timedelta(hours=1),
            created_at=now - timedelta(days=1),
        )

        session.add_all([alert_radha, alert_kama, alert_surabhi, alert_meera])

        await session.commit()
        print("\nSeed completed successfully!")
        print(f"Farmer 1: maria@livestockos.io / password123 (ID: {farmer1.id})")
        print(f"Farmer 2: ramesh@livestockos.io / password123 (ID: {farmer2.id})")
        print("Herd size: 14 animals seeded with readings, sensors, and alerts.")


if __name__ == "__main__":
    asyncio.run(seed_database())
