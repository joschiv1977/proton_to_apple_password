# Proton Pass to Apple Passwords Converter

A Python script to convert Proton Pass CSV exports to Apple Password Manager compatible format, handling duplicate URLs and preserving all login information.

## Features

- ✅ Converts Proton Pass CSV to Apple Passwords CSV format
- ✅ Handles multiple accounts for the same website (duplicate URLs)
- ✅ Preserves usernames, passwords, notes, and TOTP/2FA codes
- ✅ Debug mode for troubleshooting
- ✅ Creates backup file for duplicate entries

## Prerequisites

### Installing Python on macOS

Python 3 comes pre-installed on macOS 10.15 and later. To verify:

```bash
python3 --version
```

If you need to install or update Python:

#### Option 1: Official Python Installer (Easiest)
1. Visit [python.org](https://www.python.org/downloads/)
2. Download the latest Python 3 installer for macOS
3. Open the downloaded `.pkg` file and follow the installation steps

#### Option 2: Using Homebrew
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3
```

## Usage

### 1. Export from Proton Pass

1. Open Proton Pass (browser extension or app)
2. Go to **Settings** → **Export**
3. Choose **CSV format**
4. Save the file (e.g., `proton_export.csv`)

### 2. Run the Converter

```bash
# Basic usage
python3 convert_proton_to_apple.py proton_export.csv

# With debug information
python3 convert_proton_to_apple.py proton_export.csv --debug
```

### 3. Import to Apple Passwords

1. Open **Safari** on your Mac
2. Go to **Safari** → **Settings** → **Passwords**
3. Authenticate with Touch ID or password
4. Click the **⋮** (three dots) button → **Import Passwords...**
5. Select `apple_import.csv`
6. Confirm the import

### 4. Clean Up

**⚠️ Important: Delete all CSV files after importing as they contain passwords in plain text!**

```bash
rm proton_export.csv apple_import.csv duplicates_manual_import.csv
```

## How It Works

### Duplicate URL Handling

Apple Passwords ignores entries with identical URLs during import. This script:

1. Detects duplicate URLs
2. Modifies them by adding `?account=2`, `?account=3`, etc.
3. Updates titles to include username for clarity: `GitHub (work@email.com)`
4. Stores original URL in notes field

After import, you can edit the entries in Apple Passwords to remove the `?account=N` parameter.

### Output Files

- `apple_import.csv` - Main file for Apple Passwords import
- `duplicates_manual_import.csv` - List of modified duplicate entries (for reference)

## Troubleshooting

### Missing Usernames

If usernames are not imported correctly:

1. Run with `--debug` flag to see CSV structure analysis
2. Check which column names your Proton Pass export uses
3. The script searches for: username, email, login, user, account, etc.

### Import Fails

- Ensure Safari is updated to the latest version
- Check that the CSV file is not corrupted
- Try importing a smaller test batch first

### Passkeys Not Imported

**Note:** Passkeys cannot be exported/imported due to security design. You must:
1. Sign in to each service
2. Add a new passkey for Apple
3. Remove the old passkey from Proton Pass

## CSV Format

### Expected Apple Password Manager Format
```csv
Title,URL,Username,Password,Notes,OTPAuth
```

### Proton Pass Format (auto-detected)
```csv
name,url,username,password,note,totp
```

## Security Notes

- 🔒 CSV files contain passwords in plain text
- 🗑️ Delete all CSV files immediately after import
- 🔐 Use encrypted storage if you need to keep exports
- 💾 Consider using disk encryption (FileVault) on your Mac

## License

MIT License - Feel free to use and modify

## Contributing

Pull requests welcome! Please test changes with sample data before submitting.

## Support

If you encounter issues:
1. Run with `--debug` flag
2. Check the CSV structure analysis output
3. Ensure Proton Pass export includes all fields
4. Open an issue with debug output (remove sensitive data first!)
