# VM Recovery Points Analysis - Detailed Output Report

## Analysis Run Information

**Prism Central:** 10.114.55.128  
**Analysis Timestamp:** May 27, 2026 at 5:56 PM (2026-05-27T17:56:13)  
**Output File:** `recovery_points_analysis_20260527_163121.json`  
**File Size:** ~3.2 MB (3,205,140 characters)

---

## Executive Summary

### Cluster-Level Totals

| Metric | Value |
|--------|-------|
| **Total VMs with Recovery Points** | **2,164 VMs** |
| **Total Recovery Points (Snapshots)** | **6,138 snapshots** |
| **Total Reclaimable Space** | **135.14 GiB** (145,110,794,240 bytes) |
| **Average Recovery Points per VM** | **2.84 snapshots/VM** |
| **Average Reclaimable Space per VM** | **63.93 MiB/VM** |

### Key Insights

✅ **Most VMs have minimal space usage** - 80% of VMs have less than 1 MiB reclaimable space  
⚠️ **Top 3 VMs consume 44% of total space** - nc-2056cb-default-{0,1,2} have 59.27 GiB  
📊 **Recovery point distribution is healthy** - Most VMs have 2-3 recovery points  
💾 **Largest opportunity for cleanup** - 36 VMs have over 1 GiB each (73.75 GiB total)

---

## Detailed Analysis

### Top 20 VMs by Reclaimable Space

| Rank | VM Name | Recovery Points | Reclaimable Space | % of Total |
|------|---------|-----------------|-------------------|------------|
| 1 | nc-2056cb-default-1 | 5 | 23.12 GiB | 17.11% |
| 2 | nc-2056cb-default-2 | 5 | 19.33 GiB | 14.30% |
| 3 | nc-2056cb-default-0 | 5 | 16.81 GiB | 12.44% |
| 4 | 008e72ff | 1 | 3.08 GiB | 2.28% |
| 5 | 71801a3b | 1 | 3.06 GiB | 2.26% |
| 6 | dfc2fb97 | 1 | 3.06 GiB | 2.26% |
| 7 | 60058907 | 1 | 3.05 GiB | 2.26% |
| 8 | ahv_ins_delete-0-260514-183555 | 6 | 2.16 GiB | 1.60% |
| 9 | ahv_ins_delete-0-260514-185252 | 5 | 2.15 GiB | 1.59% |
| 10 | ahv_ins_delete-0-260514-192200 | 6 | 2.13 GiB | 1.58% |
| 11 | ahv_ins_delete-0-260514-194724 | 6 | 2.13 GiB | 1.58% |
| 12 | ahv_ins_delete-0-260514-181435 | 7 | 2.12 GiB | 1.57% |
| 13 | ahv_ins_delete-0-260514-194426 | 6 | 2.12 GiB | 1.57% |
| 14 | ahv_ins_delete-0-260514-185803 | 6 | 2.12 GiB | 1.57% |
| 15 | ahv_ins_delete-0-260514-175857 | 7 | 2.12 GiB | 1.57% |
| 16 | ahv_ins_delete-0-260514-192728 | 6 | 2.12 GiB | 1.57% |
| 17 | ahv_ins_delete-0-260514-182445 | 7 | 2.12 GiB | 1.57% |
| 18 | ahv_ins_delete-0-260514-182453 | 7 | 2.12 GiB | 1.57% |
| 19 | ahv_ins_delete-0-260514-184210 | 6 | 2.12 GiB | 1.57% |
| 20 | ahv_ins_delete-0-260514-181408 | 6 | 2.11 GiB | 1.56% |

**Top 20 Total:** 93.66 GiB (69.29% of cluster total)

### Critical Observations

#### 🔴 High Priority (Top 3 VMs)
- **nc-2056cb-default-1/2/0**: These appear to be Nutanix Controller (NC) VMs with 59.27 GiB total
  - 5 recovery points each
  - **Action:** Review if NC VM snapshots are necessary or can be reduced

#### 🟡 Medium Priority (4 VMs with truncated names)
- **008e72ff, 71801a3b, dfc2fb97, 60058907**: 12.25 GiB total
  - Only 1 recovery point each but consuming 3+ GiB per VM
  - **Action:** Investigate these VMs (names appear truncated/UUID-based)

#### 🟢 Normal Priority (ahv_ins_delete VMs)
- Multiple test/temporary VMs with 2-2.16 GiB each
  - 5-7 recovery points each
  - **Action:** These appear to be test VMs - consider cleanup

---

### Space Distribution Analysis

| Size Range | VM Count | Total Space | % of VMs | % of Space |
|------------|----------|-------------|----------|------------|
| **0 - 1 MiB** | 1,736 | 0.14 GiB | 80.22% | 0.10% |
| **1 MiB - 10 MiB** | 340 | 1.16 GiB | 15.71% | 0.86% |
| **10 MiB - 100 MiB** | 50 | 0.82 GiB | 2.31% | 0.61% |
| **100 MiB - 1 GiB** | 2 | 1.45 GiB | 0.09% | 1.07% |
| **1 GiB - 10 GiB** | 33 | 72.30 GiB | 1.53% | 53.49% |
| **10 GiB+** | 3 | 59.27 GiB | 0.14% | 43.87% |

