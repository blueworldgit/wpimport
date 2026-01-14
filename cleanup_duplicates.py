#!/usr/bin/env python3
"""Clean up duplicate child categories in Oscar database"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator

def main():
    print("🔍 Oscar Database Duplicate Cleanup")
    print("=" * 50)
    
    # Create an instance to get database connection
    creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
    if not creator.connect():
        print("❌ Failed to connect to database")
        return False

    cursor = creator.conn.cursor()

    # Check current state
    cursor.execute("""
        SELECT COUNT(*) as total_children
        FROM motorpartsdata_serialnumber sn
        JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
        JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
        WHERE sn.serial = %s
    """, ('LSFAL11A4PA157987',))
    
    total_before = cursor.fetchone()[0]
    print(f"📊 Current state: {total_before} child records")
    
    # Identify duplicates to remove (keep lower IDs, remove higher IDs)
    cursor.execute("""
        SELECT 
            ct1.id as keep_id,
            ct2.id as remove_id,
            ct1.title as category_name
        FROM motorpartsdata_serialnumber sn
        JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
        JOIN motorpartsdata_childtitle ct1 ON ct1.parent_id = pt.id
        JOIN motorpartsdata_childtitle ct2 ON ct2.parent_id = pt.id 
        WHERE sn.serial = %s
        AND ct1.title = ct2.title
        AND ct1.id < ct2.id
        ORDER BY ct1.title
    """, ('LSFAL11A4PA157987',))
    
    duplicates = cursor.fetchall()
    print(f"📂 Found {len(duplicates)} duplicate pairs to clean up")
    
    if len(duplicates) == 0:
        print("✅ No duplicates found - database is clean!")
        cursor.close()
        creator.conn.close()
        return True
    
    print(f"\n⚠️  This will remove {len(duplicates)} duplicate child category records")
    print("   (Keeping lower IDs, removing higher IDs)")
    
    # Show a few examples
    print("\n📋 Examples of what will be removed:")
    for i, (keep_id, remove_id, category_name) in enumerate(duplicates[:5]):
        print(f"   • '{category_name}': Keep ID {keep_id}, Remove ID {remove_id}")
    if len(duplicates) > 5:
        print(f"   ... and {len(duplicates) - 5} more")
    
    response = input("\n🤔 Proceed with cleanup? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Cleanup cancelled")
        cursor.close()
        creator.conn.close()
        return False
    
    print(f"\n🧹 Cleaning up {len(duplicates)} duplicate records...")
    
    # Check for any part references that would be orphaned
    remove_ids = [str(remove_id) for _, remove_id, _ in duplicates]
    cursor.execute(f"""
        SELECT COUNT(*) as orphaned_parts
        FROM motorpartsdata_part p
        WHERE p.child_title_id IN ({','.join(remove_ids)})
    """)
    
    orphaned_parts = cursor.fetchone()[0]
    if orphaned_parts > 0:
        print(f"⚠️  Found {orphaned_parts} parts that reference duplicate categories")
        print("   These need to be reassigned to the kept category IDs first")
        
        # Reassign parts to the kept category IDs
        print("🔄 Reassigning parts to kept category IDs...")
        for keep_id, remove_id, category_name in duplicates:
            cursor.execute("""
                UPDATE motorpartsdata_part 
                SET child_title_id = %s 
                WHERE child_title_id = %s
            """, (keep_id, remove_id))
        print(f"✅ Reassigned {orphaned_parts} parts to kept categories")
    
    # Now remove the duplicate child categories
    removed_count = 0
    for keep_id, remove_id, category_name in duplicates:
        cursor.execute("""
            DELETE FROM motorpartsdata_childtitle 
            WHERE id = %s
        """, (remove_id,))
        removed_count += 1
        if removed_count % 20 == 0:
            print(f"   🗑️  Removed {removed_count}/{len(duplicates)} duplicates...")
    
    # Commit the changes
    creator.conn.commit()
    print(f"✅ Successfully removed {removed_count} duplicate child categories")
    
    # Verify final state
    cursor.execute("""
        SELECT COUNT(*) as total_children
        FROM motorpartsdata_serialnumber sn
        JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
        JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
        WHERE sn.serial = %s
    """, ('LSFAL11A4PA157987',))
    
    total_after = cursor.fetchone()[0]
    print(f"📊 Final state: {total_after} child records (was {total_before})")
    print(f"🎯 Removed: {total_before - total_after} duplicates")
    
    cursor.close()
    creator.conn.close()
    
    return True

if __name__ == "__main__":
    main()