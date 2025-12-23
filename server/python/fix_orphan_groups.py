#!/usr/bin/env python3
"""
Developer Utility Script: Fix Orphaned Group References

This script identifies and fixes database records that reference non-existent groups,
which causes errors like:
    "insert or update on table 'workshop_documents' violates foreign key constraint"

Usage:
    python fix_orphan_groups.py --check     # Check for orphans (read-only)
    python fix_orphan_groups.py --fix       # Fix orphans interactively
    python fix_orphan_groups.py --auto-fix  # Auto-fix by removing orphans

Environment:
    DATABASE_URL: PostgreSQL connection string (or uses default)
"""

import argparse
import os
import sys
from typing import List, Tuple, Optional

try:
    import psycopg
except ImportError:
    print("Error: psycopg not installed. Run: pip install 'psycopg[binary]'")
    sys.exit(1)

# Default connection string
DEFAULT_DSN = "postgresql://root:secret@localhost:5434/project_monopoly"
DSN = os.getenv("DATABASE_URL", DEFAULT_DSN)


def get_connection():
    """Get a database connection."""
    try:
        return psycopg.connect(DSN, autocommit=True)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print(f"   Connection string: {DSN[:50]}...")
        sys.exit(1)


def get_valid_groups(conn) -> List[Tuple[int, str]]:
    """Get all valid group IDs and names."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM groups ORDER BY id")
        return cur.fetchall()


def check_orphan_user_competitors(conn) -> List[Tuple]:
    """Find user_competitors with non-existent group_id."""
    query = """
        SELECT uc.id, uc.user_id, uc.group_id, uc.competitor_id, c.display_name
        FROM user_competitors uc
        LEFT JOIN groups g ON g.id = uc.group_id
        LEFT JOIN competitors c ON c.id = uc.competitor_id
        WHERE uc.group_id IS NOT NULL AND g.id IS NULL
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def check_orphan_competitor_profiles(conn) -> List[Tuple]:
    """Find competitor_profiles linked to user_competitors with orphan groups."""
    # This is indirect - we check if any competitors are only linked via orphan user_competitors
    query = """
        SELECT DISTINCT cp.id, cp.handle, cp.platform, uc.group_id
        FROM competitor_profiles cp
        JOIN competitors c ON c.id = cp.competitor_id
        JOIN user_competitors uc ON uc.competitor_id = c.id
        LEFT JOIN groups g ON g.id = uc.group_id
        WHERE uc.group_id IS NOT NULL AND g.id IS NULL
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def check_orphan_workshop_docs(conn) -> List[Tuple]:
    """Find workshop_documents with non-existent group_id."""
    query = """
        SELECT wd.id, wd.filename, wd.group_id, wd.user_id
        FROM workshop_documents wd
        LEFT JOIN groups g ON g.id = wd.group_id
        WHERE g.id IS NULL
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def check_orphan_upload_jobs(conn) -> List[Tuple]:
    """Find upload_jobs with non-existent group_id."""
    query = """
        SELECT uj.id, uj.platform, uj.group_id, uj.status
        FROM upload_jobs uj
        LEFT JOIN groups g ON g.id = uj.group_id
        WHERE uj.group_id IS NOT NULL AND g.id IS NULL
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def print_orphan_report(conn):
    """Print a report of all orphaned records."""
    print("\n" + "=" * 60)
    print("🔍 ORPHAN RECORDS REPORT")
    print("=" * 60)

    # Valid groups
    valid_groups = get_valid_groups(conn)
    print(f"\n✅ Valid Groups ({len(valid_groups)} total):")
    if valid_groups:
        for gid, name in valid_groups:
            print(f"   - ID {gid}: {name}")
    else:
        print("   (No groups found)")

    # Check each table
    issues_found = False

    # user_competitors
    orphan_uc = check_orphan_user_competitors(conn)
    if orphan_uc:
        issues_found = True
        print(f"\n⚠️  Orphan user_competitors ({len(orphan_uc)} records):")
        for row in orphan_uc:
            uc_id, user_id, group_id, comp_id, display_name = row
            print(f"   - ID {uc_id}: user_id={user_id}, group_id={group_id} (missing), competitor={display_name}")

    # competitor_profiles affected
    orphan_cp = check_orphan_competitor_profiles(conn)
    if orphan_cp:
        issues_found = True
        print(f"\n⚠️  Affected competitor_profiles ({len(orphan_cp)} profiles):")
        for row in orphan_cp:
            cp_id, handle, platform, group_id = row
            print(f"   - ID {cp_id}: @{handle} ({platform}), linked to missing group_id={group_id}")

    # workshop_documents
    orphan_docs = check_orphan_workshop_docs(conn)
    if orphan_docs:
        issues_found = True
        print(f"\n⚠️  Orphan workshop_documents ({len(orphan_docs)} records):")
        for row in orphan_docs:
            doc_id, filename, group_id, user_id = row
            print(f"   - ID {doc_id}: {filename}, group_id={group_id} (missing)")

    # upload_jobs
    orphan_jobs = check_orphan_upload_jobs(conn)
    if orphan_jobs:
        issues_found = True
        print(f"\n⚠️  Orphan upload_jobs ({len(orphan_jobs)} records):")
        for row in orphan_jobs:
            job_id, platform, group_id, status = row
            print(f"   - ID {job_id}: {platform}, group_id={group_id} (missing), status={status}")

    print("\n" + "-" * 60)
    if not issues_found:
        print("✅ No orphan records found! Database is clean.")
    else:
        print("⚠️  Issues found. Run with --fix or --auto-fix to resolve.")
    print()

    return issues_found


def fix_orphans_interactive(conn):
    """Interactively fix orphan records."""
    valid_groups = get_valid_groups(conn)
    
    if not valid_groups:
        print("❌ No valid groups exist. Create a group first.")
        return

    print("\n📋 Available Groups:")
    for gid, name in valid_groups:
        print(f"   [{gid}] {name}")

    # Fix user_competitors
    orphan_uc = check_orphan_user_competitors(conn)
    if orphan_uc:
        print(f"\n🔧 Fixing {len(orphan_uc)} orphan user_competitors...")
        print("Options:")
        print("   [1] Move all to a valid group")
        print("   [2] Delete orphan records")
        print("   [3] Skip")
        
        choice = input("Choose (1/2/3): ").strip()
        
        if choice == "1":
            target_group = input(f"Enter target group ID ({valid_groups[0][0]}): ").strip()
            target_group = int(target_group) if target_group else valid_groups[0][0]
            
            with conn.cursor() as cur:
                for row in orphan_uc:
                    uc_id = row[0]
                    cur.execute(
                        "UPDATE user_competitors SET group_id = %s WHERE id = %s",
                        (target_group, uc_id)
                    )
            print(f"   ✅ Moved {len(orphan_uc)} records to group {target_group}")
            
        elif choice == "2":
            with conn.cursor() as cur:
                for row in orphan_uc:
                    uc_id = row[0]
                    cur.execute("DELETE FROM user_competitors WHERE id = %s", (uc_id,))
            print(f"   ✅ Deleted {len(orphan_uc)} orphan records")

    # Fix workshop_documents
    orphan_docs = check_orphan_workshop_docs(conn)
    if orphan_docs:
        print(f"\n🔧 Fixing {len(orphan_docs)} orphan workshop_documents...")
        print("Options:")
        print("   [1] Move all to a valid group")
        print("   [2] Delete orphan records")
        print("   [3] Skip")
        
        choice = input("Choose (1/2/3): ").strip()
        
        if choice == "1":
            target_group = input(f"Enter target group ID ({valid_groups[0][0]}): ").strip()
            target_group = int(target_group) if target_group else valid_groups[0][0]
            
            with conn.cursor() as cur:
                for row in orphan_docs:
                    doc_id = row[0]
                    cur.execute(
                        "UPDATE workshop_documents SET group_id = %s WHERE id = %s",
                        (target_group, str(doc_id))
                    )
            print(f"   ✅ Moved {len(orphan_docs)} documents to group {target_group}")
            
        elif choice == "2":
            with conn.cursor() as cur:
                for row in orphan_docs:
                    doc_id = row[0]
                    cur.execute("DELETE FROM workshop_documents WHERE id = %s", (str(doc_id),))
            print(f"   ✅ Deleted {len(orphan_docs)} orphan documents")

    print("\n✅ Fix complete!")


def fix_orphans_auto(conn):
    """Automatically fix orphans by removing them."""
    print("\n🤖 AUTO-FIX MODE: Removing all orphan records...")
    
    total_deleted = 0
    
    # Delete orphan user_competitors
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM user_competitors uc
            USING (
                SELECT uc.id 
                FROM user_competitors uc
                LEFT JOIN groups g ON g.id = uc.group_id
                WHERE uc.group_id IS NOT NULL AND g.id IS NULL
            ) orphans
            WHERE uc.id = orphans.id
            RETURNING uc.id
        """)
        count = cur.rowcount
        if count:
            print(f"   ✅ Deleted {count} orphan user_competitors")
            total_deleted += count

    # Delete orphan workshop_documents
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM workshop_documents wd
            USING (
                SELECT wd.id 
                FROM workshop_documents wd
                LEFT JOIN groups g ON g.id = wd.group_id
                WHERE g.id IS NULL
            ) orphans
            WHERE wd.id = orphans.id
            RETURNING wd.id
        """)
        count = cur.rowcount
        if count:
            print(f"   ✅ Deleted {count} orphan workshop_documents")
            total_deleted += count

    # Delete orphan upload_jobs
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM upload_jobs uj
            WHERE uj.group_id IS NOT NULL 
            AND NOT EXISTS (SELECT 1 FROM groups g WHERE g.id = uj.group_id)
            RETURNING uj.id
        """)
        count = cur.rowcount
        if count:
            print(f"   ✅ Deleted {count} orphan upload_jobs")
            total_deleted += count

    print(f"\n✅ Auto-fix complete. Total deleted: {total_deleted} records")


