# import os
# s = ["110.36.199.20","10.36.199.58","10.115.150.153","10.36.198.203"," 10.36.199.16"," 10.115.150.153"," 10.36.195.50"," 10.36.199.0"," 10.36.195.60"]
# for i in s:
#     print(i)
#     os.popen(f"sshpass -p \"nutanix/4u\" ssh -o StrictHostKeyChecking=no nutanix@{i} 'pkill screen;'")
#     print("LOL")
 
# s = """ Type         Name                              # reqs  50%  66%  75%  80%  90%  95%  98%  99% 99.9% 99.99%  100%
s = """POST                 images/list                                       201    980   1000   1100   1100   1300   1400   1400   1500   1900   1900   1900
 POST                 subnets/list                                      402    400    430    450    470    510    560    630    710    820    820    820
 GET                  accounts                          19569     11     13     14     15     16     19     28    270    790   1400   1600
 GET                  apps                                994   1500   1700   1800   2000   2200   2500   2900   3300  34000  34000  34000
 GET                  apps_provisioning                  7014   1500   1700   1900   2000   2300   2600   3100   4000  44000  50000  50000
 POST                 blueprint_create                    201   2900   3100   3400   3500   3800   4000   4100   5900  44000  44000  44000
 POST                 blueprint_launch                    999    570    780   1100   1200   1400   1500   1700   2000   2900   2900   2900
 PUT                  blueprint_update                    201   3000   3400   3600   3800   4300   4800   5100   5200   6200   6200   6200
 GET                  blueprints                          201    240    270    320    390    500    610    750    770    920    920    920
 GET                  blueprints/export_json              201   1200   1300   1400   1500   1900   2100   2400   3200   3600   3600   3600
 POST                 blueprints/list                     201   2200   3000   3400   3600   4100   4400   4900   5100   5800   5800   5800
 POST                 bp/validate_launch                 1998    280    400    470    510    640    870   1100   1300  15000  22000  22000
 POST                 dm/v3/apps_list                     201    560    630    710    740    880   1100   1300   1400   1700   1700   1700
 POST                 groups_category                     402    340    360    390    410    480    530    590    660    810    810    810
 POST                 groups_project                    39940     16     18     20     21     24     27     33     44    490    810    930
 POST                 patch_with_environment/validate      999   1500   1700   1900   2000   2300   2500   2900   3100  22000  22000  22000
 GET                  pending_launches                   2004    240    320    390    420    520    600    720    900  44000  51000  51000
 GET                  projects_internal                 19970    330    370    400    430    510    610    750    870   1600   2400   2400"""
s = [i.split() for i in s.split('\n')]
k = {}
for i in s:
    # if i[1] in k:
    #     k[i[1]].append(int(i[2]))
    # else:
        k[i[1]] = int(i[7])

for i in k:
    print(k[i])