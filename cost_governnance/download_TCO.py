#!/usr/bin/env python3
"""
NCM TCO Reports Downloader using HTTP Basic Authentication
Downloads TCO purchase data and saves to XLS files
"""
import requests
import json
import time
import os
import urllib3
from datetime import datetime
from requests.auth import HTTPBasicAuth
import xlwt
import xlrd
import pandas as pd
import pyexcel as pe
import random
import glob

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create log file with timestamp
log_filename = f"download_tco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_file = open(log_filename, 'a')

def log_print(message):
    """Print to console and write to log file"""
    print(message)
    log_file.write(str(message) + '\n')
    log_file.flush()

# Configuration
REPORTS_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/tco/purchases"

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

MAX_DOWNLOADS = 1
RATE_LIMIT_SLEEP = 60
DOWNLOADS_PER_MINUTE = 2
SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE = 60
ROWS_TO_MODIFY = 50

# Create directories
os.makedirs("tco_reports", exist_ok=True)

def save_to_xls(data, filename):
    """Save JSON data to XLS file"""
    try:
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('TCO Purchases')
        
        # Write headers and data based on response structure
        if isinstance(data, dict):
            # Write as key-value pairs
            row = 0
            for key, value in data.items():
                sheet.write(row, 0, str(key))
                sheet.write(row, 1, str(value))
                row += 1
        elif isinstance(data, list):
            # Write as table
            if len(data) > 0 and isinstance(data[0], dict):
                # Write headers
                headers = list(data[0].keys())
                for col, header in enumerate(headers):
                    sheet.write(0, col, header)
                
                # Write data rows
                for row_idx, item in enumerate(data, 1):
                    for col_idx, header in enumerate(headers):
                        value = item.get(header, '')
                        sheet.write(row_idx, col_idx, str(value))
        
        workbook.save(filename)
        log_print(f"  Saved to: {filename}")
        return True
    except Exception as e:
        log_print(f"  ERROR saving to XLS: {str(e)}")
        return False

