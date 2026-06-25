'''Here we define the CICIDS2017Cleaner class, which is responsible for cleaning 
the CICIDS2017 dataset. The cleaning process includes:
- Removing duplicate rows
- Replacing infinite values with NaN
- Removing rows with missing values
- Normalizing the 'Label' column by stripping whitespace'''
import pandas as pd
import numpy as np

# The CICIDS2017Cleaner class takes a DataFrame as input and provides methods to clean the data according to the specified steps. The run_full_cleaning_pipeline method executes all cleaning steps in sequence and returns the cleaned DataFrame.
class CICIDS2017Cleaner:

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def clean_column_names(self):
        self.df.columns = self.df.columns.str.strip()

    def remove_duplicate_rows(self):
        before = len(self.df)

        self.df = self.df.drop_duplicates()

        after = len(self.df)

        print(f"Removed {before - after} duplicate rows")

    def replace_infinite_values(self):
        self.df.replace([np.inf, -np.inf], np.nan, inplace=True)

    def remove_missing_values(self):
        before = len(self.df)

        self.df.dropna(inplace=True)

        after = len(self.df)

        print(f"Removed {before - after} rows with missing values")

    def normalize_labels(self):
        self.df["Label"] = self.df["Label"].str.strip()

    def remove_invalid_rows(self):

        self.df = self.df[
            self.df["Flow Bytes/s"] != np.inf
        ]

        self.df = self.df[
            self.df["Flow Packets/s"] != np.inf
        ]

    def run_full_cleaning_pipeline(self):

        print("Cleaning column names...")
        self.clean_column_names()

        print("Removing duplicates...")
        self.remove_duplicate_rows()

        print("Replacing infinite values...")
        self.replace_infinite_values()

        print("Removing missing values...")
        self.remove_missing_values()

        print("Normalizing labels...")
        self.normalize_labels()

        print("Removing invalid rows...")
        self.remove_invalid_rows()

        print("Cleaning completed.")

        return self.df