import requests

# Define the API endpoint URL where you want to send the request
url = "https://10.36.199.9:9440/api/nutanix/v3/blueprints/import_file"  # Replace with your actual API URL



# Define the form data
form_data = {
    'name': 'test11',
    'project_uuid': '8f3700ac-83c0-4585-b05b-31dc7d70b9ac',
    'passphrase': 'nutanix/4u'
}

headers = {
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
}
# Specify the files to be uploaded
files = {'file': ('blob', open('blob', 'rb'), 'application/octect-stream')}

# Make the POST request with the form data and files
response = requests.post(url, data=form_data, files=files, verify=False, headers=headers)

# Check the response
if response.status_code == 200:
    print("File uploaded successfully.")
    print(response.text)
else:
    print("Error uploading file.")
    print(response.text)
