from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.offer import Offer
from app.models.application import Application, ApplicationStatus


def seed_if_empty(db: Session):
    exists = db.query(User).first()
    if exists:
        return

    staff = User(
        name="Juan Pérez",
        email="juan.perez@uniandes.edu.co",
        password_hash=hash_password("123456"),
        department="Ingeniería",
        language="es",
        is_dark_mode=False,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)

    now = datetime.now()
    offer1 = Offer(
        staff_id=staff.id,
        title="Apoyo Biblioteca",
        description="Apoyo en tareas operativas y atención básica durante eventos.",
        category="Administrativo",
        value_cop=80000,
        duration_hours=4,
        is_on_site=True,
        date_time=now + timedelta(days=2),
    )
    offer2 = Offer(
        staff_id=staff.id,
        title="Asistente Laboratorio",
        description="Ayuda con inventario y preparación de materiales para prácticas.",
        category="Ingeniería",
        value_cop=120000,
        duration_hours=6,
        is_on_site=True,
        date_time=now + timedelta(days=5),
    )
    db.add_all([offer1, offer2])
    db.commit()
    db.refresh(offer1)
    db.refresh(offer2)

    apps = [
        Application(
            offer_id=offer1.id,
            student_name="Ana Gómez",
            student_email="ana.gomez@uniandes.edu.co",
            status=ApplicationStatus.pending,
        ),
        Application(
            offer_id=offer1.id,
            student_name="Mateo Ríos",
            student_email="mateo.rios@uniandes.edu.co",
            status=ApplicationStatus.accepted,
        ),
        Application(
            offer_id=offer2.id,
            student_name="Laura Díaz",
            student_email="laura.diaz@uniandes.edu.co",
            status=ApplicationStatus.rejected,
        ),
    ]
    db.add_all(apps)
    db.commit()
