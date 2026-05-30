## fetch_payload.py
import re
import base64
import json

def Sorting(lst):
    lst.sort(key=len, reverse=True)
    return lst

file = open('ergon_tasks', 'r')
lines = file.readlines()

file1 = open('decoded.txt', 'w')
count = 0
arr = []

for line in lines:
  length = len(line)
  body = "\"body\":\""
  words = line.split('"internal_opaque": "')
  if len(words) > 1:
    word = words[1]
    word2 = word.split('","')[0]
    #decoded = base64.b64decode(word2)
    #file1.write(word2)
    arr.append(word2)
    Sorting(arr)
    #file1.write("\n\n")


for a in arr:
  try:
    decoded = base64.b64decode(a)
    file1.write(decoded.decode('latin-1'))
  except Exception as e:
    print(decoded)