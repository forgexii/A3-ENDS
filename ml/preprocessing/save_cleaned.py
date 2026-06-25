'''Data Cleaning Script for CICIDS2017 Dataset'''

from data_loader import CICIDS2017Loader
from data_cleaner import CICIDS2017Cleaner


loader = CICIDS2017Loader(
    "../../datasets/raw/CICIDS2017"
)

df = loader.load_all_csvs()

cleaner = CICIDS2017Cleaner(df)

clean_df = cleaner.run_full_cleaning_pipeline()

output_path = "../../datasets/processed/CICIDS2017/cleaned_cicids2017.csv"

clean_df.to_csv(output_path, index=False)

print(f"Saved cleaned dataset to: {output_path}")