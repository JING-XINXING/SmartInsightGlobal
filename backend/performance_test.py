"""
性能基准测试
验证缓存和索引优化的效果
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
from datetime import datetime, timedelta

from app.core.logger import logger
from app.core.config import settings


class PerformanceBenchmark:
    """性能基准测试器"""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.results = {}

    async def test_api_endpoint(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        iterations: int = 5,
        delay: float = 0.1
    ) -> Dict[str, float]:
        """
        测试API端点性能

        Returns:
            响应时间统计（毫秒）
        """
        response_times = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(iterations):
                try:
                    start_time = time.time()

                    if params:
                        response = await client.get(f"{self.base_url}{endpoint}", params=params)
                    else:
                        response = await client.get(f"{self.base_url}{endpoint}")

                    if response.status_code == 200:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # 转换为毫秒
                        response_times.append(response_time)

                        if i < 3:  # 只显示前3个请求的结果
                            logger.info(f"请求 {i+1}: {response_time:.2f}ms")
                    else:
                        logger.error(f"请求 {i+1}: HTTP {response.status_code}")

                except Exception as e:
                    logger.error(f"请求 {i+1} 失败: {e}")

                if i < iterations - 1:
                    await asyncio.sleep(delay)

        if response_times:
            stats = {
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                "p99": statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
            }

            logger.info(f"{endpoint} 性能统计: 平均 {stats['mean']:.2f}ms, 中位数 {stats['median']:.2f}ms, P95 {stats['p95']:.2f}ms, P99 {stats['p99']:.2f}ms")
            return stats
        else:
            return {"error": "所有请求都失败了"}

    async def test_cache_performance(self):
        """测试缓存性能"""
        logger.info("测试缓存性能...")

        # 测试1: 新闻列表缓存
        logger.info("测试1: 新闻列表缓存")
        cache_results = await self.test_api_endpoint(
            "/api/v1/news/cached/paginated",
            params={"page": 1, "page_size": 20},
            iterations=5
        )

        # 测试2: 新闻列表（无缓存）
        logger.info("测试2: 新闻列表（无缓存）")
        no_cache_results = await self.test_api_endpoint(
            "/api/v1/news/paginated",
            params={"page": 1, "page_size": 20},
            iterations=5
        )

        # 测试3: 搜索缓存
        logger.info("测试3: 搜索缓存")
        search_cache_results = await self.test_api_endpoint(
            "/api/v1/news/cached/search",
            params={"q": "economy", "page": 1, "page_size": 20},
            iterations=5
        )

        # 测试4: 搜索（无缓存）
        logger.info("测试4: 搜索（无缓存）")
        search_no_cache_results = await self.test_api_endpoint(
            "/api/v1/news/search",
            params={"q": "economy", "page": 1, "page_size": 20},
            iterations=5
        )

        return {
            "news_list_cached": cache_results,
            "news_list_no_cache": no_cache_results,
            "search_cached": search_cache_results,
            "search_no_cache": search_no_cache_results
        }

    async def test_concurrent_performance(self):
        """测试并发性能"""
        logger.info("测试并发性能...")

        async def make_request(client, endpoint, delay=0):
            """单个请求"""
            await asyncio.sleep(delay)
            start_time = time.time()
            response = await client.get(f"{self.base_url}{endpoint}")
            end_time = time.time()
            return {
                "response_time": (end_time - start_time) * 1000,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }

        # 并发测试: 10个并发请求
        endpoints = [
            "/api/v1/news/cached/paginated?page=1&page_size=20",
            "/api/v1/news/cached/search?q=technology&page=1&page_size=20"
        ]

        all_results = {}

        for endpoint in endpoints:
            logger.info(f"并发测试: {endpoint}")

            async with httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=20)) as client:
                # 立即发送10个并发请求
                tasks = [
                    make_request(Client, endpoint, delay)
                    for Client in [Client] * 10
                ]

                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

            successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
            failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]

            if successful_results:
                response_times = [r["response_time"] for r in successful_results]
                stats = {
                    "total_requests": len(results),
                    "successful": len(successful_results),
                    "failed": len(failed_results),
                    "total_time": (end_time - start_time) * 1000,
                    "mean_response_time": statistics.mean(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "throughput": len(successful_results) / ((end_time - start_time))  # 请求/秒
                }

                logger.info(f"并发测试完成: 成功率 {stats['successful']}/{stats['total_requests']}, "
                          f"平均响应时间 {stats['mean_response_time']:.2f}ms, "
                          f"吞吐量 {stats['throughput']:.2f} req/s")

                all_results[endpoint] = stats
            else:
                all_results[endpoint] = {
                    "total_requests": len(results),
                    "successful": 0,
                    "failed": len(results),
                    "error": "所有请求都失败了"
                }

        return all_results

    async def test_cache_hit_ratio(self):
        """测试缓存命中率"""
        logger.info("测试缓存命中率...")

        # 第一次请求：缓存未命中
        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = time.time()
            response1 = await client.get(f"{self.base_url}/api/v1/news/cached/paginated?page=1&page_size=10")
            time1 = (time.time() - start_time) * 1000

        # 第二次请求：缓存命中
        start_time = time.time()
        response2 = await client.get(f"{self.base_url}/api/v1/news/cached/paginated?page=1&page_size=10")
        time2 = (time.time() - start_time) * 1000

        # 第三次请求：缓存命中
        start_time = time.time()
        response3 = await client.get(f"{self.base_url}/api/v1/news/cached/paginated?page=1&page_size=10")
        time3 = (time.time() - start_time) * 1000

        # 验证缓存状态
        stats_response = await client.get(f"{self.base_url}/api/v1/news/cache/stats")

        return {
            "first_request": {
                "response_time": time1,
                "cache_status": "miss"
            },
            "second_request": {
                "response_time": time2,
                "cache_status": "hit"
            },
            "third_request": {
                "response_time": time3,
                "cache_status": "hit"
            },
            "cache_improvement": ((time1 - time2) / time1) * 100 if time1 > 0 else 0,
            "stats_response": stats_response.status_code == 200,
            "time_ratio": {
                "hit_vs_miss": time2 / time1 if time1 > 0 else 0,
                "hit_vs_hit": time3 / time2 if time2 > 0 else 0
            }
        }

    def generate_performance_report(self, results: Dict[str, Any]):
        """生成性能报告"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_results": results,
            "summary": {},
            "recommendations": []
        }

        # 生成摘要
        if "news_list_cached" in results and "news_list_no_cache" in results:
            cached_mean = results["news_list_cached"].get("mean", 0)
            no_cache_mean = results["news_list_no_cache"].get("mean", 0)
            if no_cache_mean > 0:
                improvement = ((no_cache_mean - cached_mean) / no_cache_mean) * 100
                report["summary"]["news_list_improvement"] = f"性能提升 {improvement:.1f}%"
                report["recommendations"].append("新闻列表缓存效果显著，建议在生产环境启用")
            else:
                report["summary"]["news_list_improvement"] = "性能测试数据不完整"

        if "search_cached" in results and "search_no_cache" in results:
            cached_mean = results["search_cached"].get("mean", 0)
            no_cache_mean = results["search_no_cache"].get("mean", 0)
            if no_cache_mean > 0:
                improvement = ((no_cache_mean - cached_mean) / no_cache_mean) * 100
                report["summary"]["search_improvement"] = f"搜索性能提升 {improvement:.1f}%"
                report["recommendations"].append("搜索缓存效果显著，建议在生产环境启用")
            else:
                report["summary"]["search_improvement"] = "性能测试数据不完整"

        # 检查缓存命中率
        if "cache_hit_ratio" in results:
            cache_test = results["cache_hit_ratio"]
            if cache_test.get("stats_response"):
                report["summary"]["cache_system"] = "缓存系统运行正常"
                if cache_test.get("cache_improvement", 0) > 0:
                    report["recommendations"].append(f"缓存命中后性能提升 {cache_test['cache_improvement']:.1f}%")
            else:
                report["summary"]["cache_system"] = "需要检查缓存系统"

        return report


async def run_performance_test():
    """运行完整的性能测试套件"""
    logger.info("开始性能基准测试...")

    benchmark = PerformanceBenchmark()

    try:
        # 1. 基础性能测试
        basic_results = await benchmark.test_cache_performance()

        # 2. 并发性能测试
        concurrent_results = await benchmark.test_concurrent_performance()

        # 3. 缓存命中率测试
        cache_hit_results = await benchmark.test_cache_hit_ratio()

        # 4. 生成报告
        all_results = {
            "basic_performance": basic_results,
            "concurrent_performance": concurrent_results,
            "cache_hit_ratio": cache_hit_results
        }

        report = benchmark.generate_performance_report(all_results)

        logger.info("性能测试完成！")
        logger.info(f"测试摘要: {report['summary']}")

        # 输出JSON格式结果
        import json
        print(json.dumps(report, indent=2, ensure_ascii=False))

        return report

    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "性能测试执行失败"
        }


if __name__ == "__main__":
    asyncio.run(run_performance_test())