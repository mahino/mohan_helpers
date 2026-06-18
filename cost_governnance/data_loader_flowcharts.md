# Data Loader Success Flowcharts

## End-to-End Flow

```mermaid
flowchart TD
    A[Start: Trigger data-loader job] --> B[cron-nx-cg-data-loader Job created in ncm-cg]
    B --> C[data-loader Pod starts]
    C --> D[Read backfill config/state from Postgres<br/>pod: cg-pg-1 in ntnx-ncm-datastore]

    D --> E[Process NX_ROUTINE_WORKFLOW]
    E --> F[Discover backfill jobs to run]

    F --> G1[Process CLUSTER_CONFIG]
    F --> G2[Process CATEGORIES_CONFIG]
    F --> G3[Process VM_CONFIG]
    F --> G4[Process CLUSTER_HARDWARE_CONFIG]
    F --> G5[Process VM_RECOVERY_POINT_CONFIG]

    G1 --> H1[Fetch data for date ranges]
    G2 --> H2[Fetch data for date ranges]
    G3 --> H3[Fetch data for date ranges]
    G4 --> H4[Fetch data for date ranges]
    G5 --> H5[Fetch data for date ranges]

    H1 --> I1[Drop old partition data]
    H2 --> I2[Drop old partition data]
    H3 --> I3[Drop old partition data]
    H4 --> I4[Drop old partition data]
    H5 --> I5[Drop old partition data]

    I1 --> J1[Write metrics to ClickHouse tables]
    I2 --> J2[Write metrics to ClickHouse tables]
    I3 --> J3[Write metrics to ClickHouse tables]
    I4 --> J4[Write metrics to ClickHouse tables]
    I5 --> J5[Write metrics to ClickHouse tables]

    J1 --> K1["Update PG backfill status<br/>Service (CLUSTER_CONFIG)"]
    J2 --> K2["Update PG backfill status<br/>Service (CATEGORIES_CONFIG)"]
    J3 --> K3["Update PG backfill status<br/>Service (VM_CONFIG)"]
    J4 --> K4["Update PG backfill status<br/>Service (CLUSTER_HARDWARE_CONFIG)"]
    J5 --> K5["Update PG backfill status<br/>Service (VM_RECOVERY_POINT_CONFIG)"]

    E --> K0["Update PG backfill status<br/>Service (NX_ROUTINE_WORKFLOW)"]

    K0 --> L[Temp-file cleanup per executor]
    K1 --> L[Temp-file cleanup per executor]
    K2 --> L
    K3 --> L
    K4 --> L
    K5 --> L

    L --> M[Completion logs emitted:<br/>... completed successfully]
    M --> N[Job marked complete]

    N --> P[Post-completion workflow monitoring window]
    P --> Q1[Precalculate worker starts TCO job]
    Q1 --> Q2[Cluster TCO + RAM cost recalculation]
    Q2 --> Q3[Inventory manager updates cost configs]
    Q3 --> O[End: next iteration]
```

## Pod-to-Pod Swimlane

```mermaid
flowchart LR
    subgraph A["Lane: Trigger / Data-loader Pod (ncm-cg)"]
        A1[Manual/Scheduled Trigger] --> A2[Create Job: cron-nx-cg-data-loader]
        A2 --> A3[Pod starts: nx-cg-data-loader-*]
        A3 --> A4[Process NX_ROUTINE_WORKFLOW]
        A4 --> A5[Run executors:<br/>CLUSTER_CONFIG, CATEGORIES_CONFIG,<br/>VM_CONFIG, CLUSTER_HARDWARE_CONFIG,<br/>VM_RECOVERY_POINT_CONFIG]
        A5 --> A6[Cleanup temp files]
        A6 --> A7[Emit completion logs]
        A7 --> A8[Job complete]
        A8 --> A9[Post-completion monitor window]
    end

    subgraph B["Lane: Postgres Pod (ntnx-ncm-datastore / cg-pg-1)"]
        B1[Read backfill_job_run_status] --> B2[Return last_persisted_epoch / last_completed_date]
        B3[Update service backfill status:<br/>NX_ROUTINE_WORKFLOW] --> B4[Mark status persisted]
        B5[Update service backfill status:<br/>CLUSTER_CONFIG] --> B4
        B6[Update service backfill status:<br/>CATEGORIES_CONFIG] --> B4
        B7[Update service backfill status:<br/>VM_CONFIG] --> B4
        B8[Update service backfill status:<br/>CLUSTER_HARDWARE_CONFIG] --> B4
        B9[Update service backfill status:<br/>VM_RECOVERY_POINT_CONFIG] --> B4
    end

    subgraph C["Lane: ClickHouse / Metrics Store"]
        C1[Drop old partition data] --> C2[Write new metrics batches]
        C2 --> C3[Acknowledge rows written]
    end

    subgraph D["Lane: Post-completion Workers (ncm-cg)"]
        D1[Precalculate worker:<br/>TCO Job Starting]
        D2[Precalculate worker:<br/>Starting Cluster TCO calculation]
        D3[Precalculate worker:<br/>Starting RAM cost calculation]
        D4[Inventory manager:<br/>Updated cost config]
        D1 --> D2 --> D3 --> D4
    end

    A3 -->|Query status window| B1
    B2 -->|Backfill range + control| A4

    A5 -->|Per executor start| C1
    C3 -->|Rows written result| A5

    A4 -->|Routine workflow status| B3
    A5 -->|CLUSTER_CONFIG done| B5
    A5 -->|CATEGORIES_CONFIG done| B6
    A5 -->|VM_CONFIG done| B7
    A5 -->|CLUSTER_HARDWARE_CONFIG done| B8
    A5 -->|VM_RECOVERY_POINT_CONFIG done| B9
    A9 -->|Watch downstream logs| D1
```

