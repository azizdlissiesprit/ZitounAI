# Backend · Spring Boot

**Owner:** Membre 2 · Spring Boot 4, Java 21, PostgreSQL (JPA + Flyway), Spring Security (JWT).

The core of the app: authentication, users, parcels, prediction history, and orchestration of the six AI services.

```
src/main/java/tn/zitouna/
├── config/          SecurityConfig (JWT), AiProperties (service URLs), OpenAPI
├── auth/            register / login, issues the JWT
├── user/            User entity, GET /api/users/me
├── parcel/          olive groves CRUD (owner-scoped)
├── history/         every AI call is saved here
├── common/          errors (ProblemDetail), pagination
└── ai/
    ├── AiServiceClient     base HTTP client: timeouts, 400/503 mapping
    ├── disease/            M1 client + controller
    ├── irrigation/         M2
    ├── cropyield/          M3
    ├── price/              M4
    ├── assistant/          M5 + ChatService (routes intents to M2/M3/M4)
    ├── trees/              M6
    └── orchestration/      HarvestPlanService: M6 -> M3 -> M4
```

## Run

```bash
docker compose up postgres            # from the repo root (+ the AI services you need)
./mvnw spring-boot:run                # Windows: mvnw.cmd spring-boot:run
```

Swagger UI: http://localhost:8080/swagger-ui.html — call `/api/auth/register`, copy the token, click *Authorize*.

Configuration is in `src/main/resources/application.properties`, overridable with env vars (`DB_URL`, `JWT_SECRET`, `AI_M1_URL`…).

## Test

```bash
./mvnw verify
```

Tests use an in-memory H2 database (`application-test.properties`), no PostgreSQL needed.

## Rules

- **Database changes = new Flyway migration** `src/main/resources/db/migration/V2__add_xxx.sql`. Never edit a migration that is already merged; Hibernate only validates the schema.
- Always fetch parcels with `ParcelService.getOwned(userId, parcelId)` so a user can never see another user's data.
- A new AI field: update the `…Result` record **and** [docs/api-contract.md](../docs/api-contract.md).
