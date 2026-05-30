#!/bin/bash

STAMP="$1"
if [ -z "$STAMP" ]; then
  echo "Usage: $0 <before|after>"
  exit 1
fi

OUTDIR="cluster_snapshot_$STAMP"
mkdir -p "$OUTDIR"

echo "Collecting cluster snapshot: $STAMP"
echo "Output dir: $OUTDIR"
echo "----------------------------------"

### 1. Nodes overview
kubectl get nodes -o wide > "$OUTDIR/nodes.txt"

### 2. Pods per node + resource summary
mkdir -p "$OUTDIR/nodes"

for NODE in $(kubectl get nodes -o name | cut -d/ -f2); do
  kubectl get pods -A -o json \
    --field-selector spec.nodeName="$NODE" | jq '
    {
      node: "'"$NODE"'",
      pod_count: (.items | length),
      pods:
        (.items[] |
          {
            ns: .metadata.namespace,
            name: .metadata.name,
            phase: .status.phase,
            owner:
              (if .metadata.ownerReferences then
                .metadata.ownerReferences[0].kind
               else "Standalone" end)
          }),
      resources:
        (
          [
            .items[].spec.containers[] |
            {
              cpu_req: (.resources.requests.cpu // "0"),
              mem_req: (.resources.requests.memory // "0"),
              cpu_lim: (.resources.limits.cpu // "0"),
              mem_lim: (.resources.limits.memory // "0")
            }
          ] |
          reduce .[] as $c (
            {cpu_req:0, mem_req:0, cpu_lim:0, mem_lim:0};
            .cpu_req += (if ($c.cpu_req|test("m$")) then ($c.cpu_req|sub("m";"")|tonumber)
                         elif ($c.cpu_req=="0") then 0
                         else ($c.cpu_req|tonumber*1000) end) |
            .cpu_lim += (if ($c.cpu_lim|test("m$")) then ($c.cpu_lim|sub("m";"")|tonumber)
                         elif ($c.cpu_lim=="0") then 0
                         else ($c.cpu_lim|tonumber*1000) end) |
            .mem_req += (if ($c.mem_req|test("Mi$")) then ($c.mem_req|sub("Mi";"")|tonumber)
                         elif ($c.mem_req|test("Gi$")) then ($c.mem_req|sub("Gi";"")|tonumber*1024)
                         else 0 end) |
            .mem_lim += (if ($c.mem_lim|test("Mi$")) then ($c.mem_lim|sub("Mi";"")|tonumber)
                         elif ($c.mem_lim|test("Gi$")) then ($c.mem_lim|sub("Gi";"")|tonumber*1024)
                         else 0 end)
          )
        )
    }
    ' > "$OUTDIR/nodes/$NODE.json"
done

### 3. Standalone pods (HIGH RISK)
kubectl get pods -A -o json | jq -r '
.items[]
| select(.metadata.ownerReferences == null)
| [.spec.nodeName, .metadata.namespace, .metadata.name]
| @tsv
' > "$OUTDIR/standalone_pods.txt"

### 4. Pod Disruption Budgets
kubectl get pdb -A -o wide > "$OUTDIR/pdbs.txt"

### 5. StatefulSets
kubectl get statefulsets -A -o wide > "$OUTDIR/statefulsets.txt"

### 6. Local Persistent Volumes
kubectl get pv -o json | jq -r '
.items[]
| select(.spec.local != null)
| [.metadata.name,
   .spec.nodeAffinity.required.nodeSelectorTerms[].matchExpressions[].values[]]
| @tsv
' > "$OUTDIR/local_pvs.txt"

### 7. kube-system pod placement
kubectl get pods -n kube-system -o wide > "$OUTDIR/kube_system_pods.txt"

### 8. Node taints
kubectl get nodes -o json | jq -r '
.items[]
| [.metadata.name,
   (.spec.taints // [] | map(.key + "=" + .value) | join(","))]
| @tsv
' > "$OUTDIR/node_taints.txt"

### 9. Node conditions / pressure
kubectl describe nodes > "$OUTDIR/node_conditions.txt"

### 10. Events snapshot
kubectl get events -A --sort-by=.metadata.creationTimestamp \
  > "$OUTDIR/events.txt"

### 11. Versions
kubectl version > "$OUTDIR/version.txt"

echo "Snapshot collection complete."