## Pod-to-Pod Execution Order (with work)

```mermaid
flowchart LR
    A["nx-cg-data-loader<br/>Triggers and runs backfill executors (CLUSTER/VM/CATEGORIES/HARDWARE/RECOVERY_POINT), writes ClickHouse metrics, updates PG backfill status"]
    B["nx-cg-hydra-billing-worker<br/>Runs Hydra billing workflows on ingested/backfilled usage data"]
    C["common-platform-billing-orchestration-worker/service<br/>Orchestrates billing pipeline stages and downstream billing workflow execution"]
    D["cg-multicloud-ingestion-reconciler-worker<br/>Reconciles multicloud ingestion state and normalizes data consistency"]
    E["nx-cg-precalculate-worker-v2<br/>Starts TCO job, performs cluster TCO and RAM cost recalculation"]
    F["nx-cg-inventory-manager-service<br/>Persists recalculated cost config updates in DB (Updated cost config)"]

    A --> B --> C --> D --> E --> F
```

### Must-See Log Pattern Per Pod

- `nx-cg-data-loader`: `NDP Data fetching: .* completed successfully` and `Updating service backfill status for Service :\[.*\]`
- `nx-cg-hydra-billing-worker`: `hydra` / `billing` workflow start-complete markers (environment-specific wording)
- `common-platform-billing-orchestration-worker/service`: `orchestration` / `workflow` stage transition logs
- `cg-multicloud-ingestion-reconciler-worker`: `reconcile` / `ingestion` state update logs
- `nx-cg-precalculate-worker-v2`: `TCO Job Starting for jobId`, `Starting Cluster TCO calculation`, `Starting RAM cost calculation`
- `nx-cg-inventory-manager-service`: `Updated cost config`

### Quick Grep Commands

```bash
# 1) Data-loader completion + PG status updates
rg "NDP Data fetching: .* completed successfully|Updating service backfill status for Service :\\[.*\\]" /Users/mohan.as1/workspace/mohan_helpers/pod-logs/nx-cg-data-loader-*.log

# 2) Hydra billing
rg -i "hydra|billing|workflow|completed|failed" /Users/mohan.as1/workspace/mohan_helpers/pod-logs/nx-cg-hydra-billing-worker-*.log

# 3) Platform billing orchestration
rg -i "orchestration|workflow|stage|completed|failed" /Users/mohan.as1/workspace/mohan_helpers/pod-logs/common-platform-billing-orchestration-*.log

# 4) Multicloud reconciler
rg -i "reconcile|ingestion|state|completed|failed" /Users/mohan.as1/workspace/mohan_helpers/pod-logs/cg-multicloud-ingestion-reconciler-worker-*.log

# 5) Precalculate TCO/cost recalculation
rg "TCO Job Starting for jobId|Starting Cluster TCO calculation|Starting RAM cost calculation" /Users/mohan.as1/workspace/mohan_helpers/pod-logs/nx-cg-precalculate-worker-v2-*.log

# 6) Final DB-side cost persistence
rg "Updated cost config" /Users/mohan.as1/workspace/mohan_helpers/pod-logs/nx-cg-inventory-manager-service-*.log
```


flowchart TD
    %% Kubernetes layer
    A[cron-nx-cg-data-loader CronJob] -->|Creates| B(nx-cg-data-loader Pod)
    B -->|Schedules via gRPC| C[NxBillingWorkflow]

    %% Temporal layer
    subgraph Temporal Workflow Orchestration

        C --> D[CgMulticloudBillingIngestionWf]

        subgraph Ingestion
            D --> E[CgMulticloudBillingNxSemiEnrichmentPushSubWf]
            E --> F[CgNxBillingIngestionSubWf]
        end

        F --> G[BillingPostProcessWorkflow]

        %% Parallel jobs triggered post-ingestion
        G --> H[MlForecastWorkflow]
        G --> I[ExpiredBudgetWorkflow]

        %% Routine jobs
        G --> J[WorkerModuleRoutineWorkflow]
        J --> K[PrecalculateModuleRoutineWorkflow]
        K --> L[HydraModuleRoutineWorkflow]

    end
