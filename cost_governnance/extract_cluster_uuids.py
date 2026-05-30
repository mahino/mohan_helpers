#!/usr/bin/env python3
"""
Script to extract cluster UUIDs from Nutanix Cost Governance API response
"""

import json

def main():
    # API response data
    api_response = {
        "totalCount": 24,
        "data": [
            {
                "clusterUuid": "00063ffe-e22c-90bf-45a6-7cc25530e846",
                "clusterName": "AdPE1",
                "monthlyCost": 424.5183332,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063fff-3b65-3df9-6bee-7cc255814617",
                "clusterName": "AdPE2",
                "monthlyCost": 424.5183332,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8c-07f2-1dad-07cb-25bd600237e9",
                "clusterName": "auto_cluster_nested_68c323767298f6fd7d0a7df7",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8c-0969-ed22-068d-0fdd8949cf6d",
                "clusterName": "auto_cluster_nested_68c323767298f6fd7d0a7df8",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8c-06e5-7147-0f46-caabd7bfeaa4",
                "clusterName": "auto_cluster_nested_68c323767298f6fd7d0a7dfa",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8c-08a2-ee9a-0367-29d8c810c154",
                "clusterName": "auto_cluster_nested_68c323767298f6fd7d0a7dfb",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8c-0879-a6af-06c5-258c9eb39dbb",
                "clusterName": "auto_cluster_nested_68c323767298f6fd7d0a7dfd",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8c-06de-a542-0a1c-51119efe9de3",
                "clusterName": "auto_cluster_nested_68c323767298f6fd7d0a7dfe",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8e-dddf-b295-0e33-3e7a8ce0f3c3",
                "clusterName": "auto_cluster_nested_68c354cb7298f6fd81d8230e",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063e8e-dc39-5f8c-0ef8-15920b5dfcbc",
                "clusterName": "auto_cluster_nested_68c354cb7298f6fd81d8230f",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-b124-e115-0530-2da12ed6ef52",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f0147",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-b15b-edc0-09e1-b8b0e380d3c0",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f0148",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-b1e3-835f-0547-e7823f12c680",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f0149",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-b0d0-9aaf-0700-8c57df20f4fb",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f014a",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-b11f-db16-0aea-8ea279b90f43",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f014b",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-b065-dd7d-0300-bbb7b08dbe38",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f014c",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-af43-e0be-0935-ac48ab5be589",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f014d",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ecc-af30-785b-07c7-cb32a4f6770a",
                "clusterName": "auto_cluster_nested_68c760cc92fce935695f014e",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ef1-2e1c-e92b-0f64-c5b5ef285092",
                "clusterName": "auto_cluster_nested_68c9c58b360236a240bdb158",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ef1-2e6f-1344-07f4-2472d57ed923",
                "clusterName": "auto_cluster_nested_68c9c58b360236a240bdb159",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ef1-3a57-a749-064b-1086c8fb24f5",
                "clusterName": "auto_cluster_nested_68c9c58b360236a240bdb15a",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ef1-3acc-466e-0a59-3e878e0ed012",
                "clusterName": "auto_cluster_nested_68c9c58b360236a240bdb15b",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00063ef1-3793-3dbe-0e32-2897dafc3e93",
                "clusterName": "auto_cluster_nested_68c9c58b360236a240bdb15c",
                "monthlyCost": 443.8300008,
                "meteringModel": "ACTUAL"
            },
            {
                "clusterUuid": "00064002-1290-400a-0000-0000000193e1",
                "clusterName": "auto_cluster_prod_shashi_kiran_f65bc645cb98",
                "monthlyCost": 1150.2199976,
                "meteringModel": "ACTUAL"
            }
        ]
    }
    
    print("=" * 80)
    print("  NUTANIX CLUSTER UUID EXTRACTOR")
    print("=" * 80)
    print(f"Total Clusters Found: {api_response['totalCount']}")
    print(f"Clusters in Data: {len(api_response['data'])}")
    print("=" * 80)
    print()
    
    # Extract cluster UUIDs
    cluster_uuids = []
    
    print("CLUSTER UUIDs:")
    print("-" * 50)
    
    for i, cluster in enumerate(api_response['data'], 1):
        uuid = cluster['clusterUuid']
        name = cluster['clusterName']
        cost = cluster['monthlyCost']
        
        cluster_uuids.append(uuid)
        print(f"{i:2d}. {uuid} | {name[:40]:<40} | ${cost:>8.2f}")
    
    print("-" * 50)
    print(f"Total: {len(cluster_uuids)} cluster UUIDs extracted")
    print()
    
    # Print UUIDs as a simple list
    print("CLUSTER UUIDs (List Format):")
    print("-" * 40)
    for uuid in cluster_uuids:
        print(uuid)
    
    print()
    print("CLUSTER UUIDs (Python List Format):")
    print("-" * 40)
    print("cluster_uuids = [")
    for uuid in cluster_uuids:
        print(f'    "{uuid}",')
    print("]")
    
    print()
    print("CLUSTER UUIDs (Comma-separated):")
    print("-" * 40)
    print(",".join(cluster_uuids))
    
    print()
    print("CLUSTER UUIDs (JSON Format):")
    print("-" * 40)
    print(json.dumps(cluster_uuids, indent=2))
    
    # Summary by cluster type
    print()
    print("CLUSTER SUMMARY BY TYPE:")
    print("-" * 30)
    
    ad_clusters = [c for c in api_response['data'] if c['clusterName'].startswith('AdPE')]
    nested_clusters = [c for c in api_response['data'] if 'nested' in c['clusterName']]
    prod_clusters = [c for c in api_response['data'] if 'prod' in c['clusterName']]
    
    print(f"AdPE Clusters: {len(ad_clusters)}")
    print(f"Nested Clusters: {len(nested_clusters)}")
    print(f"Production Clusters: {len(prod_clusters)}")
    print(f"Other Clusters: {len(api_response['data']) - len(ad_clusters) - len(nested_clusters) - len(prod_clusters)}")
    
    # Cost summary
    total_cost = sum(cluster['monthlyCost'] for cluster in api_response['data'])
    avg_cost = total_cost / len(api_response['data'])
    
    print()
    print("COST SUMMARY:")
    print("-" * 20)
    print(f"Total Monthly Cost: ${total_cost:,.2f}")
    print(f"Average Cost per Cluster: ${avg_cost:,.2f}")
    print(f"Highest Cost: ${max(cluster['monthlyCost'] for cluster in api_response['data']):,.2f}")
    print(f"Lowest Cost: ${min(cluster['monthlyCost'] for cluster in api_response['data']):,.2f}")
    
    print()
    print("=" * 80)
    print("Script completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()