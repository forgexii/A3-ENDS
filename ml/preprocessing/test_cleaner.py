from data_loader import CICIDS2017Loader
from data_cleaner import CICIDS2017Cleaner


loader = CICIDS2017Loader(
    "../../datasets/raw/CICIDS2017"
)

df = loader.load_all_csvs()

print("Original Shape:")
print(df.shape)

cleaner = CICIDS2017Cleaner(df)

clean_df = cleaner.run_full_cleaning_pipeline()

print("Cleaned Shape:")
print(clean_df.shape)

print(clean_df["Label"].value_counts())