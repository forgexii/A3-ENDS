import os
import glob
import pandas as pd
import numpy as np
from pathlib import Path

# ==========================================
# PATHS
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "CICIDS2017"
OUTPUT_DIR = PROJECT_ROOT / "cleaned_cicids2017"
OUTPUT_FILE = OUTPUT_DIR / "cleaned_cicids2017.csv"

def clean_and_combine():
    print(f"Looking for raw CSV files in {RAW_DIR}...")
    csv_files = glob.glob(str(RAW_DIR / "*.csv"))
    
    if not csv_files:
        print("No CSV files found!")
        return

    print(f"Found {len(csv_files)} files. Starting processing...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Remove existing output file if it exists
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    first_file = True
    total_rows = 0
    total_dropped = 0

    for file in csv_files:
        print(f"\nProcessing: {os.path.basename(file)}")
        
        try:
            # Read CSV
            df = pd.read_csv(file, low_memory=False)
            initial_len = len(df)
            
            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()
            
            # Replace infinity with NaN
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            
            # Drop rows with missing values
            df.dropna(inplace=True)
            
            # Track stats
            final_len = len(df)
            dropped = initial_len - final_len
            total_rows += final_len
            total_dropped += dropped
            
            print(f"  > Initial rows: {initial_len:,}")
            print(f"  > Dropped rows (NaN/Inf): {dropped:,}")
            print(f"  > Kept rows: {final_len:,}")

            # Append to master CSV
            # Mode 'a' to append, write header only if it's the first file
            df.to_csv(OUTPUT_FILE, mode='a', index=False, header=first_file)
            first_file = False
            
        except Exception as e:
            print(f"Error processing {file}: {e}")

    print("\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)
    print(f"Total Rows Kept: {total_rows:,}")
    print(f"Total Rows Dropped: {total_dropped:,}")
    print(f"Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_and_combine()
