import requests
p = []
r = []
for i in range(655,669):
    r.append(i)
r.append(701)
for j in r:
    url = f"http://erdinger.eng.nutanix.com/job/QA/job/ST/job/locust/{j}/console"
    payload = {}
    headers = {
    'Cookie': 'JSESSIONID.91e6b991=node050odpagrsbu3llrliqr9s6mw51483.node0'
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    s = response.text
    log = False
    result = []
    data = s.split('\n')
    for i in data:
        if log and '--' not in i:
            result.append(i.split())
        if i == 'Percentage of the requests completed within given times':
            log = True
        if ' None                 Aggregated     ' in i:
            break
        
    final_result = {}
    for i in result[1:]:
        final_result[i[1]] = [eval(i[2]), eval(i[8])]

    count = 0
    for i in data[::-1]:
        if count >5:
            break
        if count == 5 and '-' not in i:
            l = i.split()[3].split('(')
            final_result[i.split()[1]].extend([eval(l[0]), eval(l[1][:-2])])
        if '-------------------------------------------------------------------------------------------------------------' in i:
            count += 1
    for i in data:
        if '<title>QA » ST » locust ' in i:
            print(i.split()[5])
            p.append(i.split()[5])
            break
    for i in final_result:
        if len(final_result[i]) == 4:
            if 2 < final_result[i][-1] < 100 :
                print(i, final_result[i])
        
print(p)