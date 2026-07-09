"""
Remove all files with _MISMATCH in their name from the pricedata folder
"""
import os
import glob

def remove_mismatch_files():
    # Path to the pricedata folder
    pricedata_dir = "pricedata"
    
    if not os.path.exists(pricedata_dir):
        print(f"Error: Directory '{pricedata_dir}' does not exist.")
        return
    
    # Find all files with _MISMATCH in their name
    mismatch_files = glob.glob(os.path.join(pricedata_dir, "*_MISMATCH.json"))
    
    if not mismatch_files:
        print("No mismatch files found.")
        return
    
    print(f"Found {len(mismatch_files)} files with _MISMATCH")
    
    # Confirm before deleting
    confirm = input(f"\nAre you sure you want to DELETE {len(mismatch_files)} files? (yes/no): ")
    if confirm.lower() != "yes":
        print("Deletion cancelled.")
        return
    
    # Delete the files
    deleted_count = 0
    failed_count = 0
    
    for filepath in mismatch_files:
        try:
            os.remove(filepath)
            deleted_count += 1
            filename = os.path.basename(filepath)
            print(f"Deleted: {filename}")
        except Exception as e:
            failed_count += 1
            print(f"Failed to delete {filepath}: {e}")
    
    print(f"\n=== Deletion Summary ===")
    print(f"Successfully deleted: {deleted_count}")
    print(f"Failed to delete: {failed_count}")
    print(f"Total processed: {len(mismatch_files)}")

if __name__ == "__main__":
    remove_mismatch_files()
