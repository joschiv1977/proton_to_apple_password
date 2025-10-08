#!/usr/bin/env python3
import csv
import sys
import os
from collections import defaultdict
from urllib.parse import urlparse, urlunparse

def analyze_csv_structure(input_file):
    """
    Analyzes the CSV structure to show what columns are available
    """
    print("\n📋 Analyzing CSV structure...")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        first_row = next(reader, None)
        if first_row:
            print("\nFound columns:")
            for key, value in first_row.items():
                sample = value[:50] + "..." if len(value) > 50 else value
                print(f"  - '{key}': '{sample}'")
            return first_row.keys()
    return []

def convert_proton_to_apple(input_file, output_file):
    """
    Converts Proton Pass CSV to Apple Password Manager format
    Handles duplicate URLs by modifying them to ensure all logins are imported
    """
    
    # First analyze the CSV structure
    columns = analyze_csv_structure(input_file)
    
    # Track URLs to detect duplicates
    url_counts = defaultdict(int)
    apple_rows = []
    duplicates_file = "duplicates_manual_import.csv"
    duplicate_rows = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Possible column names in Proton Pass (case-insensitive)
        # Extended list to catch all variations
        name_fields = ['name', 'title', 'item name', 'itemname']
        url_fields = ['url', 'website', 'urls', 'web site', 'web address']
        user_fields = ['username', 'email', 'login', 'user', 'user name', 'loginname', 
                      'login name', 'account', 'userid', 'user id']
        pass_fields = ['password', 'pass', 'passwd', 'pw']
        note_fields = ['note', 'notes', 'description', 'comment', 'comments']
        totp_fields = ['totp', 'otp', '2fa', 'two-factor', 'twofactor', 'mfa']
        
        entries = []
        missing_usernames = 0
        
        # Process each row
        for row_num, row in enumerate(reader, start=2):  # start=2 because line 1 is header
            # Debug first few rows
            if row_num <= 4:
                print(f"\n🔍 Row {row_num-1} raw data:")
                for k, v in row.items():
                    if v:  # Only show non-empty fields
                        print(f"   {k}: {v[:30]}...")
            
            # Make a case-insensitive version of the row
            row_lower = {}
            row_original = {}
            for k, v in row.items():
                k_lower = k.lower().strip()
                row_lower[k_lower] = v
                row_original[k] = v  # Keep original for exact match
            
            # Extract values - try exact match first, then fuzzy match
            title = ""
            url = ""
            username = ""
            password = ""
            notes = ""
            otpauth = ""
            
            # Try to find each field - prioritize exact column names from original CSV
            # Title
            for field in name_fields:
                if field in row_lower and row_lower[field]:
                    title = row_lower[field]
                    break
            
            # URL
            for field in url_fields:
                if field in row_lower and row_lower[field]:
                    url = row_lower[field]
                    break
            
            # Username - THIS IS CRITICAL
            # Check exact matches first
            if 'Username' in row_original and row_original['Username']:
                username = row_original['Username']
            elif 'username' in row_lower and row_lower['username']:
                username = row_lower['username']
            else:
                # Try all variations
                for field in user_fields:
                    if field in row_lower and row_lower[field]:
                        username = row_lower[field]
                        break
            
            # If still no username, check if email field exists
            if not username:
                for k in row_lower:
                    if 'email' in k or 'mail' in k:
                        if row_lower[k]:
                            username = row_lower[k]
                            break
            
            # Password
            for field in pass_fields:
                if field in row_lower and row_lower[field]:
                    password = row_lower[field]
                    break
            
            # Notes
            for field in note_fields:
                if field in row_lower and row_lower[field]:
                    notes = row_lower[field]
                    break
            
            # TOTP/OTP
            for field in totp_fields:
                if field in row_lower and row_lower[field]:
                    otpauth = row_lower[field]
                    break
            
            # If no title, use URL as title
            if not title and url:
                title = url.replace('https://', '').replace('http://', '').split('/')[0]
            
            # Format OTP Auth URL if only secret is present
            if otpauth and not otpauth.startswith('otpauth://'):
                if title:
                    otpauth = f'otpauth://totp/{title}?secret={otpauth}'
                else:
                    otpauth = f'otpauth://totp/Account?secret={otpauth}'
            
            # Track missing usernames
            if not username:
                missing_usernames += 1
                print(f"⚠️  Row {row_num-1}: No username found for {title or url}")
            
            entries.append({
                'Title': title,
                'URL': url,
                'Username': username,  # This should now have the value!
                'Password': password,
                'Notes': notes,
                'OTPAuth': otpauth
            })
        
        print(f"\n📊 Username statistics:")
        print(f"   Total entries: {len(entries)}")
        print(f"   Missing usernames: {missing_usernames}")
        print(f"   With usernames: {len(entries) - missing_usernames}")
        
        # Second pass: handle duplicates
        for entry in entries:
            url = entry['URL']
            
            if url:
                # Count occurrences
                url_counts[url] += 1
                count = url_counts[url]
                
                if count > 1:
                    # Duplicate found - modify URL to make it unique
                    if '?' in url:
                        modified_url = f"{url}&account={count}"
                    else:
                        modified_url = f"{url}?account={count}"
                    
                    # Update title to indicate which account
                    if entry['Username']:
                        entry['Title'] = f"{entry['Title']} ({entry['Username']})"
                    else:
                        entry['Title'] = f"{entry['Title']} (Account {count})"
                    
                    # Add note about original URL
                    original_note = entry['Notes']
                    entry['Notes'] = f"Original URL: {url}\n{original_note}" if original_note else f"Original URL: {url}"
                    
                    # Use modified URL for import
                    entry['URL'] = modified_url
                    
                    # Save to duplicates file for reference
                    duplicate_rows.append(entry.copy())
            
            apple_rows.append(entry)
    
    # Write main Apple format file
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Title', 'URL', 'Username', 'Password', 'Notes', 'OTPAuth']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(apple_rows)
    
    print(f"\n✅ Converted: {len(apple_rows)} entries")
    print(f"📁 Main file: {output_file}")
    
    # Show sample of output to verify
    print("\n🔍 Sample of output (first 3 entries):")
    for i, entry in enumerate(apple_rows[:3]):
        print(f"\nEntry {i+1}:")
        print(f"  Title: {entry['Title']}")
        print(f"  URL: {entry['URL']}")
        print(f"  Username: {entry['Username']}")  # This should show the username!
        print(f"  Password: {'*' * min(len(entry['Password']), 8) if entry['Password'] else '(empty)'}")
    
    # Write duplicates file if any duplicates found
    if duplicate_rows:
        with open(duplicates_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['Title', 'URL', 'Username', 'Password', 'Notes', 'OTPAuth']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(duplicate_rows)
        print(f"\n⚠️  Found {len(duplicate_rows)} duplicate URLs - modified for import")
        print(f"📁 Duplicates saved to: {duplicates_file}")
    
    # Summary of URLs with multiple accounts
    multi_account_sites = {url: count for url, count in url_counts.items() if count > 1}
    if multi_account_sites:
        print("\n📊 Sites with multiple accounts:")
        for url, count in sorted(multi_account_sites.items(), key=lambda x: x[1], reverse=True):
            domain = urlparse(url).netloc or url
            print(f"  - {domain}: {count} accounts")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_proton_to_apple.py proton_export.csv [--debug]")
        print("Output will be saved as 'apple_import.csv'")
        print("Duplicates will be saved to 'duplicates_manual_import.csv'")
        print("\nAdd --debug flag to see detailed column analysis")
        sys.exit(1)
    
    input_file = sys.argv[1]
    debug_mode = "--debug" in sys.argv
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    output_file = "apple_import.csv"
    
    if debug_mode:
        print("🔧 Debug mode enabled\n")
    
    convert_proton_to_apple(input_file, output_file)
    
    print("\n⚠️  IMPORTANT:")
    print("1. Import 'apple_import.csv' in Safari → Settings → Passwords")
    print("2. For duplicate URLs: They have been modified with ?account=N")
    print("3. After import, edit entries in Apple Passwords to remove the URL parameter")
    print("4. DELETE all CSV files after import!")
    print("5. Passkeys must be recreated manually")
    print("\n❓ If usernames are missing:")
    print("   - Check the CSV structure analysis above")
    print("   - Run with --debug flag for more details")
    print("   - Ensure Proton Pass export includes username field")
