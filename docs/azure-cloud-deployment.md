# Azure Cloud Deployment: Progress, Process, and Lessons Learned

Last updated: 2026-08-08

## 1. Deployment scope

This project uses a hybrid deployment model:

- Azure Container Apps hosts the public FastAPI service.
- Azure Database for PostgreSQL Flexible Server stores application data.
- Azure Container Registry (ACR) stores versioned Docker images.
- GitHub Actions currently provides CI; automated cloud deployment (CD) is still pending.
- Airflow remains in local Docker Compose as an orchestration demonstration.
- An Azure Container Apps scheduled Job runs the cloud ETL workflow without hosting the full Airflow stack in Azure.

This approach demonstrates cloud deployment while controlling portfolio-project cost and operational complexity.

## 2. Current architecture

```text
GitHub repository
       |
       v
GitHub Actions CI
  - Ruff
  - pytest
  - Alembic migrations
  - dbt build/tests
  - Docker image build

Developer machine / future CD workflow
       |
       v
Azure Container Registry
  banking-intelligence-api:<git-sha>
       |
       v
Azure Container Apps
  - public FastAPI API
  - scheduled ETL Job
       |
       v
Azure PostgreSQL Flexible Server
  ingestion / core / risk / analytics schemas

Local Docker Compose
  Airflow DAG: CSV ingestion -> risk evaluation -> dbt warehouse
```

## 3. Azure resources created

| Resource | Name | Status |
| --- | --- | --- |
| Resource group | `rg-banking-intelligence-dev` | Complete |
| Region | `newzealandnorth` | Selected |
| Cost budget | Resource-group budget | Complete |
| Container Registry | `bankingintelligencenzdev` | Complete |
| API image | `banking-intelligence-api:c310e39` | Pushed to ACR |
| PostgreSQL Flexible Server | `banking-intelligence-pg-nz-dev` | Complete |
| Application database | `banking_intelligence` | Complete |
| Database schema migrations | Alembic head `d22ee119ffee` | Applied |
| Container Apps environment | `cae-banking-intelligence-dev` | Complete |
| Managed identity | `id-banking-intelligence-api-dev` | Complete |
| CD Entra application | `app-banking-intelligence-cd-dev` | Created; RBAC and GitHub federation complete |
| GitHub Actions Azure IDs | Client, tenant, and subscription IDs | Explicit non-secret workflow configuration |
| ACR permission | `AcrPull` on the registry | Assigned |
| Container App | `ca-banking-intelligence-api-dev` | Created |
| Public endpoint verification | Health, readiness, authenticated query, and logs | Complete |
| Automated CD | GitHub Actions deployment workflow | Pending |
| Manual cloud ETL Job | `job-banking-etl-dev` | Complete and idempotency-tested |
| Scheduled cloud ETL Job | `job-banking-etl-scheduled-dev` | Complete; daily at `0 14 * * *` UTC |

Registered Azure providers include:

- `Microsoft.App`
- `Microsoft.OperationalInsights`
- `Microsoft.ContainerRegistry`
- `Microsoft.DBforPostgreSQL`
- `Microsoft.ManagedIdentity`

No subscription IDs, passwords, API keys, or connection strings should be stored in this document or committed to Git.

## 4. Deployment process completed so far

### Step 1: Prepare the Azure account

1. Install Azure CLI.
2. Sign in with `az login`.
3. Select the subscription.
4. choose `newzealandnorth` as the deployment region.
5. Create a resource group and a monthly budget.
6. Register the Azure resource providers required by the deployment.

Purpose: establish an isolated, tagged, and cost-monitored environment for the project.

### Step 2: Create Azure Container Registry

ACR was created with the Basic SKU. It stores deployable Docker artifacts; GitHub remains the source-code repository.

The current image uses the Git commit SHA as its tag:

```text
bankingintelligencenzdev.azurecr.io/banking-intelligence-api:c310e39
```

Using a commit SHA makes a deployment traceable to an exact source revision and allows rollback to an older image.

### Step 3: Provision managed PostgreSQL

The deployment created:

- PostgreSQL 16 Flexible Server
- Burstable `Standard_B1ms` compute
- 32 GB storage
- seven-day backup retention
- application database `banking_intelligence`
- a firewall rule for the current developer public IP
- access from Azure-hosted resources

Alembic then applied every database revision to the cloud database. `alembic current` confirmed revision `d22ee119ffee (head)`.

Purpose: the cloud API must use a durable database independent from the local Docker PostgreSQL container.

### Step 4: Build and publish the API image

