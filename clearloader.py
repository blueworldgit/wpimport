#!/usr/bin/env python3
"""
Clear Loader - Reset all checkpoints, cache, and temporary data for fresh testing
Usage: python clearloader.py
"""

import os
import shutil
import glob
import json
from pathlib import Path

def clear_checkpoints():
    """Clear all checkpoint files"""
    checkpoint_dir = Path("data/checkpoints")
    if checkpoint_dir.exists():
        print("🗑️  Clearing checkpoints...")
        for checkpoint_file in checkpoint_dir.glob("*.json"):
            try:
                os.remove(checkpoint_file)
                print(f"   ✓ Removed {checkpoint_file}")
            except Exception as e:
                print(f"   ❌ Failed to remove {checkpoint_file}: {e}")
    else:
        print("   ℹ️  No checkpoint directory found")

def clear_cache():
    """Clear Python cache files"""
    print("🗑️  Clearing Python cache...")
    
    # Clear __pycache__ directories
    for pycache_dir in Path(".").rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            print(f"   ✓ Removed {pycache_dir}")
        except Exception as e:
            print(f"   ❌ Failed to remove {pycache_dir}: {e}")
    
    # Clear .pyc files
    for pyc_file in Path(".").rglob("*.pyc"):
        try:
            os.remove(pyc_file)
            print(f"   ✓ Removed {pyc_file}")
        except Exception as e:
            print(f"   ❌ Failed to remove {pyc_file}: {e}")

def clear_logs():
    """Clear log files"""
    logs_dir = Path("logs")
    if logs_dir.exists():
        print("🗑️  Clearing logs...")
        for log_file in logs_dir.glob("*.log"):
            try:
                os.remove(log_file)
                print(f"   ✓ Removed {log_file}")
            except Exception as e:
                print(f"   ❌ Failed to remove {log_file}: {e}")
        
        # Clear any log subdirectories
        for log_subdir in logs_dir.iterdir():
            if log_subdir.is_dir():
                try:
                    shutil.rmtree(log_subdir)
                    print(f"   ✓ Removed {log_subdir}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {log_subdir}: {e}")
    else:
        print("   ℹ️  No logs directory found")

def clear_temp_data():
    """Clear temporary extracted data files"""
    extracted_dir = Path("data/extracted")
    if extracted_dir.exists():
        print("🗑️  Clearing temporary extracted data...")
        temp_files = [
            "extracted_data_test.json",
            "test_10products.json",
        ]
        
        for temp_file in temp_files:
            file_path = extracted_dir / temp_file
            if file_path.exists():
                try:
                    os.remove(file_path)
                    print(f"   ✓ Removed {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {file_path}: {e}")
    else:
        print("   ℹ️  No extracted data directory found")

def clear_converted_images():
    """Clear converted images (optional - comment out if you want to keep them)"""
    converted_dir = Path("images/converted")
    if converted_dir.exists():
        print("🗑️  Clearing converted images...")
        for img_file in converted_dir.glob("*"):
            if img_file.is_file():
                try:
                    os.remove(img_file)
                    print(f"   ✓ Removed {img_file}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {img_file}: {e}")
    else:
        print("   ℹ️  No converted images directory found")

def create_fresh_checkpoint():
    """Create a fresh, empty checkpoint structure"""
    checkpoint_dir = Path("data/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    fresh_checkpoint = {
        "products_created": 0,
        "last_processed_serial": None,
        "categories_created": {},
        "failed_products": [],
        "timestamp": None
    }
    
    checkpoint_file = checkpoint_dir / "import_checkpoint.json"
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump(fresh_checkpoint, f, indent=2)
        print(f"   ✓ Created fresh checkpoint: {checkpoint_file}")
    except Exception as e:
        print(f"   ❌ Failed to create fresh checkpoint: {e}")

def main():
    print("🧹 Clear Loader - Resetting for fresh testing...")
    print("=" * 50)
    
    # Clear all data
    clear_checkpoints()
    clear_cache()
    clear_logs()
    clear_temp_data()
    
    # Uncomment the next line if you want to clear converted images too
    # clear_converted_images()
    
    # Create fresh checkpoint
    print("🔄 Creating fresh checkpoint structure...")
    create_fresh_checkpoint()
    
    print("=" * 50)
    print("✅ Clear Loader complete! Ready for fresh testing.")
    print()
    print("📝 Next steps:")
    print("   1. Manually clear WP products (as you're already doing)")
    print("   2. Run your import script with fresh state")
    print()

if __name__ == "__main__":
    main()