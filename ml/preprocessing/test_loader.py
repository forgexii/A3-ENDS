'''Here we test the data loader for the CICIDS2017 dataset. 
We load all CSV files from the specified directory 
and combine them into a single DataFrame. 
We then print the shape and the first few rows of the DataFrame to verify that 
it has been loaded correctly.'''

from data_loader import CICIDS2017Loader

loader = CICIDS2017Loader(
    "../../datasets/raw/CICIDS2017"
)

df = loader.load_all_csvs()

print(df.shape)

print(df.head())