The initial plan was to use `az acr build`, which uploads the source and asks ACR Tasks to build remotely. The subscription rejected ACR Tasks operations, so the working path became:

1. Build the image locally with Docker.
2. Tag it with the ACR login server and Git SHA.
3. Sign in with `az acr login`.
4. Push the image with `docker push`.
5. Verify the tag with `az acr repository show-tags`.

This is a valid manual deployment process. The final CD workflow should build and push from GitHub Actions instead.

### Step 5: Configure workload identity and registry access

A user-assigned managed identity was created and given the `AcrPull` role scoped to the registry.

Purpose: Container Apps can pull a private image without storing an ACR username and password in project files.

### Step 6: Create the Container Apps environment and API app

The Container Apps environment uses the Consumption workload profile. The API app was created with:

- external ingress
- target port `8000`
- minimum replicas `0`
- maximum replicas `1`
- private ACR image
- PostgreSQL configuration supplied through environment variables
- sensitive values supplied as Container Apps secrets
- the managed identity used for ACR access

Scaling to zero controls cost but means the first request after inactivity can have a cold-start delay.

### Step 7: Validate the public deployment

The public deployment was validated on 2026-08-08. The Container App hostname is:

```text
ca-banking-intelligence-api-dev.nicebeach-b97e3acc.newzealandnorth.azurecontainerapps.io
```

The active revision was `ca-banking-intelligence-api-dev--5ua9ef8`. Azure reported it as healthy; it initially had zero replicas because the development deployment intentionally scales to zero.

The validation results were:

| Check | Result |
| --- | --- |
| `GET /health` | HTTP 200, `{"status":"ok"}` |
| `GET /ready` | HTTP 200, `{"status":"ready"}` |
| `GET /transactions?limit=1&offset=0` with `X-API-Key` | HTTP 200; valid paginated response with no current transaction rows |
| Structured request logs | Confirmed method, path, status, duration, and a unique request ID for each request |
| Runtime errors | No application or database errors observed during validation |
| Cloud database migration | `alembic current` run inside the app container returned `d22ee119ffee (head)` |
| Secret injection | `POSTGRES_PASSWORD` uses `postgres-password`; `PLATFORM_API_KEY` uses `platform-api-key` |

The hostname was retrieved with:

```powershell
$appFqdn = az containerapp show `
  --name ca-banking-intelligence-api-dev `
  --resource-group rg-banking-intelligence-dev `
  --query properties.configuration.ingress.fqdn `
  --output tsv

$appFqdn
```

The public probes were verified with:

```powershell
curl "https://$appFqdn/health"
curl "https://$appFqdn/ready"
```

The authenticated endpoint can be called without printing the API key after loading it into the current process environment:

```powershell
$headers = @{ "X-API-Key" = $env:PLATFORM_API_KEY }
Invoke-RestMethod `
  -Uri "https://$appFqdn/transactions?limit=1&offset=0" `
  -Headers $headers
```

The successful readiness response, authenticated database-backed query, and in-container Alembic check jointly confirm that the deployed revision can use its PostgreSQL configuration and secret references to reach the migrated cloud database. Secret values were not printed or added to this document.

On 2026-08-08, the public FQDN retrieval, `GET /health`, `GET /ready`, authenticated transaction query, console-log inspection, in-container Alembic check, and secret-reference inspection were independently repeated from the developer PowerShell session. The hostname resolved successfully, `/health` returned `status: ok`, and `/ready` returned `status: ready`. `GET /transactions?limit=1&offset=0` accepted the locally loaded API key and returned a valid empty page with `total: 0`. The corresponding structured log recorded `http.request.completed`, a unique request ID, HTTP 200, and approximately 16 ms duration without exposing secrets. A separate request to the undefined root path returned the expected HTTP 404 and was not an application failure. Running `alembic current` inside the active revision connected with the PostgreSQL implementation and returned `d22ee119ffee (head)`. Configuration inspection confirmed that `POSTGRES_PASSWORD` references `postgres-password` and `PLATFORM_API_KEY` references `platform-api-key`, without reading either secret value. Together these checks confirmed public ingress, working secret injection, the migrated Azure PostgreSQL query path, and request observability.

### Step 8: Design the lightweight cloud ETL job

Azure Container Apps Jobs was selected as the preferred scheduler and execution environment. It fits the hybrid architecture because the existing Airflow deployment can remain a local orchestration demonstration while Azure runs a small, bounded batch container on a schedule.