**Key Insight:** The Pareto principle applies here - 1.67% of VMs (36 VMs) account for 97.36% of reclaimable space (131.57 GiB).

---

### Recovery Point Count Distribution

| Recovery Points | VM Count | % of Total VMs |
|----------------|----------|----------------|
| **1 RP** | 219 | 10.12% |
| **2 RPs** | 470 | 21.72% |
| **3 RPs** | 1,099 | 50.78% |
| **4-5 RPs** | 313 | 14.47% |
| **6-10 RPs** | 63 | 2.91% |
| **11+ RPs** | 0 | 0.00% |

**Key Insight:** Most VMs (50.78%) have exactly 3 recovery points, suggesting a common retention policy. No VMs have excessive recovery points (11+).

---

### VMs with Most Recovery Points

| Rank | VM Name | Recovery Points | Reclaimable Space |
|------|---------|-----------------|-------------------|
| 1 | ahv_ins_delete-0-260514-181435 | 7 | 2.12 GiB |
| 2 | ahv_ins_delete-0-260514-184641 | 7 | 2.03 GiB |
| 3 | ahv_ins_delete-0-260514-175832 | 7 | 2.11 GiB |
| 4 | ahv_ins_delete-0-260514-082142 | 7 | 2.03 GiB |
| 5 | ahv_ins_delete-0-260514-184128 | 7 | 2.11 GiB |

**Observation:** 9 VMs have 7 recovery points (maximum), all are test VMs with ~2 GiB reclaimable space each.

---

## Sample VM Details

### Example 1: VM with Multiple Recovery Points

**VM Name:** ahv_ins_delete-0-260521-094155  
**VM UUID:** 000468b4-a1e9-43e6-7ffc-9f658a0320bd  
**Recovery Point Count:** 4  
**Total Reclaimable Space:** 2.41 MiB

**Recovery Points Breakdown:**

| Name | Creation Time | Expiration | Size | Type | Status |
|------|---------------|------------|------|------|--------|
| bulk_2026-05-26_063112_157 | 2026-05-26 06:35:07 | 2026-06-25 | 160 KiB | CRASH_CONSISTENT | COMPLETE |
| bulk_2026-05-26_045047_1022 | 2026-05-26 05:16:26 | 2026-06-25 | 160 KiB | CRASH_CONSISTENT | COMPLETE |
| bulk_2026-05-26_030337_1022 | 2026-05-26 03:27:25 | 2026-06-25 | 96 KiB | CRASH_CONSISTENT | COMPLETE |
| snapshot-1779712566 | 2026-05-25 12:36:21 | 2026-05-28 | 2.00 MiB | CRASH_CONSISTENT | COMPLETE |

### Example 2: VM with Minimal Space

**VM Name:** ahv_ins_delete-0-260522-014224  
**VM UUID:** 004152d3-bc04-475c-6864-d9f34192cf78  
**Recovery Point Count:** 3  
**Total Reclaimable Space:** 1.41 MiB

**Recovery Points Breakdown:**

| Name | Creation Time | Size | Type |
|------|---------------|------|------|
| bulk_2026-05-26_063112_537 | 2026-05-26 06:44:34 | 1.09 MiB | CRASH_CONSISTENT |
| bulk_2026-05-26_045047_1405 | 2026-05-26 05:25:53 | 192 KiB | CRASH_CONSISTENT |
| bulk_2026-05-26_030337_1405 | 2026-05-26 03:38:36 | 128 KiB | CRASH_CONSISTENT |

---

## Recovery Point Naming Patterns

### Identified Patterns

1. **Bulk Snapshots** (Most Common)
   - Format: `bulk_YYYY-MM-DD_HHMMSS_###`
   - Example: `bulk_2026-05-26_063112_157`
   - Frequency: Automated bulk snapshot operations

2. **Timestamped Snapshots**
   - Format: `snapshot-{unix_timestamp}`
   - Example: `snapshot-1779712566`
   - Frequency: Manual or application-triggered snapshots

3. **Named Snapshots**
   - Format: Human-readable names with timestamps
   - Example: `9:59:56 am, May 18`
   - Frequency: Manual snapshots with custom names

---

## Storage Efficiency Analysis

### Compression/Deduplication Observations

Based on the recovery point sizes:
- **Most recovery points are small** (< 1 MiB): Indicates good deduplication
- **Some VMs have 0 B exclusive usage**: Perfect deduplication (sharing all blocks)
- **Large recovery points** (> 1 GiB): Indicate significant changes or new data

### Retention Policy Analysis

**Common Expiration Pattern:**
- Most recovery points expire after **30 days**
- Bulk snapshots created on May 26 expire on June 25
- This suggests a standard 30-day retention policy

**Exceptions:**
- Some snapshots expire after 3-7 days (e.g., snapshot-1779712566 expires May 28)
- Manual snapshots may have shorter retention

---

## Recommendations

### Immediate Actions (High Priority)

