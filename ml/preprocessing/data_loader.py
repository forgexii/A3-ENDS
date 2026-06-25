'''This file contains the data loader for the CICIDS2017 dataset. 
It provides functionality to load all CSV files from a specified 
directory and combine them into a single DataFrame.'''

from pathlib import Path
import pandas as pd

#Load the CICIDS2017 dataset from the specified directory and combine all CSV files into a single DataFrame.
class CICIDS2017Loader:

    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)

    def load_all_csvs(self):
        # Get a list of all CSV files in the dataset directory
        csv_files = list(self.dataset_path.glob("*.csv"))

        dataframes = []

        for file in csv_files:
            try:
                df = pd.read_csv(file)
                dataframes.append(df)
                print(f"Loaded: {file.name}")
            except Exception as e:
                print(f"Error loading {file.name}: {e}")

        combined_df = pd.concat(dataframes, ignore_index=True)

        return combined_df