The existing API image must not be reused unchanged for the batch job. It intentionally contains only application runtime dependencies and does not contain dbt, the `warehouse/` project, or the demo CSV input. The cloud ETL therefore needs a separate job image built from the same application source with the additional batch assets and dbt runtime.

The intended job sequence remains consistent with the Airflow DAG:

```text
idempotent CSV ingestion -> high-amount risk evaluation -> dbt build and tests
```

A read-only check against the cloud database on 2026-08-08 found that both `ingestion.source_systems` and `risk.risk_rules` were empty. Alembic correctly created their schemas but did not seed environment-specific source configuration or business-rule configuration. Creating the scheduled job before addressing this prerequisite would cause ingestion and risk evaluation to fail.

The implementation order is therefore:

1. Add an explicit, idempotent demo-configuration bootstrap command.
2. Use it to create or verify the `demo-csv` source system and active high-amount risk rule.
3. Build and locally verify a dedicated ETL job image containing dbt, `warehouse/`, and the demo CSV.
4. Push a versioned job image to ACR.
5. Create and manually execute an Azure Container Apps Job.
6. Add the schedule only after the manual execution succeeds end to end.

The packaged CSV is appropriate only as a deterministic portfolio demonstration of scheduling and idempotency. A production implementation would ingest a changing upstream object or API rather than repeatedly process a bundled sample file.

The core bootstrap function was implemented on 2026-08-08 in `banking_intelligence.bootstrap.demo_config`. It uses PostgreSQL upserts to create or refresh the `demo-csv` source and `HIGH_AMOUNT_DEMO` version 1 rule, returning both database IDs. It is exposed through `banking-intelligence bootstrap-demo-config` and runs both upserts in one transaction. Focused CLI, unit, and PostgreSQL integration tests passed, including repeated execution with stable IDs. The command has not yet been included in a deployed image or run against the cloud database.

The dbt runtime was also moved from the general `dev` dependency group into a dedicated `etl` group. This allows the future job image to install the application plus dbt without including pytest, Ruff, or other development-only tools. Refreshing `uv.lock` changed only the dependency-group assignment and did not upgrade resolved packages.

A dedicated `banking-intelligence-demo-job` entry point and `Dockerfile.etl` are now implemented locally. The entry point composes the existing bootstrap, CSV ingestion, high-amount risk, and dbt build stages in fail-fast order. Unit tests verify the order and propagation of the bootstrapped source-system and risk-rule IDs. The Dockerfile installs the application with only the `etl` dependency group and copies the dbt warehouse plus deterministic demo CSV. On 2026-08-08, the local image build completed successfully as `banking-intelligence-etl:dev`. A no-database smoke inspection confirmed the installed job entry point, dbt Core 1.12.0, dbt-postgres 1.11.0, the warehouse project, the demo CSV, and execution as the non-root `app` user. The ETL implementation was committed as Git revision `2212fc4`, and the same local image was tagged as `bankingintelligencenzdev.azurecr.io/banking-intelligence-etl:2212fc4`. The ACR-formatted tag establishes source-to-image traceability and tells Docker which registry and repository will receive the image; it does not duplicate the underlying local image layers. Local Docker authentication to `bankingintelligencenzdev` then completed successfully with `az acr login`. The ETL image was pushed successfully with digest `sha256:a2d69824c47dedc709ff8b59807b295cc83c8cdbac87e25088a4b0e6124a375f`; ACR reused shared layers already stored for the API image and uploaded the ETL-specific layers. An independent ACR tag query confirmed tag `2212fc4`, the same digest, and its registry creation timestamp. The existing user-assigned managed identity resource ID was retrieved into the local deployment session for reuse by the Job; the subscription-bearing ID is intentionally not recorded here. An Azure RBAC query confirmed that this identity still has `AcrPull` scoped to the registry. The API resource's non-secret PostgreSQL settings were then loaded into the local deployment session: the Azure PostgreSQL hostname, port 5432, database `banking_intelligence`, and application user `banking_admin`. Secret values were transferred directly into local variables without being displayed. The Manual Container Apps Job `job-banking-etl-dev` was created successfully with the ETL image, user-assigned identity, ACR managed-identity authentication, database configuration, and Job-scoped secret references. The local secret variables were cleared after creation. A read-only preflight confirmed Manual trigger mode, image tag `2212fc4`, 0.5 CPU, 1 GiB memory, 1,800-second timeout, retry limit 1, parallelism 1, completion count 1, user-assigned identity, managed-identity registry access, and both secret references. Azure accepted the first manual execution as `job-banking-etl-dev-vi9qprx`; its successful result is recorded below.

