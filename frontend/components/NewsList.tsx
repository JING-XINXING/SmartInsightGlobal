"use client";

import Link from "next/link";
import type { NewsItem } from "@/lib/types";
import { sentimentLabel } from "@/lib/api";

function tone(score: number | null | undefined): string {
  if (score === null || score === undefined) return "neu";
  if (score >= 25) return "pos";
  if (score <= -25) return "neg";
  return "neu";
}

/** 新闻行列表。情感分放在左侧，方便扫读，而不是做成等宽功能卡。 */
export function NewsList({ items }: { items: NewsItem[] }) {
  if (items.length === 0) {
    return <div className="empty">当前没有可显示的新闻。确认后端已采集数据后再刷新。</div>;
  }
  return (
    <div className="panel list">
      {items.map((item) => (
        <article key={item.id} className="row">
          <div className={`score ${tone(item.sentiment_score)}`}>
            {item.sentiment_score ?? "—"}
            <div>{sentimentLabel(item.sentiment_score)}</div>
          </div>
          <div>
            <h2>
              <Link href={`/news/${item.id}`}>{item.title}</Link>
            </h2>
            <div className="meta">
              <span>{item.source}</span>
              <span>{item.category || "未分类"}</span>
              <span>{item.publish_date ? new Date(item.publish_date).toLocaleString() : "时间未知"}</span>
            </div>
            {item.keywords && item.keywords.length > 0 && (
              <div className="tags">
                {item.keywords.slice(0, 5).map((word) => (
                  <span className="tag" key={word}>{word}</span>
                ))}
              </div>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
