import requests

url = "https://10.53.60.173:9440/api/lifecycle/v4.0/svcmgr/applications"

payload = {}
headers = {
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
  'Cookie': 'NTNX_IAM_SESSION=CgVhZG1pbhC4+vvLBhoHTWVyY3VyeSAAKihmZjNiMGY2YzdhMjMzMWFjYmZiMGMzZDk1N2YzMzBkOWExZmFhMGJj|xGWvkq4IdiHLqRTCjwp5lsQgWMfFIDDd2QNXlRz5mOQ=; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChlmMzJrMzRidG5iM2dvaDJndTZpeXh6bnNvEhlpeDNxZXpsanBjY2N4eDdrNzNqenZkY2th; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhC4+vvLBhoHTWVyY3VyeSAAKihmZjNiMGY2YzdhMjMzMWFjYmZiMGMzZDk1N2YzMzBkOWExZmFhMGJj|xGWvkq4IdiHLqRTCjwp5lsQgWMfFIDDd2QNXlRz5mOQ='
}

response = requests.request("GET", url, headers=headers, data=payload, verify=False)

print(response.text)
