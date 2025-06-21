# CarModPicker Backend

## Useful Commands

### Local Development

- `docker compose up -d`
  - to build the backend, the prod db, and the test db for unit tests
- `alembic upgrade head`
  - to get db schema up to date
- `pytest`
  - to trigger unit tests
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  - To start server outside of docker

## Database Migrations

### Local Development Migrations

#### Creating New Migrations

```bash
# Generate a new migration based on model changes
alembic revision --autogenerate -m "description of changes"

# Create an empty migration file
alembic revision -m "description of changes"
```

#### Running Migrations Locally

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Check current migration status
alembic current

# View migration history
alembic history --verbose

# Downgrade to a previous revision
alembic downgrade <revision_id>
```

### Kubernetes Deployment Migrations

The backend deployment includes an init container that automatically runs migrations before the application starts. However, for production environments, it's recommended to run migrations manually.

#### Automatic Migrations (Init Container)

- Migrations run automatically when the deployment starts
- No manual intervention required
- Suitable for development and simple deployments

#### Manual Migrations (Recommended for Production)

##### Using the Migration Script

```bash
cd kubernetes

# Check migration status
./migrate.sh status

# Run migrations manually
./migrate.sh run

# View migration history
./migrate.sh history

# Show help
./migrate.sh help
```

##### Using Kubernetes Jobs Directly

```bash
# Apply the migration job
kubectl apply -f kubernetes/migration-job.yaml

# Monitor the job
kubectl get jobs
kubectl logs job/db-migration-job

# Wait for completion
kubectl wait --for=condition=complete job/db-migration-job --timeout=300s

# Clean up
kubectl delete job db-migration-job
```

#### Migration Workflow for Production

1. **Create and test migrations locally**:

   ```bash
   alembic revision --autogenerate -m "your migration description"
   alembic upgrade head
   ```

2. **Build and push the new image**:

   ```bash
   docker build -t webbpulse/carmodpicker:backend-latest .
   docker push webbpulse/carmodpicker:backend-latest
   ```

3. **Run migrations in production**:

   ```bash
   cd kubernetes
   ./migrate.sh run
   ```

4. **Verify migration status**:

   ```bash
   ./migrate.sh status
   ```

5. **Deploy the application**:
   ```bash
   kubectl rollout restart deployment/carmodpicker-backend
   ```

#### Troubleshooting Migrations

##### Check Migration Status

```bash
# Check current database revision
kubectl run migration-check --rm -i --restart=Never \
  --image=webbpulse/carmodpicker:backend-latest \
  --command -- alembic current

# Check available migrations
kubectl run migration-heads --rm -i --restart=Never \
  --image=webbpulse/carmodpicker:backend-latest \
  --command -- alembic heads
```

##### View Migration Logs

```bash
# View init container logs
kubectl logs deployment/carmodpicker-backend -c db-migrate

# View migration job logs
kubectl logs job/db-migration-job
```

##### Rollback Migrations

```bash
# Create a rollback job
kubectl run migration-rollback --rm -i --restart=Never \
  --image=webbpulse/carmodpicker:backend-latest \
  --command -- alembic downgrade <previous_revision>
```

## Prerequisites

- `.env`
- `.env.test`
- k8s postgres secrets
- k8s backend secrets
- for docker debug with backend, configure a docker network with 'docker network create carmodpicker_network'