The first execution status was subsequently verified as `Succeeded`. It ran from approximately 00:54:48 UTC to 00:55:45 UTC, a duration of about 57 seconds. A direct `az containerapp job logs show` attempt installed the preview CLI extension but returned `No replicas found for execution` because the completed Job replica had already been cleaned up. This did not indicate a Job failure; the persistent logs were retrieved from the environment's Log Analytics workspace instead. They confirmed 54 successful dbt checks with zero warnings or errors, comprising three table models, two view models, and 49 data tests. The final Job summary reported ETL run ID 1, risk rule ID 1, three evaluated transactions, three inserted risk results, and one inserted alert. Public API verification then confirmed three transactions, one risk alert, and two daily analytics summary rows. This completed the first end-to-end cloud ETL validation. A second manual execution, `job-banking-etl-dev-k7johlt`, then completed with status `Succeeded` from approximately 01:11:43 UTC to 01:12:37 UTC, a duration of about 54 seconds. Its persistent logs again reported 54 passing dbt checks with zero warnings or errors. ETL run ID advanced to 2 while risk rule ID remained 1; all three transactions were evaluated, but zero new risk results and zero new alerts were inserted. Public API totals remained at three transactions, one alert, and two daily summary rows. This completed the end-to-end idempotency validation, so the Job is ready for a schedule.

The Scheduled Container Apps Job `job-banking-etl-scheduled-dev` was then created successfully from the same immutable ETL image, `banking-intelligence-etl:2212fc4`. It reuses the user-assigned managed identity for ACR access and has its own Job-scoped references to the PostgreSQL password and platform API key. Its cron expression is `0 14 * * *`, so Azure starts it daily at 14:00 UTC. This corresponds to approximately 02:00 in Auckland during NZST and 03:00 during NZDT; accepting this daylight-saving shift keeps the schedule simple and UTC-based. The already-tested Manual Job remains available for smoke tests and controlled backfills.

The core GitHub Actions CD workflow is now implemented in `.github/workflows/cd.yml`. It waits for a successful `CI` run on `main` (or a manual dispatch), checks out the tested revision, derives a Git-SHA image tag, authenticates with Azure OIDC, builds and pushes the API and ETL images, and updates the existing API Container App plus both ETL Jobs. It intentionally does not start either Job or recreate their trigger configuration. The deployment principal is the dedicated Microsoft Entra application `app-banking-intelligence-cd-dev`, following the standard GitHub-to-Azure workload identity pattern. No client secret was created. Its service principal has `AcrPush` on the registry plus `Container Apps Contributor` and `Container Apps Jobs Contributor` at the project resource-group scope. The `github-main-immutable` federated credential trusts only OIDC tokens issued for this repository's `main` branch and the Azure token-exchange audience. The client, tenant, and subscription IDs are non-secret identifiers stored explicitly in the workflow; authentication still requires GitHub's short-lived signed OIDC token. The initial `AADSTS700213` failures were ultimately traced to a one-digit transcription error in the immutable GitHub owner ID: the Azure subject contained `155221180`, while the token contained `15522180`. The public GitHub Check Runs annotations exposed the complete unmasked value and allowed the federation to be corrected precisely.

## 5. Difficulties encountered and what they taught

### No Azure subscription was initially available

Azure CLI authentication succeeded, but resource creation could not begin until an active subscription existed.

Lesson: identity authentication and billing/subscription authorization are separate concerns.

### Resource provider registration was asynchronous

Several services initially returned `Registering`. Resource creation had to wait until `registrationState` became `Registered`.

Lesson: cloud control-plane prerequisites are eventually consistent and should be checked explicitly.

### Azure CLI arguments differed from assumptions

Examples:

- database creation required `--name`, not `--database-name`
- this CLI version did not accept `--high-availability Disabled`; omitting the option produced the intended non-HA development server

Lesson: use `az <command> --help` and verify commands against the installed CLI version.

### A temporary database password was too weak and appeared in terminal output

The password must be rotated before the deployment is treated as complete. After rotation, update the corresponding Container App secret and create a new revision.

Lesson: generated secrets must meet service policies, must never be copied into Git or documentation, and should not be exposed in screenshots.

### Database firewall configuration was required

The local migration client needed a rule for the current public IP, while the cloud workload needed Azure-side access.

Lesson: a database can be healthy but unreachable because network authorization is a separate layer. For a production design, replace broad public access with private networking or more narrowly scoped rules.

### ACR remote build was unavailable

