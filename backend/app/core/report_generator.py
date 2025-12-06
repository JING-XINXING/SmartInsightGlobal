"""
报告生成器
支持生成PDF、HTML、Markdown格式的分析报告
"""
import os
import io
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

# PDF生成
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # 创建占位符类型
    Table = None
    SimpleDocTemplate = None

# HTML生成
try:
    from jinja2 import Environment, BaseLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    # 创建占位符类型
    Environment = None
    BaseLoader = None

from app.core.logger import logger
from app.core.i18n import i18n_manager, Language, get_current_language


class ReportFormat(str, Enum):
    """报告格式"""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"


class ReportType(str, Enum):
    """报告类型"""
    NEWS_ANALYSIS = "news_analysis"
    SENTIMENT_TREND = "sentiment_trend"
    GEOGRAPHIC_ANALYSIS = "geographic_analysis"
    COMPREHENSIVE_REPORT = "comprehensive_report"
    CUSTOM = "custom"


@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: str
    subsections: List['ReportSection'] = None
    charts: List[Dict[str, Any]] = None
    tables: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.charts is None:
            self.charts = []
        if self.tables is None:
            self.tables = []


@dataclass
class ReportMetadata:
    """报告元数据"""
    title: str
    author: str
    language: Language
    report_type: ReportType
    created_at: datetime
    time_range: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None


