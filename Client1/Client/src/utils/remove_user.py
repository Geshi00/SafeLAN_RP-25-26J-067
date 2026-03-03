import os
import shutil

def remove_user(user_id):
    """
    Deletes all files associated with a specific user profile.
    """
    # Define paths to search for user-specific files
    paths = [
        f'data/raw/{user_id}_raw.json',
        f'data/processed/{user_id}_features.csv',
        f'data/processed/{user_id}_raw_seconds.csv',
        f'models/classifiers/{user_id}_svm.pkl',
        f'models/scalers/{user_id}_scaler.pkl',
        f'models/scalers/{user_id}_context.pkl'
    ]

    print(f"--- Removing User Profile: {user_id} ---")
    files_removed = 0

    for path in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"🗑️ Deleted: {path}")
                files_removed += 1
            except Exception as e:
                print(f"❌ Error deleting {path}: {e}")
        else:
            print(f"🔍 Not found: {path}")

    if files_removed > 0:
        print(f"\n✅ Success: {user_id} has been completely removed from the system.")
    else:
        print(f"\n⚠️ Warning: No data found for user '{user_id}'.")

if __name__ == "__main__":
    uid = input("Enter the Username you want to remove: ").strip()
    if uid:
        confirm = input(f"Are you sure you want to delete all data for '{uid}'? (y/n): ").lower()
        if confirm == 'y':
            remove_user(uid)
        else:
            print("Operation cancelled.")