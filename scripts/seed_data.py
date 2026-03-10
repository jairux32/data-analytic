"""
Script para generar datos de prueba (seed data).

Genera 50 registros ficticios realistas de productores de cacao
con coordenadas GPS dentro de las provincias de Guayas y Los Ríos, Ecuador.
"""
import random
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.survey import Survey
from app.models.field_mapping import FieldMapping, DEFAULT_MAPPINGS


# Nombres comunes en Ecuador
FIRST_NAMES_MALE = [
    "Juan", "Carlos", "Luis", "Pedro", "Miguel", "José", "Antonio", "Francisco",
    "Javier", "Roberto", "Andrés", "Fernando", "Gabriel", "Daniel", "Ricardo",
    "Marco", "Édison", "Walter", "Édgar", "César"
]

FIRST_NAMES_FEMALE = [
    "María", "Carmen", "Ana", "Luisa", "Rosa", "Elena", "Patricia", "Laura",
    "Isabel", "Carmen", "Margarita", "Sandra", "Diana", "Claudia", "Andrea",
    "Natalia", "Carolina", "Gabriela", "Sofía", "Valentina"
]

LAST_NAMES = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez",
    "Ramírez", "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Reyes", "Cruz",
    "Morales", "Ortiz", "Gutiérrez", "Chávez", "Ramos"
]

# Provincias, cantones y parroquias de Guayas y Los Ríos
LOCATIONS = {
    "Guayas": {
        "Guayaquil": ["Garay", "Tarqui", "Manuela Cañizares", "El Oro", "XIV de Abril"],
        "Durán": ["El Recreo", "Eloy Alfaro", "La Joya"],
        "Samborondón": ["La Puntilla", "Samborondón", "San Ramón"],
        "Milagro": ["Milagro", "Chobo", "Roberto Astudillo"],
        "Yaguachi": ["Yaguachi", "San Jacinto", "Guayas"],
        "El Triunfo": ["El Triunfo", "El Rosario"],
        "Balzar": ["Balzar", "Palestina"],
        "Colimes": ["Colimes", "San José"],
        "Daule": ["Daule", "La Aurora", "Banano"],
        "Nobol": ["Nobol", "Dr. Camilo Ponce Enríquez"],
        "Palestina": ["Palestina", "Retamoso"],
        "Santa Lucía": ["Santa Lucía", "San Juan"],
        "Salinas": ["Salinas", "Anconcito", "Ballenita"],
    },
    "Los Ríos": {
        "Babahoyo": ["Babahoyo", "Cañada", "Pimocha", "San Juan"],
        "Quevedo": ["Quevedo", "Mocache", "San Carlos", "La Esperanza"],
        "Ventanas": ["Ventanas", "Chaco", "La Unión"],
        "Vinces": ["Vinces", "San Camilo", "Antonio Sotomayor"],
        "Buena Fe": ["Buena Fe", "San Jacinto", "Las Matas"],
        "Montalvo": ["Montalvo", "La Sofía"],
        "Jujan": ["Juján", "San José de Fe"],
        "Mocache": ["Mocache", "Quinsaloma"],
        "Palenque": ["Palenque", "San Carlos"],
        "Valencia": ["Valencia", "Los Almendros"],
    }
}

# Variedades de cacao
CACAO_VARIETIES = [
    "CCN-51", "Nacional", "Forastero", "Trinitario", "Criollo",
    "Ecuador", "Manabí", "Arriba", "Palencia"
]

EDUCATION_LEVELS = [
    "Primaria", "Secundaria", "Bachillerato", "Universidad", "Ninguno"
]

# Coordenadas aproximadas de las provincias (centros)
PROVINCE_CENTERS = {
    "Guayas": (-2.1894, -79.8890),
    "Los Ríos": (-1.5930, -79.4378)
}


def random_location():
    """Genera una ubicación aleatoria en Guayas o Los Ríos."""
    province = random.choice(list(LOCATIONS.keys()))
    canton = random.choice(list(LOCATIONS[province].keys()))
    parish = random.choice(LOCATIONS[province][canton])

    # Generar coordenadas cerca del centro de la provincia
    base_lat, base_lon = PROVINCE_CENTERS[province]
    lat = base_lat + random.uniform(-0.5, 0.5)
    lon = base_lon + random.uniform(-0.5, 0.5)

    return province, canton, parish, lat, lon