class ReportGenerator:
    """
    报告生成器
    支持多种格式和类型的报告生成
    """

    def __init__(self):
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)

        # 检查依赖
        self.pdf_available = REPORTLAB_AVAILABLE
        self.html_available = JINJA2_AVAILABLE

        if not self.pdf_available:
            logger.warning("ReportLab not available, PDF generation disabled")

        if not self.html_available:
            logger.warning("Jinja2 not available, HTML generation disabled")

        # HTML模板
        self.html_template = self._get_html_template()

    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .metadata {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: #007bff;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        .subsection {
            margin-left: 20px;
            margin-top: 15px;
        }
        .subsection h3 {
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        table, th, td {
            border: 1px solid #ddd;
            padding: 8px;
        }
        th {
            background-color: #f2f2f2;
            text-align: left;
        }
        .chart-placeholder {
            background: #f9f9f9;
            border: 2px dashed #ddd;
            padding: 20px;
            text-align: center;
            margin: 15px 0;
        }
        .footer {
            margin-top: 50px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }
        .sentiment-positive { color: #28a745; }
        .sentiment-negative { color: #dc3545; }
        .sentiment-neutral { color: #6c757d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p class="metadata">{{ author }} | {{ created_at }}</p>
        {% if time_range %}
        <p>时间范围: {{ time_range }}</p>
        {% endif %}
    </div>

    <div class="metadata">
        <h3>报告信息</h3>
        <ul>
            <li>报告类型: {{ report_type }}</li>
            <li>生成时间: {{ created_at }}</li>
            {% if filters %}
            <li>筛选条件: {{ filters }}</li>
            {% endif %}
            {% if data_sources %}
            <li>数据来源: {{ data_sources | join(', ') }}</li>
            {% endif %}
        </ul>
    </div>

    {% for section in sections %}
    <div class="section">
        <h2>{{ section.title }}</h2>
        <div>{{ section.content | safe }}</div>

        {% for table in section.tables %}
        <div>
            <h4>{{ table.title }}</h4>
            {{ table.html | safe }}
        </div>
        {% endfor %}

        {% for chart in section.charts %}
        <div class="chart-placeholder">
            <p><strong>{{ chart.title }}</strong></p>
            <p>{{ chart.description }}</p>
            {% if chart.data_url %}
            <img src="{{ chart.data_url }}" alt="{{ chart.title }}" style="max-width: 100%;">
            {% endif %}
        </div>
        {% endfor %}

        {% for subsection in section.subsections %}
        <div class="subsection">
            <h3>{{ subsection.title }}</h3>
            <div>{{ subsection.content | safe }}</div>
        </div>
        {% endfor %}
    </div>
    {% endfor %}

    <div class="footer">
        <p>此报告由 SmartInsight Global 自动生成</p>
        <p>生成时间: {{ created_at }}</p>
    </div>
</body>
</html>
        """

    async def generate_report(
        self,
        metadata: ReportMetadata,
        sections: List[ReportSection],
        format: ReportFormat = ReportFormat.HTML,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成报告

        Args:
            metadata: 报告元数据
            sections: 报告章节
            format: 报告格式
            output_filename: 输出文件名（可选）

        Returns:
            生成结果
        """
        try:
            logger.info(f"Generating {format.value} report: {metadata.title}")

            # 生成文件名
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{metadata.report_type.value}_{timestamp}.{format.value}"

            output_path = self.output_dir / output_filename

            # 根据格式生成报告
            if format == ReportFormat.PDF:
                if not self.pdf_available:
                    raise ValueError("PDF generation not available - ReportLab not installed")

                result = await self._generate_pdf_report(metadata, sections, output_path)

            elif format == ReportFormat.HTML:
                if not self.html_available:
                    raise ValueError("HTML generation not available - Jinja2 not installed")

                result = await self._generate_html_report(metadata, sections, output_path)

            elif format == ReportFormat.MARKDOWN:
                result = await self._generate_markdown_report(metadata, sections, output_path)

            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Report generated successfully: {output_path}")
            return result

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise

    async def _generate_pdf_report(
        self,
        metadata: ReportMetadata,
        sections: List[ReportSection],
        output_path: Path
    ) -> Dict[str, Any]:
        """生成PDF报告"""
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # 自定义样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )

        # 标题
        story.append(Paragraph(metadata.title, title_style))
        story.append(Spacer(1, 20))

        # 元数据
        metadata_text = f"""
        <b>作者:</b> {metadata.author}<br/>
        <b>生成时间:</b> {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>报告类型:</b> {self._translate_report_type(metadata.report_type, metadata.language)}<br/>
        """
        if metadata.time_range:
            metadata_text += f"<b>时间范围:</b> {metadata.time_range}<br/>"

        story.append(Paragraph(metadata_text, styles['Normal']))
        story.append(Spacer(1, 20))

        # 章节内容
        for section in sections:
            story.append(Paragraph(section.title, heading_style))
            story.append(Paragraph(section.content, styles['Normal']))

            # 添加表格
            for table in section.tables:
                if table.get('data'):
                    story.append(Paragraph(table['title'], styles['Heading3']))
                    pdf_table = self._create_pdf_table(table['data'])
                    story.append(pdf_table)
                    story.append(Spacer(1, 12))

            story.append(Spacer(1, 20))

        # 页脚
        footer_text = "此报告由 SmartInsight Global 自动生成"
        story.append(Paragraph(footer_text, styles['Normal']))

        # 构建PDF
        doc.build(story)

        # 读取文件并编码为base64
        with open(output_path, 'rb') as f:
            pdf_data = f.read()

        return {
            "success": True,
            "format": "pdf",
            "filename": output_path.name,
            "file_size": len(pdf_data),
            "file_path": str(output_path),
            "base64_data": base64.b64encode(pdf_data).decode('utf-8')
        }

    async def _generate_html_report(
        self,
        metadata: ReportMetadata,
        sections: List[ReportSection],
        output_path: Path
    ) -> Dict[str, Any]:
        """生成HTML报告"""
        if not self.html_available:
            raise ValueError("HTML generation not available")

        # 准备模板数据
        template_data = {
            "title": metadata.title,
            "author": metadata.author,
            "created_at": metadata.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "report_type": self._translate_report_type(metadata.report_type, metadata.language),
            "language": metadata.language.value,
            "time_range": metadata.time_range,
            "filters": json.dumps(metadata.filters, ensure_ascii=False) if metadata.filters else None,
            "data_sources": metadata.data_sources,
            "sections": []
        }

        # 处理章节
        for section in sections:
            section_data = {
                "title": section.title,
                "content": section.content,
                "subsections": [
                    {
                        "title": sub.title,
                        "content": sub.content
                    }
                    for sub in section.subsections
                ],
                "tables": [],
                "charts": []
            }

            # 处理表格
            for table in section.tables:
                table_data = {
                    "title": table.get("title", ""),
                    "html": self._create_html_table(table.get("data", []))
                }
                section_data["tables"].append(table_data)

            # 处理图表
            for chart in section.charts:
                chart_data = {
                    "title": chart.get("title", ""),
                    "description": chart.get("description", ""),
                    "data_url": chart.get("data_url", "")
                }
                section_data["charts"].append(chart_data)

            template_data["sections"].append(section_data)

        # 渲染HTML
        template = Environment(loader=BaseLoader()).from_string(self.html_template)
        html_content = template.render(**template_data)

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 读取文件并编码
        with open(output_path, 'r', encoding='utf-8') as f:
            html_data = f.read()

        return {
            "success": True,
            "format": "html",
            "filename": output_path.name,
            "file_size": len(html_data.encode('utf-8')),
            "file_path": str(output_path),
            "content": html_data
        }

    async def _generate_markdown_report(
        self,
        metadata: ReportMetadata,
        sections: List[ReportSection],
        output_path: Path
    ) -> Dict[str, Any]:
        """生成Markdown报告"""
        markdown_content = []

        # 标题
        markdown_content.append(f"# {metadata.title}\n")

        # 元数据
        markdown_content.append("## 报告信息\n")
        markdown_content.append(f"- **作者**: {metadata.author}")
        markdown_content.append(f"- **生成时间**: {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        markdown_content.append(f"- **报告类型**: {self._translate_report_type(metadata.report_type, metadata.language)}")
        if metadata.time_range:
            markdown_content.append(f"- **时间范围**: {metadata.time_range}")
        markdown_content.append("")

        # 章节内容
        for section in sections:
            markdown_content.append(f"## {section.title}\n")
            markdown_content.append(f"{section.content}\n")

            # 添加子章节
            for subsection in section.subsections:
                markdown_content.append(f"### {subsection.title}\n")
                markdown_content.append(f"{subsection.content}\n")

            # 添加表格
            for table in section.tables:
                if table.get("data"):
                    markdown_content.append(f"### {table.get('title', '数据表')}\n")
                    markdown_content.append(self._create_markdown_table(table["data"]))
                    markdown_content.append("")

            # 添加图表说明
            for chart in section.charts:
                markdown_content.append(f"### {chart.get('title', '图表')}\n")
                markdown_content.append(f"{chart.get('description', '图表说明')}\n")
                markdown_content.append("")

        # 页脚
        markdown_content.append("---\n")
        markdown_content.append("*此报告由 SmartInsight Global 自动生成*")

        # 保存文件
        final_content = "\n".join(markdown_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        return {
            "success": True,
            "format": "markdown",
            "filename": output_path.name,
            "file_size": len(final_content.encode('utf-8')),
            "file_path": str(output_path),
            "content": final_content
        }

    def _create_pdf_table(self, data: List[List[str]]) -> Table:
        """创建PDF表格"""
        if not data:
            return Table([["无数据"]])

        # 确保所有行都有相同的列数
        max_cols = max(len(row) for row in data)
        normalized_data = []
        for row in data:
            normalized_row = row + [""] * (max_cols - len(row))
            normalized_data.append(normalized_row)

        table = Table(normalized_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        return table

    def _create_html_table(self, data: List[List[str]]) -> str:
        """创建HTML表格"""
        if not data:
            return "<p>无数据</p>"

        html = ["<table>"]

        # 表头
        if data:
            html.append("<thead><tr>")
            for cell in data[0]:
                html.append(f"<th>{cell}</th>")
            html.append("</tr></thead>")

        # 表体
        html.append("<tbody>")
        for row in data[1:]:
            html.append("<tr>")
            for cell in row:
                html.append(f"<td>{cell}</td>")
            html.append("</tr>")
        html.append("</tbody>")

        html.append("</table>")
        return "".join(html)

    def _create_markdown_table(self, data: List[List[str]]) -> str:
        """创建Markdown表格"""
        if not data:
            return "| 无数据 |\n|--------|"

        table_lines = []

        # 表头
        header = "| " + " | ".join(data[0]) + " |"
        table_lines.append(header)

        # 分隔线
        separator = "|" + "|".join([" --- " for _ in data[0]]) + "|"
        table_lines.append(separator)

        # 数据行
        for row in data[1:]:
            # 确保行长度一致
            while len(row) < len(data[0]):
                row.append("")
            table_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

        return "\n".join(table_lines)

    def _translate_report_type(self, report_type: ReportType, language: Language) -> str:
        """翻译报告类型"""
        translations = {
            ReportType.NEWS_ANALYSIS: {
                Language.CHINESE: "新闻分析报告",
                Language.ENGLISH: "News Analysis Report"
            },
            ReportType.SENTIMENT_TREND: {
                Language.CHINESE: "情感趋势报告",
                Language.ENGLISH: "Sentiment Trend Report"
            },
            ReportType.GEOGRAPHIC_ANALYSIS: {
                Language.CHINESE: "地理分析报告",
                Language.ENGLISH: "Geographic Analysis Report"
            },
            ReportType.COMPREHENSIVE_REPORT: {
                Language.CHINESE: "综合分析报告",
                Language.ENGLISH: "Comprehensive Analysis Report"
            },
            ReportType.CUSTOM: {
                Language.CHINESE: "自定义报告",
                Language.ENGLISH: "Custom Report"
            }
        }

        return translations.get(report_type, {}).get(language, report_type.value)

    async def create_news_analysis_report(
        self,
        news_data: List[Dict[str, Any]],
        language: Language = Language.CHINESE,
        time_range: Optional[str] = None
    ) -> ReportSection:
        """创建新闻分析报告章节"""
        # 统计数据
        total_news = len(news_data)
        avg_sentiment = sum(n.get("sentiment_score", 0) for n in news_data) / total_news if total_news > 0 else 0

        # 类别统计
        category_stats = {}
        for news in news_data:
            category = news.get("category", "其他")
            category_stats[category] = category_stats.get(category, 0) + 1

        # 情感分布
        sentiment_distribution = {
            "非常积极": len([n for n in news_data if (n.get("sentiment_score", 0) or 0) > 50]),
            "积极": len([n for n in news_data if 10 < (n.get("sentiment_score", 0) or 0) <= 50]),
            "中性": len([n for n in news_data if -10 <= (n.get("sentiment_score", 0) or 0) <= 10]),
            "消极": len([n for n in news_data if -50 <= (n.get("sentiment_score", 0) or 0) < -10]),
            "非常消极": len([n for n in news_data if (n.get("sentiment_score", 0) or 0) < -50])
        }

        # 创建内容
        content = f"""
本报告分析了 {total_news} 条新闻数据。

### 核心指标
- 总新闻数量: {total_news}
- 平均情感分数: {avg_sentiment:.2f}
- 主要类别: {max(category_stats.items(), key=lambda x: x[1])[0] if category_stats else '无'}

### 情感分布
- 非常积极: {sentiment_distribution['非常积极']} 条
- 积极: {sentiment_distribution['积极']} 条
- 中性: {sentiment_distribution['中性']} 条
- 消极: {sentiment_distribution['消极']} 条
- 非常消极: {sentiment_distribution['非常消极']} 条

### 类别分布
"""

        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_news * 100) if total_news > 0 else 0
            content += f"- {category}: {count} 条 ({percentage:.1f}%)\n"

        # 创建数据表格
        category_table_data = [["类别", "数量", "百分比"]]
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_news * 100) if total_news > 0 else 0
            category_table_data.append([category, str(count), f"{percentage:.1f}%"])

        sentiment_table_data = [["情感级别", "数量"]]
        for level, count in sentiment_distribution.items():
            sentiment_table_data.append([level, str(count)])

        return ReportSection(
            title="新闻数据分析" if language == Language.CHINESE else "News Data Analysis",
            content=content,
            tables=[
                {
                    "title": "类别分布统计" if language == Language.CHINESE else "Category Distribution",
                    "data": category_table_data
                },
                {
                    "title": "情感分布统计" if language == Language.CHINESE else "Sentiment Distribution",
                    "data": sentiment_table_data
                }
            ]
        )

    async def create_sentiment_trend_report(
        self,
        trend_data: List[Dict[str, Any]],
        language: Language = Language.CHINESE
    ) -> ReportSection:
        """创建情感趋势报告章节"""
        if not trend_data:
            content = "暂无足够的趋势数据进行分析。" if language == Language.CHINESE else "Insufficient trend data for analysis."
            return ReportSection(
                title="情感趋势分析" if language == Language.CHINESE else "Sentiment Trend Analysis",
                content=content
            )

        # 分析趋势
        sentiment_scores = [point.get("avg_sentiment", 0) for point in trend_data]
        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        # 判断趋势
        if len(sentiment_scores) >= 2:
            recent_avg = sum(sentiment_scores[-3:]) / min(3, len(sentiment_scores))
            earlier_avg = sum(sentiment_scores[:3]) / min(3, len(sentiment_scores))

            if recent_avg > earlier_avg + 5:
                trend_desc = "整体呈上升趋势" if language == Language.CHINESE else "Overall upward trend"
            elif recent_avg < earlier_avg - 5:
                trend_desc = "整体呈下降趋势" if language == Language.CHINESE else "Overall downward trend"
            else:
                trend_desc = "整体保持稳定" if language == Language.CHINESE else "Overall stable"
        else:
            trend_desc = "数据不足，无法判断趋势" if language == Language.CHINESE else "Insufficient data to determine trend"

        content = f"""
基于 {len(trend_data)} 个时间点的数据分析：

### 趋势分析
- 平均情感分数: {avg_score:.2f}
- 趋势描述: {trend_desc}
- 最高分数: {max(sentiment_scores):.2f}
- 最低分数: {min(sentiment_scores):.2f}

### 关键发现
1. 情感波动范围: {max(sentiment_scores) - min(sentiment_scores):.2f} 分
2. 数据点数量: {len(trend_data)}
3. 分析周期: {trend_data[-1].get('timestamp', '')[:10] if trend_data else 'N/A'}
"""

        # 创建趋势表格
        trend_table_data = [
            ["时间", "情感分数", "新闻数量", "主要类别"] if language == Language.CHINESE
            else ["Time", "Sentiment Score", "News Count", "Top Categories"]
        ]

        for point in trend_data[:10]:  # 显示前10个数据点
            timestamp = point.get('timestamp', '')[:10]
            sentiment = point.get('avg_sentiment', 0)
            count = point.get('location_count', 0)
            categories = ', '.join([cat.get('category', '') for cat in point.get('top_categories', [])[:2]])

            trend_table_data.append([timestamp, f"{sentiment:.1f}", str(count), categories])

        return ReportSection(
            title="情感趋势分析" if language == Language.CHINESE else "Sentiment Trend Analysis",
            content=content,
            tables=[
                {
                    "title": "时间序列数据" if language == Language.CHINESE else "Time Series Data",
                    "data": trend_table_data
                }
            ]
        )


# 全局实例
report_generator = ReportGenerator()