`az acr build` returned `TasksOperationsNotAllowed` for this registry/subscription. Logging into ACR did not enable the remote Tasks service.

Workaround: build locally and push with Docker.

Lesson: registry authentication, image storage, and managed remote-build capability are separate features.

### A locked pytest directory broke source packaging

The ACR upload process encountered `WinError 5` on `.pytest_tmp`. Adding ignore patterns did not remove the locked Windows filesystem object; ownership and ACL repair were needed before deletion.

Lesson: ignore files control build context selection but cannot repair host filesystem permissions. A clean repository directory and deterministic build context reduce deployment failures.

### Airflow and application dependencies conflicted

Airflow constrained FastAPI differently from the application. The Airflow image therefore needed dependency isolation rather than installing every application dependency into one shared environment.

Lesson: different deployable components should have separate runtime dependency boundaries.

### The Airflow DAG initially lacked an API key

The DAG task failed Pydantic settings validation because `PLATFORM_API_KEY` was absent inside the Airflow service containers. The Compose environment was corrected and the services were recreated without deleting their volumes. A later manual DAG run completed all three tasks successfully.

Lesson: a value present in the host `.env` is not automatically available inside every container; it must be mapped into the service environment.

### A one-digit immutable owner-ID error blocked OIDC

GitHub's log UI wrapped the immutable subject across lines, and the owner ID was initially transcribed as `155221180`. The actual signed token used `15522180`. Because Entra performs an exact, case-sensitive comparison, every token exchange correctly returned `AADSTS700213` even though the values appeared visually similar.

Resolution: query the public GitHub Check Runs annotations to obtain the complete presented assertion, then recreate the Entra application's federated credential with the exact issuer, subject, and audience. The deployment identifiers are safe to store as workflow configuration because they do not authenticate by themselves; GitHub must still mint a valid short-lived OIDC token.

Lesson: compare machine-readable claim values rather than transcribing wrapped screenshots. OIDC failures should be isolated across the token claims, selected client ID, Azure federation object, and control-plane propagation before replacing identity resources.

## 6. Security and cost actions still required

- Rotate the previously exposed PostgreSQL administrator password when the explicitly deferred security task is resumed.
- Update the Container App database-password secret after rotation.
- Confirm that `.env` is ignored and contains no committed secrets.
- Keep API keys and database passwords in Azure secrets or GitHub Actions secrets.
- Do not enable ACR admin credentials when managed identity can be used.
- Reassess the broad Azure-services PostgreSQL firewall rule after the demo works.
- Keep Container Apps at `min-replicas=0` and `max-replicas=1` for the portfolio environment.
- Retain the Azure budget alerts and review Cost Management while resources are running.
- Stop or delete paid resources when the demo is not needed; a budget alert does not automatically stop spending.

## 7. Remaining cloud work

### Required to finish the portfolio deployment

1. Commit the CD workflow and complete the first successful `CI -> CD` run.
2. Add deployment and rollback instructions to the main README.
3. Perform final end-to-end acceptance and clean up Azure resources when the demo is no longer needed.

The PostgreSQL administrator password rotation remains a known security action but was explicitly deferred on 2026-08-08. It must be completed before treating the environment as production-like or sharing further terminal screenshots.

### Optional production-strength improvements

- Infrastructure as Code with Bicep or Terraform
- private PostgreSQL networking
- Azure Key Vault references
- custom domain and managed TLS certificate
- alerting dashboards and log queries
- separate development and production environments
- automated database backup/restore exercise

## 8. What the candidate should be able to explain

- Why source code belongs in GitHub but Docker images belong in ACR.
- Why a Git SHA is a useful immutable image tag.
- Why Alembic migrations must run against the cloud database before the API starts using it.
- Why managed identity is safer than registry admin credentials.
- The difference between CI, image publication, and CD.
- Why `/health` and `/ready` answer different operational questions.
- Why the portfolio keeps Airflow local while hosting the public API and database in Azure.
- How secrets, firewall rules, and environment variables affect a containerized application.
- How to diagnose failures across source code, image build, registry, container runtime, network, and database layers.

## 9. Resume point

The public FastAPI deployment and cloud ETL path are complete. The Manual Job succeeded twice and demonstrated end-to-end idempotency; the Scheduled Job now runs daily at 14:00 UTC. Do not recreate these resources. The core CD workflow, dedicated Entra application, Azure RBAC roles, GitHub immutable `main` federation, and non-secret Azure identifiers are configured. The next step is completing the first successful `CI -> CD` run after federation propagation. PostgreSQL password rotation is explicitly deferred but remains documented as a security action.
