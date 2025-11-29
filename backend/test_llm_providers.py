"""
Test script for LLM client with multiple providers.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.core.llm_client import llm_client
from app.core.logger import logger

async def test_provider(provider_name: str):
    """Test a specific LLM provider."""
    print(f"\n{'='*60}")
    print(f"Testing Provider: {provider_name.upper()}")
    print(f"{'='*60}")
    
    messages = [
        {"role": "system", "content": "你是一个专业的新闻分析助手。"},
        {"role": "user", "content": "请分析以下新闻的情感倾向，给出-100到100之间的分数：\n标题：全球经济复苏加速，多国GDP增长超预期\n内容：最新数据显示，全球主要经济体在第三季度表现强劲...\n\n只返回一个整数分数。"}
    ]
    
    try:
        response = await llm_client.chat_completion(
            messages=messages,
            provider=provider_name,
            temperature=0.3,
            max_tokens=50
        )
        
        if response:
            print(f"✅ SUCCESS - Response: {response}")
            return True
        else:
            print(f"❌ FAILED - No response received")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

async def main():
    print("\n" + "="*60)
    print("SmartInsight Global - LLM Provider Test Suite")
    print("="*60)
    
    # Get available providers
    available = llm_client.get_available_providers()
    print(f"\nAvailable Providers: {', '.join(available)}")
    
    # Test each provider
    results = {}
    for provider in llm_client.PROVIDERS.keys():
        success = await test_provider(provider)
        results[provider] = success
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for provider, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{provider:15} {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    print(f"\nTotal: {success_count}/{total_count} providers working")

if __name__ == "__main__":
    asyncio.run(main())
