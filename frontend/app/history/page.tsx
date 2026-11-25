"use client";

import { useEffect, useState } from "react";
import { Status } from "@/components/Status";
import { apiGet, getToken } from "@/lib/api";

interface HistoryItem {
  id: number;
  title: string;
  analysis_type: string;
  status: string;
  created_at?: string;
}

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      setError("登录后才能查看自己的分析历史。");
      return;
    }
    apiGet<{ items?: HistoryItem[] }>("/analysis/history?page=1&page_size=20", true)
      .then((result) => setItems(result.items || []))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>分析历史</h1>
          <p>只显示当前账户的记录。</p>
        </div>
      </div>
      <Status loading={loading} error={error} />
      {!loading && !error && (
        <div className="panel list">
          {items.length === 0 && <div className="empty">还没有分析记录。</div>}
          {items.map((item) => (
            <article className="row" key={item.id}>
              <div className="score neu">{item.analysis_type}</div>
              <div>
                <h2>{item.title}</h2>
                <div className="meta">
                  <span>{item.status}</span>
                  <span>{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
