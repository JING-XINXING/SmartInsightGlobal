"use client";

import { useEffect, useState } from "react";
import { Status } from "@/components/Status";
import { apiGet } from "@/lib/api";
import type { PaginatedNews } from "@/lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<PaginatedNews | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<PaginatedNews>("/news/paginated?page=1&page_size=50")
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const items = data?.items ?? [];
  const scored = items.filter((item) => typeof item.sentiment_score === "number");
  const average = scored.length
    ? Math.round(scored.reduce((sum, item) => sum + (item.sentiment_score || 0), 0) / scored.length)
    : null;
  const categories = new Map<string, number>();
  items.forEach((item) => {
    const key = item.category || "未分类";
    categories.set(key, (categories.get(key) || 0) + 1);
  });
  const max = Math.max(1, ...categories.values());

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>仪表盘</h1>
          <p>用最近 50 条新闻估算情感和分类分布。样本不足时数字会偏。</p>
        </div>
      </div>
      <Status loading={loading} error={error} />
      {data && (
        <div className="grid">
          <div className="panel card">
            <h2>样本</h2>
            <p>库内总数 {data.total}</p>
            <p>本页已分析 {scored.length} / {items.length}</p>
            <p>平均情感 {average ?? "—"}</p>
          </div>
          <div className="panel card">
            <h2>分类</h2>
            <div className="bars">
              {[...categories.entries()].map(([name, count]) => (
                <div className="bar-line" key={name}>
                  <span>{name}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${(count / max) * 100}%` }} />
                  </div>
                  <span>{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
