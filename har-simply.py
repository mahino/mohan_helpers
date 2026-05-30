import json
import copy
with open('temp.har') as f:
  apis_data = f.read()
  

s = []
data = {
  "url": '',
  "request": {},
  "response": {}
  
}
apis_data = json.loads(apis_data)
for i in apis_data['log']['entries']:
  if i['_resourceType'] in ['fetch', 'xhr']:
    data_copy = copy.deepcopy(data)
    data_copy['url'] = i['request']['url']
    data_copy['request'] = i['request']
    data_copy['method'] = i['request']['method']
    data_copy['response'] = i['response']
    ## requests del
    del data_copy['request']['httpVersion']
    del data_copy['request']['headers']
    del data_copy['request']['queryString']
    del data_copy['request']['cookies']
    del data_copy['request']['headersSize']
    del data_copy['request']['bodySize']
    if data_copy['method'] not in ['GET', 'DELETE']:
      data_copy['request']['postData']['payload'] = json.loads(data_copy['request']['postData']['text'])
      del data_copy['request']['postData']['text']
      
    ## response del
    del data_copy['response']['httpVersion']
    del data_copy['response']['headers']
    del data_copy['response']['cookies']
    del data_copy['response']['headersSize']
    del data_copy['response']['bodySize']
    if data_copy['response']['content']['mimeType'] == 'application/json':
      data_copy['response']['content']['payload'] = json.loads(data_copy['response']['content']['text'])
      del data_copy['response']['content']['text']
    
    s.append(data_copy)

with open('final_har_simply.json', 'w') as f:
  f.write(json.dumps(s))

print(len(s))