def download_report():
    """Download a single report"""
    try:
        response = client.get(REPORTS_URL, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        log_print(f"Request failed: {e}")
        return None


def modify_cost_per_metering_unit(input_file, output_file, change_amount=1):
    """
    Modify the 'Cost per Metering Unit' column in the Excel file by adding/subtracting a random value
    ONLY modifies custom costs (test_tco_config_*) as per API guidelines
    Uses pyexcel for better Excel file preservation
    
    Args:
        input_file: Path to input Excel file
        output_file: Path to save modified Excel file
        change_amount: Amount to add or subtract (default: 1)
    
    Returns:
        Number of rows modified
    """
    try:
        # Read the Excel file as a book (preserves all sheets and formatting)
        print(f"Reading Excel file with pyexcel...")
        book = pe.get_book(file_name=input_file)
        
        # Get the Direct_Costs sheet
        direct_costs_sheet = book['Direct_Costs']
        
        # Convert to array for easier manipulation
        data = direct_costs_sheet.to_array()
        
        # Get headers (first row)
        headers = data[0]
        
        # Find column indices
        cost_col_idx = headers.index('Cost per Metering Unit')
        product_name_col_idx = headers.index('Product Name')
        cost_type_col_idx = headers.index('Cost Type')
        
        print(f"Total rows in Direct_Costs: {len(data) - 1}")  # -1 for header
        
        # Find custom cost rows
        custom_cost_rows = []
        for row_idx in range(1, len(data)):  # Skip header
            try:
                product_name = str(data[row_idx][product_name_col_idx])
                cost_value = data[row_idx][cost_col_idx]
                cost_type = data[row_idx][cost_type_col_idx]
                
                # Check if it's a custom cost with valid values
                if (product_name.startswith('test_tco_config_') and 
                    cost_value and
                    isinstance(cost_value, (int, float)) and 
                    cost_value > 0 and
                    cost_type and str(cost_type).strip() != ''):
                    custom_cost_rows.append(row_idx)
            except:
                continue
        
        print(f"Custom cost rows found: {len(custom_cost_rows)}")
        
        if not custom_cost_rows:
            print("WARNING: No custom cost rows found to modify!")
            return 0
        
        # Select random rows to modify
        num_rows_to_modify = min(ROWS_TO_MODIFY, len(custom_cost_rows))
        selected_rows = random.sample(custom_cost_rows, num_rows_to_modify)
        print(f"Modifying {num_rows_to_modify} random rows")
        
        modified_count = 0
        
        for row_idx in selected_rows:
            try:
                current_value = data[row_idx][cost_col_idx]
                product_name = data[row_idx][product_name_col_idx]
                
                # Randomly add or subtract the change_amount
                change = random.choice([change_amount, -change_amount])
                new_value = current_value + change
                
                # Ensure value doesn't go negative or zero
                if new_value <= 0:
                    new_value = current_value + abs(change_amount)  # Force positive change
                
                # Modify the value in the data array
                data[row_idx][cost_col_idx] = new_value
                print(f"  Row {row_idx + 1} ({product_name}): {current_value} -> {new_value}")
                modified_count += 1
            except Exception as e:
                print(f"  ERROR modifying row {row_idx}: {str(e)}")
                continue
        
        # Save with explicit sheet ordering: Guide first, then Direct_Costs
        print(f"Writing modified Excel file...")
        # Create ordered dict to preserve sheet order and names
        from collections import OrderedDict
        sheets_dict = OrderedDict()
        sheets_dict['Guide'] = book['Guide'].to_array()
        sheets_dict['Direct_Costs'] = data
        
        # Save with correct sheet names
        pe.save_book_as(bookdict=sheets_dict, dest_file_name=output_file)
        
        # Verify sheet names are correct
        verify_book = pe.get_book(file_name=output_file)
        print(f"Saved sheets: {verify_book.sheet_names()}")
        
        print(f"Successfully saved modified file")
        return modified_count
        
    except Exception as e:
        raise Exception(f"Failed to modify Excel file: {str(e)}")


def upload_tco_file(file_path):
    """
    Upload TCO Excel file to the API
    
    Args:
        file_path: Path to the Excel file to upload
    
    Returns:
        Response object with purchase data
    """
    try:
        # Create a new session without JSON content-type for file upload
        upload_client = requests.Session()
        upload_client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
        upload_client.verify = False
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/vnd.ms-excel')}
            response = upload_client.post(REPORTS_URL, files=files, timeout=60)
        
        return response
        
    except Exception as e:
        raise Exception(f"Failed to upload file: {str(e)}")


def apply_tco_changes(purchases_data):
    """
    Apply TCO changes using PUT endpoint
    
    Args:
        purchases_data: List of purchase objects from upload response
    
    Returns:
        Response object
    """
    try:
        body = {"purchases": purchases_data}
        response = client.put(REPORTS_URL, json=body, timeout=60)
        return response
        
    except Exception as e:
        raise Exception(f"Failed to apply changes: {str(e)}")


def process_tco_modification(original_file, change_amount=1):
    """
    Complete workflow: modify Excel file, upload, and apply changes
    
    Args:
        original_file: Path to the original downloaded Excel file
        change_amount: Amount to modify Cost per Metering Unit by (default: 1)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Step 1: Create modified file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        modified_file = original_file.replace('.xls', f'_modified_{timestamp}.xls')
        
        log_print(f"\n{'='*80}")
        log_print("TCO MODIFICATION WORKFLOW")
        log_print(f"{'='*80}")
        log_print(f"Step 1: Modifying 'Cost per Metering Unit' column (±{change_amount})")
        
        modified_count = modify_cost_per_metering_unit(original_file, modified_file, change_amount)
        log_print(f"  ✓ Modified {modified_count} rows")
        log_print(f"  ✓ Saved to: {modified_file}")
        
        # Step 2: Upload modified file
        log_print(f"\nStep 2: Uploading modified file to API")
        log_print(f"  Waiting 60 seconds to avoid rate limiting...")
        time.sleep(60)
        
        # Retry logic for rate limiting
        max_retries = 3
        retry_delay = 60
        upload_response = None
        
        for attempt in range(max_retries):
            upload_response = upload_tco_file(modified_file)
            
            if upload_response.status_code == 429:
                if attempt < max_retries - 1:
                    log_print(f"  Rate limited (429). Waiting {retry_delay}s before retry {attempt + 2}/{max_retries}...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False, f"Upload failed after {max_retries} attempts due to rate limiting"
            elif upload_response.status_code not in [200, 201, 202]:
                error_text = upload_response.text
                log_print(f"  Full error response: {error_text}")
                return False, f"Upload failed with status {upload_response.status_code}: {error_text[:500]}"
            else:
                break
        
        log_print(f"  ✓ Upload successful (Status: {upload_response.status_code})")
        
        # Parse response
        upload_data = upload_response.json()
        purchases = upload_data.get('purchases', [])
        log_print(f"  ✓ Received {len(purchases)} purchase records")
        
        # Log sample purchase data
        if purchases:
            log_print(f"\n  Sample purchase data:")
            sample = purchases[0]
            log_print(f"    - Config ID: {sample.get('configId')}")
            log_print(f"    - Product: {sample.get('productName')}")
            log_print(f"    - Cost per Meter: {sample.get('costPerMeter')}")
            log_print(f"    - Row Number: {sample.get('rowNumber')}")
        
        # Step 3: Apply changes
        log_print(f"\nStep 3: Applying TCO changes via PUT endpoint")
        print(json.dumps(purchases))
        apply_response = apply_tco_changes(purchases)
        
        if apply_response.status_code not in [200, 201, 202, 204]:
            return False, f"Apply failed with status {apply_response.status_code}: {apply_response.text[:200]}"
        
        log_print(f"  ✓ Changes applied successfully (Status: {apply_response.status_code})")
        
        if apply_response.text:
            log_print(f"  Response: {apply_response.text[:200]}")
        else:
            log_print(f"  Response: null (success)")
        
        log_print(f"\n{'='*80}")
        log_print("TCO MODIFICATION COMPLETED SUCCESSFULLY")
        log_print(f"{'='*80}\n")
        
        return True, "Success"
        
    except Exception as e:
        error_msg = f"TCO modification workflow failed: {str(e)}"
        log_print(f"\n  ✗ ERROR: {error_msg}")
        return False, error_msg



log_print(f"{'='*80}")
log_print(f"NCM TCO Reports Download Script Started")
log_print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log_print(f"Log file: {log_filename}")
log_print(f"Max Downloads: {MAX_DOWNLOADS}")
log_print(f"Rate Limit: {DOWNLOADS_PER_MINUTE} requests per minute")
log_print(f"{'='*80}\n")

download_count = 0
sleep_count = 0
saved_count = 0
failed_count = 0
start_time = datetime.now()

try:
    while download_count < MAX_DOWNLOADS:
        
        if download_count % DOWNLOADS_PER_MINUTE == 0 and download_count > 0:
            log_print(f"\nRate Limit: Sleeping for {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE} seconds after {DOWNLOADS_PER_MINUTE} TCO Report downloads...")
            time.sleep(SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
        
        log_print(f"\n--- TCO Report [{download_count + 1}/{MAX_DOWNLOADS}] ---")
        response = download_report()
        
        if response is None:
            log_print(f"Request failed, retrying in 1 second...")
            failed_count += 1
            time.sleep(1)
            continue

        if response.status_code == 429:
            sleep_count += 1
            log_print(f"WARN: Rate limited (429). Sleeping for {RATE_LIMIT_SLEEP}s. Sleep count: {sleep_count}")
            time.sleep(RATE_LIMIT_SLEEP)

        elif response.status_code in [200, 202]:
            download_count += 1
            log_print(f"SUCCESS: TCO Report downloaded (Status: {response.status_code})")
            
            # Check content type and save accordingly
            try:
                content_type = response.headers.get('Content-Type', '').lower()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Check if response is JSON
                if 'application/json' in content_type or (content_type.startswith('text/') and response.content[0:1] in [b'{', b'[']):
                    # Parse JSON and save to XLS
                    data = json.loads(response.content)
                    filename = f"tco_reports/tco_report_{download_count}_{timestamp}.xls"
                    
                    if save_to_xls(data, filename):
                        saved_count += 1
                    else:
                        failed_count += 1
                else:
                    # Binary content - likely Excel file from API
                    # Check if it's an Excel file by magic bytes
                    is_excel = response.content[:4] == b'\xd0\xcf\x11\xe0'  # Old Excel format
                    is_xlsx = response.content[:4] == b'PK\x03\x04'  # ZIP format (xlsx)
                    
                    if is_excel or 'excel' in content_type or 'spreadsheet' in content_type:
                        # It's already an Excel file, save it directly
                        ext = 'xls' if is_excel else 'xlsx'
                        filename = f"tco_reports/tco_report_{download_count}_{timestamp}.{ext}"
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        log_print(f"  Saved Excel file to: {filename}")
                        log_print(f"  Content-Type: {content_type}")
                        saved_count += 1
                    elif 'pdf' in content_type or response.content[:4] == b'%PDF':
                        # PDF file
                        filename = f"tco_reports/tco_report_{download_count}_{timestamp}.pdf"
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        log_print(f"  Saved PDF file to: {filename}")
                        saved_count += 1
                    else:
                        # Unknown binary format
                        filename = f"tco_reports/tco_report_{download_count}_{timestamp}.bin"
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        log_print(f"  Saved binary file to: {filename}")
                        log_print(f"  Content-Type: {content_type}")
                        log_print(f"  First 20 bytes (hex): {response.content[:20].hex()}")
                        saved_count += 1
                    
            except json.JSONDecodeError as e:
                log_print(f"  ERROR: Failed to parse JSON - {str(e)}")
                log_print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                log_print(f"  First 100 bytes: {response.content[:100]}")
                failed_count += 1
            except Exception as e:
                log_print(f"  ERROR: Failed to save file - {str(e)}")
                failed_count += 1
            
            sleep_count = 0
            time.sleep(0.5)
            
        else:
            log_print(f"FAILED: Download failed with status {response.status_code}")
            log_print(f"Response: {response.text[:200]}...")
            failed_count += 1
            time.sleep(1)
        
        # After downloading, modify and upload the file
        tco_files = sorted(glob.glob("tco_reports/*.xls"))
        # Filter out already modified files
        tco_files = [f for f in tco_files if '_modified_' not in f]
        if tco_files:
            success, message = process_tco_modification(tco_files[0], change_amount=1)
            if success:
                log_print(f"✓ TCO modification successful!")
            else:
                log_print(f"✗ TCO modification failed: {message}")

except KeyboardInterrupt:
    log_print("\n\nScript interrupted by user")
except Exception as e:
    log_print(f"\n\nFATAL ERROR: {str(e)}")
finally:
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log_print(f"\n{'='*80}")
    log_print("FINAL STATISTICS")
    log_print(f"{'='*80}")
    log_print(f"Total Downloads Attempted: {download_count}")
    log_print(f"Successfully Saved: {saved_count}")
    log_print(f"Failed: {failed_count}")
    log_print(f"Rate Limited Count: {sleep_count}")
    log_print(f"Duration: {duration:.2f} seconds")
    log_print(f"{'='*80}")
    log_print(f"Files saved to: tco_reports/")
    log_print(f"Log saved to: {log_filename}")
    log_print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_print(f"{'='*80}")
    
    # Close log file if it's still open
    if log_file and not log_file.closed:
        log_file.close()

