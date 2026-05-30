import os
import copy
import json
import sys
import requests
from pprint import pprint


client = requests.Session()

BASE_URL = 'https://iislliveblob.niftyindices.com/jsonfiles/Heatmap/FinalHeatMap{}.json?'
client = requests.Session()

indices = ['NIFTY%2050',  'NIFTY%20NEXT%2050', 'NIFTY%20100', 'NIFTY%20200', 'NIFTY%20500', 'NIFTY%20MIDCAP%2050', 'NIFTY%20MIDCAP%20100', 'NIFTY%20MIDCAP%20100', 'NIFTY%20SMALLCAP%20100', 'NIFTY%20AUTO', 'NIFTY%20BANK', 'NIFTY%20FINANCIAL%20SERVICES', 'NIFTY%20FMCG', 'NIFTY%20IT', 'NIFTY%20MEDIA', 'NIFTY%20METAL', 'NIFTY%20PHARMA', 'NIFTY%20PRIVATE%20BANK', 'NIFTY%20PSU%20BANK', 'NIFTY%20REALTY', 'NIFTY%20COMMODITIES', 'NIFTY%20CPSE', 'NIFTY%20ENERGY', 'NIFTY%20INDIA%20CONSUMPTION','NIFTY%20INFRASTRUCTURE', 'NIFTY%20MIDCAP%20LIQUID%2015', 'NIFTY%20MNC', 'NIFTY%20PSE', 'NIFTY%20SERVICES%20SECTOR', 'NIFTY100%20LIQUID%2015', 'NIFTY%20DIVIDEND%20OPPORTUNITIES%2050', 'NIFTY100%20QUALITY%2030', 'NIFTY%20GROWTH%20SECTORS%2015', 'NIFTY50%20VALUE%2020']
mail_dict = {}
temp = {}
for indice in indices:
  temp_copy = copy.deepcopy(temp)
  resp = client.get(BASE_URL.format(indice))
  if resp.status_code != 200:
    continue
  resp = json.loads(resp.content)
  send_data = []
  for i in resp:
    if abs(i['iislPercChange']) > 2:
      temp_copy[i['symbol']] = i['iislPercChange']
  temp_copy = json.dumps({k.replace('&', '_'): v for k, v in sorted(temp_copy.items(), key=lambda item: item[1])})
  indice = indice.replace('%20', '_')
  mail_dict['"' + indice + '"'] = temp_copy
  print(indice)

print(json.dumps(mail_dict))
mail = 'echo "{}" | mail -s "Nifty Indices" as.mohan9999@gmail.com'.format(json.dumps(mail_dict))
os.system(mail)