def generate_survey_data():
    """Genera datos de una encuesta ficticia."""
    # Determinar género
    gender = random.choice(["masculino", "femenino"])
    first_name = random.choice(FIRST_NAMES_MALE if gender == "masculino" else FIRST_NAMES_FEMALE)
    last_name = random.choice(LAST_NAMES)
    producer_name = f"{first_name} {last_name}"

    province, canton, parish, lat, lon = random_location()

    # Datos socioeconómicos
    age = random.randint(25, 70)
    education = random.choice(EDUCATION_LEVELS)
    farm_size = round(random.uniform(1, 50), 1)
    total_income = round(random.uniform(3000, 30000), 2)
    income_cacao = round(total_income * random.uniform(0.5, 0.9), 2)
    income_other = round(total_income - income_cacao, 2)

    access_water = random.choice(["sí", "no"])
    access_electricity = random.choice(["sí", "no"])
    access_health = random.choice(["sí", "no"])

    # Datos agronómicos
    varieties = random.sample(CACAO_VARIETIES, k=random.randint(1, 3))
    cacao_varieties = " ".join(varieties)
    yield_per_ha = round(random.uniform(0.5, 8), 1)

    use_fertilizers = random.choice(["sí", "no", "sí"])
    use_organic = random.choice(["sí", "no", "no"])
    use_none = "sí" if use_fertilizers == "no" and use_organic == "no" else "no"

    post_harvest = random.sample(
        ["fermentación", "secado", "clasificado", "almacenamiento"],
        k=random.randint(1, 3)
    )
    post_harvest_practices = " ".join(post_harvest)

    member_org = random.choice(["sí", "no", "sí"])
    org_name = f"Asociación de Productores {random.choice(['Cacaoteros', 'Agrícolas', 'Rurales'])} {canton}" if member_org == "sí" else None
    tech_assistance = random.choice(["sí", "no", "sí"])

    # Datos ambientales
    forest_coverage = round(random.uniform(5, 80), 1)
    conservation = random.sample(
        ["reforestación", "cercos vivos", "manejo integrado", "protección de fuentes", "no aplica"],
        k=random.randint(1, 2) if random.random() > 0.3 else 1
    )
    conservation_practices = " ".join([c for c in conservation if c != "no aplica"])

    protected_area = random.choice(["sí", "no", "no"])
    water_sources = random.sample(
        ["río", "quebrada", "pozo", "acequia", "represa"],
        k=random.randint(1, 2)
    )
    water_sources_on_farm = " ".join(water_sources)

    risks = random.sample(
        ["sequía", "inundación", "deforestación", "plagas", "enfermedades"],
        k=random.randint(1, 2)
    )
    environmental_risks = " ".join(risks)

    # Datos de gobernanza
    actors = random.sample(
        ["MAG", "PNG", "GAD Provincial", "Cooperativas", "ONGs", "Bancos"],
        k=random.randint(1, 3)
    )
    institutional_actors = " ".join(actors)

    access_credit = random.choice(["sí", "no", "sí"])

    certs = random.sample(
        ["UTZ", "Rainforest", "Orgánico", "Fairtrade", "ninguna"],
        k=random.randint(1, 2)
    )
    certifications = " ".join([c for c in certs if c != "ninguna"]) if random.random() > 0.5 else None

    participation = random.sample(
        ["asambleas", "toma decisiones", "capacitaciones", "ninguna"],
        k=random.randint(1, 2)
    )
    participation_in_decision_making = " ".join([p for p in participation if p != "ninguna"]) if random.random() > 0.3 else None

    # UUID único
    kobo_uuid = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

    return {
        "kobo_uuid": kobo_uuid,
        "asset_uid": "test-asset-001",
        "submission_date": datetime.now() - timedelta(days=random.randint(1, 365)),
        "producer_name": producer_name,
        "gender": gender,
        "age": age,
        "education_level": education,
        "province": province,
        "canton": canton,
        "parish": parish,
        "farm_size_hectares": farm_size,
        "total_income": total_income,
        "income_from_cacao": income_cacao,
        "income_from_other": income_other,
        "access_to_water": access_water,
        "access_to_electricity": access_electricity,
        "access_to_health": access_health,
        "cacao_varieties": cacao_varieties,
        "yield_quintals_per_ha": yield_per_ha,
        "use_of_fertilizers": use_fertilizers,
        "use_of_organic": use_organic,
        "use_of_none": use_none,
        "post_harvest_practices": post_harvest_practices,
        "member_of_organization": member_org,
        "organization_name": org_name,
        "access_to_technical_assistance": tech_assistance,
        "forest_coverage_percent": forest_coverage,
        "conservation_practices": conservation_practices,
        "protected_area_nearby": protected_area,
        "water_sources_on_farm": water_sources_on_farm,
        "environmental_risks_perceived": environmental_risks,
        "institutional_actors": institutional_actors,
        "access_to_credit": access_credit,
        "certifications": certifications,
        "participation_in_decision_making": participation_in_decision_making,
        "gps_latitude": lat,
        "gps_longitude": lon,
        "gps_accuracy": round(random.uniform(5, 30), 1),
    }


def seed_database():
    """Ejecuta el seed de la base de datos."""
    db = SessionLocal()

    try:
        # Verificar si ya hay datos
        existing_surveys = db.query(Survey).count()
        if existing_surveys > 0:
            print(f"Ya existen {existing_surveys} encuestas en la base de datos.")
            response = input("¿Desea continuar y agregar más datos? (s/n): ")
            if response.lower() != "s":
                print("Seed cancelado.")
                return

        # Crear usuario admin si no existe
        admin = db.query(User).filter(User.email == "admin@admin.com").first()
        if not admin:
            admin = User(
                email="admin@admin.com",
                password_hash=get_password_hash("admin123"),
                full_name="Administrador",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            print("Usuario admin creado: admin@admin.com / admin123")

        # Crear mapeos de campos por defecto
        for kobo_name, internal_name, field_type, category in DEFAULT_MAPPINGS:
            existing = db.query(FieldMapping).filter(
                FieldMapping.kobo_field_name == kobo_name
            ).first()
            if not existing:
                mapping = FieldMapping(
                    kobo_field_name=kobo_name,
                    internal_field_name=internal_name,
                    field_type=field_type,
                    category=category,
                )
                db.add(mapping)

        # Generar encuestas
        print("\nGenerando 50 encuestas ficticias...")
        for i in range(50):
            data = generate_survey_data()
            survey = Survey(**data)
            db.add(survey)

            if (i + 1) % 10 == 0:
                print(f"  {i + 1} encuestas generadas...")

        db.commit()
        print(f"\nSeed completado: 50 encuestas creadas exitosamente!")
        print(f"Total de encuestas en la base de datos: {db.query(Survey).count()}")

    except Exception as e:
        db.rollback()
        print(f"Error durante el seed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("SEED DE DATOS DE PRUEBA")
    print("Diagnóstico Socioambiental Cacaotero - Guayas & Los Ríos")
    print("=" * 60)
    seed_database()
