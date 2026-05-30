#!/usr/bin/env python3
"""
TCO Modification and Upload Script
Modifies 'Cost per Metering Unit' values in TCO Excel files and uploads them back to the API
"""
import sys
import os
import glob

# Add parent directory to path to import from download_TCO
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_TCO import process_tco_modification, log_print, log_file, log_filename
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='Modify and upload TCO Excel files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Modify the most recent TCO file with ±1 change
  %(prog)s
  
  # Modify a specific file with ±5 change
  %(prog)s --file tco_reports/tco_report_1_20251124_071526.xls --change 5
  
  # Process all TCO files in the directory
  %(prog)s --all --change 2
        '''
    )
    
    parser.add_argument(
        '--file', '-f',
        help='Path to specific TCO Excel file to modify',
        default=None
    )
    
    parser.add_argument(
        '--change', '-c',
        type=float,
        help='Amount to add/subtract from Cost per Metering Unit (default: 1)',
        default=1
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Process all TCO files in tco_reports directory'
    )
    
    args = parser.parse_args()
    
    # Determine which files to process
    files_to_process = []
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"✗ Error: File not found: {args.file}")
            return 1
        files_to_process = [args.file]
    elif args.all:
        files_to_process = sorted(glob.glob("tco_reports/*.xls"))
        # Exclude modified files
        files_to_process = [f for f in files_to_process if '_modified_' not in f]
    else:
        # Default: use the most recent file
        files = sorted(glob.glob("tco_reports/*.xls"), key=os.path.getmtime, reverse=True)
        # Exclude modified files
        files = [f for f in files if '_modified_' not in f]
        if files:
            files_to_process = [files[0]]
        else:
            print("✗ Error: No TCO files found in tco_reports/ directory")
            print("  Run download_TCO.py first to download TCO files")
            return 1
    
    if not files_to_process:
        print("✗ Error: No files to process")
        return 1
    
    print(f"\n{'='*80}")
    print(f"TCO MODIFICATION SCRIPT")
    print(f"{'='*80}")
    print(f"Files to process: {len(files_to_process)}")
    print(f"Change amount: ±{args.change}")
    print(f"{'='*80}\n")
    
    success_count = 0
    failed_count = 0
    
    for file_path in files_to_process:
        print(f"\nProcessing: {file_path}")
        print("-" * 80)
        
        try:
            success, message = process_tco_modification(file_path, change_amount=args.change)
            
            if success:
                print(f"✓ Success: {os.path.basename(file_path)}")
                success_count += 1
            else:
                print(f"✗ Failed: {os.path.basename(file_path)}")
                print(f"  Reason: {message}")
                failed_count += 1
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {str(e)}")
            failed_count += 1
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total files processed: {len(files_to_process)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"{'='*80}")
    print(f"Log file: {log_filename}")
    print(f"{'='*80}\n")
    
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