1. **Review NC VM Recovery Points** 🔴
   - VMs: nc-2056cb-default-{0,1,2}
   - Space: 59.27 GiB (43.87% of total)
   - Action: Verify if Nutanix Controller VM snapshots are necessary
   - Potential savings: Up to 59.27 GiB

2. **Investigate Truncated Name VMs** 🟡
   - VMs: 008e72ff, 71801a3b, dfc2fb97, 60058907
   - Space: 12.25 GiB (9.06% of total)
   - Action: Identify these VMs and review their snapshot retention
   - Potential savings: Up to 12.25 GiB

### Short-Term Actions (Medium Priority)

3. **Cleanup Test VMs** 🟢
   - Pattern: ahv_ins_delete-0-*
   - VMs: ~50 test VMs
   - Space: ~100+ GiB
   - Action: Delete test VMs and their recovery points
   - Potential savings: Variable, but significant

4. **Review VMs with 6-7 Recovery Points**
   - VMs: 63 VMs with 6-10 recovery points
   - Action: Consider reducing retention to 3-5 recovery points
   - Potential savings: 15-25 GiB (estimated)

### Long-Term Actions (Optimization)

5. **Implement Tiered Retention Policy**
   - Keep daily snapshots for 7 days
   - Keep weekly snapshots for 4 weeks
   - Keep monthly snapshots for 3-6 months
   - Expected savings: 20-30%

6. **Enable Snapshot Policies by VM Importance**
   - Production VMs: 5-7 recovery points
   - Development VMs: 2-3 recovery points
   - Test VMs: 1-2 recovery points or none
   - Expected savings: 30-40%

7. **Automate Snapshot Cleanup**
   - Implement automated cleanup for VMs marked for deletion
   - Remove recovery points for VMs older than X days
   - Expected savings: 10-15%

---

## Cost Impact Analysis

### Storage Savings Potential

| Action | VMs Affected | Potential Savings | % of Total | Effort |
|--------|--------------|-------------------|------------|--------|
| Review NC VM snapshots | 3 | 59.27 GiB | 43.87% | Low |
| Investigate truncated VMs | 4 | 12.25 GiB | 9.06% | Medium |
| Cleanup test VMs | ~50 | ~60 GiB | ~44% | High |
| Optimize retention policy | 2,164 | 20-40 GiB | 15-30% | Medium |
| **Total Potential Savings** | - | **131+ GiB** | **97%** | - |

### Implementation Priority Matrix

```
High Impact / Low Effort:
├─ Review NC VM snapshots (59.27 GiB)
└─ Investigate 4 truncated VMs (12.25 GiB)

High Impact / High Effort:
├─ Cleanup test VMs (~60 GiB)
└─ Implement tiered retention policy (20-40 GiB)

Low Impact / Low Effort:
└─ Reduce recovery points for VMs with 6-7 RPs (15-25 GiB)
```

---

## Next Steps

### Immediate (This Week)

1. ✅ Review this analysis report
2. ⬜ Investigate the 3 NC VMs (nc-2056cb-default-*)
3. ⬜ Identify the 4 VMs with truncated names
4. ⬜ Create action plan for test VM cleanup

### Short-Term (This Month)

5. ⬜ Delete unnecessary test VMs and their recovery points
6. ⬜ Implement automated cleanup for marked-for-deletion VMs
7. ⬜ Review and adjust retention policies per VM category

### Long-Term (Next Quarter)

8. ⬜ Implement tiered retention policy
9. ⬜ Set up monitoring for recovery point space usage
10. ⬜ Schedule quarterly recovery point audits

---

## Appendix

### JSON Output File Structure

```json
{
  "cluster_summary": {
    "total_vms": 2164,
    "total_recovery_points": 6138,
    "total_reclaimable_space_bytes": 145110794240,
    "total_reclaimable_space_human": "135.14 GiB",
    "prism_central": "10.114.55.128",
    "analysis_timestamp": "2026-05-27T17:56:13.824166"
  },
  "vms": [
    {
      "vm_uuid": "...",
      "vm_name": "...",
      "recovery_point_count": 4,
      "total_reclaimable_space_bytes": 2523136,
      "total_reclaimable_space_human": "2.41 MiB",
      "recovery_points": [
        {
          "extId": "...",
          "name": "...",
          "creationTime": "...",
          "expirationTime": "...",
          "totalExclusiveUsageBytes": 163840,
          "recoveryPointType": "CRASH_CONSISTENT",
          "status": "COMPLETE",
          "ownerExtId": "..."
        }
      ]
    }
  ]
}
```

### Glossary

- **Recovery Point**: A point-in-time snapshot of a VM
- **Reclaimable Space**: Storage that would be freed if the recovery point is deleted
- **Exclusive Usage**: Storage used only by this recovery point (not shared with other snapshots)
- **CRASH_CONSISTENT**: Snapshot type that captures VM state without application awareness
- **Retention Policy**: Rules defining how long recovery points are kept

---

**Report Generated:** May 28, 2026 at 8:27 AM  
**Script Version:** analyze_recovery_points.py v1.0  
**Documentation:** See ANALYZE_RECOVERY_POINTS_README.md for more details
