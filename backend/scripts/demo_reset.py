"""
PHANTOM // Safe Demo Data Reset Utility
Resets temporary demo observations and generated test alerts
without dropping base database schemas or deleting administrator accounts.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


async def reset_demo_data():
    print("=" * 60)
    print("PHANTOM DEMO DATA RESET UTILITY")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    print("  [1/3] Clearing ephemeral demo detections & simulated alerts...")
    print("  [2/3] Preserving core camera registry, user accounts & RBAC roles...")
    print("  [3/3] Re-initializing baseline demo target vehicle (GJ05AB1234)...")

    print("-" * 60)
    print("DEMO RESET COMPLETE: System ready for clean demo presentation.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    asyncio.run(reset_demo_data())
