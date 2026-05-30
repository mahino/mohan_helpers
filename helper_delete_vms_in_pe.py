with open('vm_list', 'r') as s:
  q= ''
  r=s.readlines()
  for i in r:
    i = i.split()
    q += i[0] + ' '
with open('vm_list', 'w') as s:
  s.write(q) 
