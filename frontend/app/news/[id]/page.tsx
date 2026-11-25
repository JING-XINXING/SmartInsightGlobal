"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Status } from "@/components/Status";
import { apiGet, sentimentLabel } from "@/lib/api";
import type { NewsItem } from "@/lib/types";

export default function NewsDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<NewsItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<NewsItem>(`/news/${params.id}`)
      .then(setItem)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>新闻详情</h1>
          <p>原文链接、摘要和已保存的情感、关键词。</p>
        </div>
      </div>
      <Status loading={loading} error={error} />
      {item && (
        <article className="panel card">
          <h2>{item.title}</h2>
          <div className="meta">
            <span>{item.source}</span>
            <span>{item.category || "未分类"}</span>
            <span>
              情感 {item.sentiment_score ?? "—"}（{sentimentLabel(item.sentiment_score)}）
            </span>
          </div>
          <p>{item.summary || item.content || "没有摘要。"}</p>
          <p>
            <a href={item.url} target="_blank" rel="noreferrer">打开原文</a>
          </p>
        </article>
      )}
    </section>
  );
}
