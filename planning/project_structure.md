```text
DriveNow/
├── .git/
├── .gitignore
├── docker-compose.yml
├── infra/
│   ├── postgres_init.sql
│   └── prometheus.yml
├── md/
│   ├── N-EXERCISE.md
│   ├── exercise_architecture.md
│   ├── project_implementation_plan.md
│   ├── project_structure.md
│   ├── rental_ser_example.md
│   └── stages/
│       ├── s1_dependencies.md
│       ├── s2_config.md
│       ├── s3_infrastructure.md
│       ├── s4_db.md
│       └── s5_vehicle_service.md
├── gateway_service/
│   ├── .venv/
│   ├── pyproject.toml
│   └── src/
│       ├── config.py
│       └── logger.py
├── rental_service/
│   ├── .venv/
│   ├── pyproject.toml
│   └── src/
│       ├── config.py
│       ├── logger.py
│       └── db/
│           ├── __init__.py
│           ├── database.py
│           └── models.py
├── return_service/
│   ├── .venv/
│   ├── pyproject.toml
│   └── src/
│       ├── config.py
│       └── logger.py
└── vehicle_service/
    ├── .env
    ├── .venv/
    ├── pyproject.toml
    ├── src/
    │   ├── config.py
    │   ├── logger.py
    │   ├── main.py
    │   ├── schemas.py
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── database.py
    │   │   ├── enums.py
    │   │   └── models.py
    │   └── routers/
    │       ├── __init__.py
    │       └── cars.py
    └── tests/
        ├── __init__.py
        └── test_cars.py
```
