#!/usr/bin/env python3
"""
生成测试覆盖率报告
分析代码覆盖率并提供改进建议
"""
import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class CoverageReportGenerator:
    """覆盖率报告生成器"""

    def __init__(self, coverage_file: str = "coverage.xml"):
        self.coverage_file = coverage_file
        self.base_dir = Path(__file__).parent

    def parse_coverage_xml(self) -> Dict[str, Any]:
        """解析pytest-cov生成的XML覆盖率报告"""
        if not os.path.exists(self.coverage_file):
            raise FileNotFoundError(f"覆盖率文件不存在: {self.coverage_file}")

        tree = ET.parse(self.coverage_file)
        root = tree.getroot()

        coverage_data = {
            "packages": {},
            "total_lines": 0,
            "covered_lines": 0,
            "total_branches": 0,
            "covered_branches": 0,
            "coverage_percentage": 0.0
        }

        for package in root.findall(".//package"):
            package_name = package.get("name", "")
            if not package_name.startswith("app."):
                continue

            lines_data = {
                "total": 0,
                "covered": 0,
                "missing": 0,
                "excluded": 0
            }

            branches_data = {
                "total": 0,
                "covered": 0,
                "missing": 0,
                "partial": 0
            }

            # 解析行覆盖率
            for lines in package.findall(".//lines"):
                lines_data["total"] = int(lines.get("total", 0))
                lines_data["covered"] = int(lines.get("covered", 0))
                lines_data["missing"] = int(lines.get("missing", 0))
                lines_data["excluded"] = int(lines.get("excluded", 0))

            # 解析分支覆盖率
            for branches in package.findall(".//branches"):
                branches_data["total"] = int(branches.get("total", 0))
                branches_data["covered"] = int(branches.get("covered", 0))
                branches_data["missing"] = int(branches.get("missing", 0))
                branches_data["partial"] = int(branches.get("partial", 0))

            coverage_data["packages"][package_name] = {
                "lines": lines_data,
                "branches": branches_data,
                "line_coverage": self._calculate_percentage(lines_data["covered"], lines_data["total"]),
                "branch_coverage": self._calculate_percentage(branches_data["covered"], branches_data["total"])
            }

            coverage_data["total_lines"] += lines_data["total"]
            coverage_data["covered_lines"] += lines_data["covered"]
            coverage_data["total_branches"] += branches_data["total"]
            coverage_data["covered_branches"] += branches_data["covered"]

        # 计算总体覆盖率
        if coverage_data["total_lines"] > 0:
            coverage_data["coverage_percentage"] = (
                coverage_data["covered_lines"] / coverage_data["total_lines"]
            ) * 100

        return coverage_data

    def _calculate_percentage(self, covered: int, total: int) -> float:
        """计算百分比"""
        if total == 0:
            return 0.0
        return round((covered / total) * 100, 2)

    def analyze_test_gaps(self, coverage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析测试空白和未覆盖的代码"""
        gaps = []

        # 分析低覆盖率模块
        for package_name, package_data in coverage_data["packages"].items():
            line_coverage = package_data["line_coverage"]
            branch_coverage = package_data["branch_coverage"]

            if line_coverage < 50 or branch_coverage < 50:
                gaps.append({
                    "type": "low_coverage",
                    "module": package_name,
                    "line_coverage": line_coverage,
                    "branch_coverage": branch_coverage,
                    "severity": "high" if line_coverage < 25 else "medium"
                })

        return gaps

    def generate_improvement_suggestions(self, coverage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []

        overall_coverage = coverage_data["coverage_percentage"]

        if overall_coverage < 30:
            suggestions.append({
                "priority": "critical",
                "category": "overall_coverage",
                "description": "整体覆盖率过低，需要立即增加测试用例",
                "actions": [
                    "为核心模块编写基础单元测试",
                    "使用测试驱动开发（TDD）方法",
                    "优先测试业务逻辑关键路径"
                ]
            })
        elif overall_coverage < 50:
            suggestions.append({
                "priority": "high",
                "category": "overall_coverage",
                "description": "整体覆盖率偏低，需要增加测试用例",
                "actions": [
                    "补充边界条件和异常情况测试",
                    "增加集成测试覆盖",
                    "为配置和工具函数编写测试"
                ]
            })
        elif overall_coverage < 70:
            suggestions.append({
                "priority": "medium",
                "category": "overall_coverage",
                "description": "整体覆盖率中等，可以进一步优化",
                "actions": [
                    "增加参数化测试用例",
                    "补充性能和错误处理测试",
                    "优化现有测试的断言覆盖率"
                ]
            })

        # 模块特定建议
        for package_name, package_data in coverage_data["packages"].items():
            line_coverage = package_data["line_coverage"]

            if line_coverage < 70:
                module_type = self._classify_module_type(package_name)
                suggestions.append({
                    "priority": "high" if line_coverage < 50 else "medium",
                    "category": "module_coverage",
                    "module": package_name,
                    "module_type": module_type,
                    "line_coverage": line_coverage,
                    "description": f"模块 {package_name} 覆盖率不足",
                    "actions": self._get_module_test_suggestions(module_type)
                })

        return suggestions

    def _classify_module_type(self, module_name: str) -> str:
        """分类模块类型"""
        if "api" in package_name or "endpoints" in package_name:
            return "api"
        elif "analyzer" in package_name or "client" in package_name:
            return "analysis"
        elif "crawler" in package_name or "scraper" in package_name:
            return "crawler"
        elif "models" in package_name:
            return "models"
        elif "core" in package_name:
            return "core"
        else:
            return "general"

    def _get_module_test_suggestions(self, module_type: str) -> List[str]:
        """获取模块特定的测试建议"""
        suggestions = {
            "api": [
                "添加更多HTTP状态码测试（400, 401, 404, 500）",
                "增加参数验证和边界条件测试",
                "添加认证和授权测试",
                "补充错误处理和异常情况测试",
                "增加并发请求和性能测试"
            ],
            "analysis": [
                "测试各种输入格式和边界情况",
                "增加错误处理和异常恢复测试",
                "添加性能和资源使用测试",
                "测试与外部服务的集成",
                "补充并发和异步操作测试"
            ],
            "crawler": [
                "测试网络错误和超时处理",
                "增加不同RSS格式的解析测试",
                "添加内容验证和清理测试",
                "测试并发爬取和资源限制",
                "补充数据持久化测试"
            ],
            "models": [
                "测试数据验证和约束",
                "增加关系操作测试",
                "添加序列化和反序列化测试",
                "测试数据库查询和索引",
                "补充迁移和版本兼容性测试"
            ],
            "core": [
                "测试配置管理功能",
                "增加日志记录和监控测试",
                "添加缓存和性能优化测试",
                "测试错误恢复和容错机制",
                "补充安全性和权限验证测试"
            ],
            "general": [
                "增加基础功能和边界测试",
                "添加参数验证和类型测试",
                "补充错误处理和异常测试",
                "增加性能和资源使用测试"
            ]
        }
        return suggestions.get(module_type, suggestions["general"])

    def generate_markdown_report(self, coverage_data: Dict[str, Any],
                               gaps: List[Dict[str, Any]],
                               suggestions: List[Dict[str, Any]]) -> str:
        """生成Markdown格式的报告"""
        report = []

        # 标题
        report.append("# SmartInsight Global 测试覆盖率报告\n")
        report.append(f"**生成时间**: {self._get_current_time()}\n")
        report.append(f"**总体覆盖率**: {coverage_data['coverage_percentage']:.1f}%\n")

        # 总体统计
        report.append("## 📊 总体统计\n")
        report.append(f"- **总代码行数**: {coverage_data['total_lines']:,}")
        report.append(f"- **已覆盖行数**: {coverage_data['covered_lines']:,}")
        report.append(f"- **总分支数**: {coverage_data['total_branches']:,}")
        report.append(f"- **已覆盖分支数**: {coverage_data['covered_branches']:,}")
        report.append(f"- **行覆盖率**: {coverage_data['coverage_percentage']:.1f}%\n")

        # 模块覆盖率详情
        report.append("## 📦 模块覆盖率详情\n")
        for package_name, package_data in sorted(coverage_data["packages"].items()):
            line_cov = package_data["line_coverage"]
            branch_cov = package_data["branch_coverage"]

            status_emoji = self._get_coverage_emoji(line_cov)
            report.append(f"### {status_emoji} `{package_name}`\n")
            report.append(f"- **行覆盖率**: {line_cov:.1f}% ({package_data['lines']['covered']}/{package_data['lines']['total']})")
            report.append(f"- **分支覆盖率**: {branch_cov:.1f}% ({package_data['branches']['covered']}/{package_data['branches']['total']})")
            report.append("")

        # 测试空白分析
        if gaps:
            report.append("## ⚠️ 测试空白分析\n")
            for gap in gaps:
                emoji = "🔴" if gap["severity"] == "high" else "🟡"
                report.append(f"### {emoji} {gap['type'].replace('_', ' ').title()}")
                report.append(f"- **模块**: `{gap['module']}`")
                report.append(f"- **行覆盖率**: {gap['line_coverage']:.1f}%")
                report.append(f"- **严重程度**: {gap['severity']}")
                report.append("")

        # 改进建议
        if suggestions:
            report.append("## 💡 改进建议\n")

            # 按优先级分组
            critical_suggestions = [s for s in suggestions if s["priority"] == "critical"]
            high_suggestions = [s for s in suggestions if s["priority"] == "high"]
            medium_suggestions = [s for s in suggestions if s["priority"] == "medium"]

            for priority, suggestions_group in [
                ("critical", critical_suggestions),
                ("high", high_suggestions),
                ("medium", medium_suggestions)
            ]:
                if suggestions_group:
                    emoji = {"critical": "🚨", "high": "⚠️", "medium": "📝"}[priority]
                    report.append(f"### {emoji} {priority.title()} 优先级\n")

                    for suggestion in suggestions_group:
                        report.append(f"**{suggestion['description']}**\n")
                        for action in suggestion["actions"]:
                            report.append(f"- {action}")
                        report.append("")
                else:
                    report.append(f"无 {priority} 优先级问题\n")

        # 下一步行动计划
        report.append("## 🎯 下一步行动计划\n")
        report.append("### 短期目标（1-2周）\n")
        report.append("- [ ] 提升整体测试覆盖率达到70%以上")
        report.append("- [ ] 完善低覆盖率模块的测试用例")
        report.append("- [ ] 增加边界条件和异常情况测试")
        report.append("- [ ] 实现自动化测试报告生成")
        report.append("")

        report.append("### 中期目标（1个月）\n")
        report.append("- [ ] 建立完整的CI/CD测试流水线")
        report.append("- [ ] 实现性能测试和基准测试")
        report.append("- [ ] 增加集成测试和端到端测试")
        report.append("- [ ] 优化测试执行效率")
        report.append("")

        report.append("### 长期目标（2-3个月）\n")
        report.append("- [ ] 测试覆盖率达到90%以上")
        report.append("- [ ] 建立测试数据管理和Mock策略")
        report.append("- [ ] 实现测试驱动的开发流程")
        report.append("- [ ] 建立代码质量门禁和自动化检查")
        report.append("")

        return "\n".join(report)

    def _get_coverage_emoji(self, coverage: float) -> str:
        """根据覆盖率获取emoji"""
        if coverage >= 90:
            return "🟢"
        elif coverage >= 80:
            return "🟡"
        elif coverage >= 70:
            return "🟠"
        elif coverage >= 50:
            return "🟡"
        else:
            return "🔴"

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(self, report: str, output_file: str = "test_coverage_report.md"):
        """保存报告到文件"""
        report_path = self.base_dir / output_file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"覆盖率报告已保存到: {report_path}")

    def generate_summary(self, coverage_data: Dict[str, Any]) -> str:
        """生成简要摘要"""
        coverage_pct = coverage_data['coverage_percentage']

        if coverage_pct >= 80:
            status = "优秀"
            emoji = "🟢"
        elif coverage_pct >= 70:
            status = "良好"
            emoji = "🟡"
        elif coverage_pct >= 50:
            status = "中等"
            emoji = "🟠"
        else:
            status = "需改进"
            emoji = "🔴"

        return f"{emoji} 测试覆盖率: {coverage_pct:.1f}% ({status})"

    def run(self):
        """运行覆盖率分析"""
        try:
            print("🔍 解析测试覆盖率报告...")
            coverage_data = self.parse_coverage_xml()

            print("📊 分析测试空白...")
            gaps = self.analyze_test_gaps(coverage_data)

            print("💡 生成改进建议...")
            suggestions = self.generate_improvement_suggestions(coverage_data)

            print("📋 生成详细报告...")
            report = self.generate_markdown_report(coverage_data, gaps, suggestions)

            print("💾 保存报告...")
            self.save_report(report)

            print("✅ 覆盖率分析完成!")
            print(self.generate_summary(coverage_data))

            return 0

        except Exception as e:
            print(f"❌ 生成覆盖率报告失败: {e}")
            return 1


def main():
    """主函数"""
    generator = CoverageReportGenerator()

    # 支持命令行参数
    coverage_file = "coverage.xml"
    output_file = "test_coverage_report.md"

    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("用法: python test_coverage_report.py [coverage_file] [output_file]")
            print("默认: coverage.xml, test_coverage_report.md")
            return 0
        elif len(sys.argv) >= 2:
            coverage_file = sys.argv[1]
        if len(sys.argv) >= 3:
            output_file = sys.argv[2]

    generator.coverage_file = coverage_file
    return generator.run()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)