#!/usr/bin/env python3
"""Utility script to regenerate mock data"""

from database.connection import regenerate_mock_data, storage

if __name__ == "__main__":
    print("🔄 Regenerating mock data...")
    regenerate_mock_data()
    print("✅ Done! Fresh mock data has been generated.")
    print(f"\n📊 Database Stats:")
    stats = storage.get_stats()
    for key, value in stats.items():
        print(f"   - {key.title()}: {value}")