def create_missing_group(conn, group_id: int, group_name: str, user_id: int):
    """Create a missing group to fix orphan references."""
    with conn.cursor() as cur:
        # Check if we can insert with specific ID
        cur.execute("""
            INSERT INTO groups (id, user_id, name, description)
            VALUES (%s, %s, %s, 'Auto-created to fix orphan references')
            ON CONFLICT (id) DO NOTHING
            RETURNING id
        """, (group_id, user_id, group_name))
        result = cur.fetchone()
        if result:
            # Fix the sequence
            cur.execute("SELECT setval('groups_id_seq', GREATEST((SELECT MAX(id) FROM groups), %s))", (group_id,))
            print(f"   ✅ Created group ID {group_id}: {group_name}")
            return True
        else:
            print(f"   ⚠️  Group ID {group_id} already exists or couldn't be created")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix orphaned group references in the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fix_orphan_groups.py --check         Check for orphans
    python fix_orphan_groups.py --fix           Fix interactively
    python fix_orphan_groups.py --auto-fix      Auto-delete orphans
    python fix_orphan_groups.py --create-group 2 "Missing Group" 1
                                                Create missing group
        """
    )
    
    parser.add_argument("--check", action="store_true", help="Check for orphan records (read-only)")
    parser.add_argument("--fix", action="store_true", help="Fix orphans interactively")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix by removing orphans")
    parser.add_argument("--create-group", nargs=3, metavar=("ID", "NAME", "USER_ID"),
                        help="Create a missing group: --create-group 2 'My Group' 1")

    args = parser.parse_args()

    if not any([args.check, args.fix, args.auto_fix, args.create_group]):
        parser.print_help()
        sys.exit(0)

    print(f"🔌 Connecting to database...")
    conn = get_connection()
    print(f"✅ Connected successfully")

    try:
        if args.check:
            print_orphan_report(conn)
        
        elif args.fix:
            has_issues = print_orphan_report(conn)
            if has_issues:
                confirm = input("\nProceed with interactive fix? (y/N): ")
                if confirm.lower() == 'y':
                    fix_orphans_interactive(conn)
        
        elif args.auto_fix:
            has_issues = print_orphan_report(conn)
            if has_issues:
                confirm = input("\n⚠️  This will DELETE orphan records. Are you sure? (yes/N): ")
                if confirm.lower() == 'yes':
                    fix_orphans_auto(conn)
                else:
                    print("Aborted.")
        
        elif args.create_group:
            group_id, group_name, user_id = args.create_group
            create_missing_group(conn, int(group_id), group_name, int(user_id))
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
