"""
Check which LLM providers are being used in analysis.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check_provider_usage():
    """Check recent analysis logs to see which providers were used."""
    
    # Read recent log entries
    log_file = "logs/app.log"
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find lines with "Calling LLM Provider"
        provider_calls = []
        for line in lines:
            if "Calling LLM Provider:" in line:
                # Extract provider name
                parts = line.split("Calling LLM Provider:")
                if len(parts) > 1:
                    provider_info = parts[1].strip().split("|")[0].strip()
                    provider_calls.append(provider_info)
        
        if provider_calls:
            print(f"\n✅ Found {len(provider_calls)} LLM API calls in logs:")
            print(f"Recent providers used: {', '.join(provider_calls[-10:])}")
            
            # Count by provider
            from collections import Counter
            counts = Counter(provider_calls)
            print("\nProvider usage distribution:")
            for provider, count in counts.most_common():
                print(f"  {provider}: {count} calls")
        else:
            print("\n⚠️  No LLM provider calls found in logs yet.")
            print("This might mean:")
            print("  1. Analysis tasks haven't run yet")
            print("  2. All providers are using MOCK responses")
            print("  3. Logs were recently cleared")
    
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_file}")
    except Exception as e:
        print(f"❌ Error reading logs: {e}")

if __name__ == "__main__":
    asyncio.run(check_provider_usage())
