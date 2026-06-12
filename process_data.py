import os
import pandas as pd
import hashlib
import numpy as np

RAW_DIR = "data"
PROCESSED_DIR = "data/processed"

os.makedirs(PROCESSED_DIR, exist_ok=True)

def get_experiment_group(user_id):
    user_id_str = str(user_id).encode('utf-8')
    hash_val = int(hashlib.md5(user_id_str).hexdigest(), 16)
    return hash_val % 2

def process_chunk(chunk):
    # Handle NaNs in user_id
    chunk['user_id'] = chunk['user_id'].fillna('unknown')
    
    # Assign experiment group (0 for Control, 1 for Treatment)
    chunk['experiment_group'] = chunk['user_id'].apply(get_experiment_group)
    
    # Inject 5% conversion uplift for Treatment group on 'cart' events
    treatment_cart_mask = (chunk['experiment_group'] == 1) & (chunk['event_type'] == 'cart')
    random_probs = np.random.rand(treatment_cart_mask.sum())
    convert_to_purchase = random_probs < 0.05
    
    indices_to_update = chunk[treatment_cart_mask].index[convert_to_purchase]
    chunk.loc[indices_to_update, 'event_type'] = 'purchase'
    
    return chunk

def main():
    for filename in os.listdir(RAW_DIR):
        input_path = os.path.join(RAW_DIR, filename)
        
        # Ensure it's a file and ends with .csv
        if os.path.isfile(input_path) and filename.endswith(".csv"):
            print(f"Processing {filename}...")
            output_path = os.path.join(PROCESSED_DIR, filename)
            
            chunksize = 1000000
            first_chunk = True
            
            try:
                for chunk in pd.read_csv(input_path, chunksize=chunksize):
                    processed_chunk = process_chunk(chunk)
                    mode = 'w' if first_chunk else 'a'
                    header = first_chunk
                    processed_chunk.to_csv(output_path, index=False, mode=mode, header=header)
                    first_chunk = False
                    print(".", end="", flush=True)
                print(f"\nFinished processing {filename}.")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print("All files processed successfully.")

if __name__ == "__main__":
    main()
