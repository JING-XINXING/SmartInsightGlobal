"use client";

import { useEffect, useState } from "react";
import { NewsList } from "@/components/NewsList";
import { Status } from "@/components/Status";
import { apiGet } from "@/lib/api";
import type { PaginatedNews } from "@/lib/types";

/** 首页：分页新闻流。page_size 最小为 10，与后端校验一致。 */
export default function HomePage() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedNews | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    apiGet<PaginatedNews>(`/news/paginated?page=${page}&page_size=10`)
      .then((result) => {
        if (alive) setData(result);
      })
      .catch((err: Error) => {
        if (alive) setError(err.message);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [page]);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>新闻流</h1>
          <p>按发布时间查看已入库的全球资讯，点进单篇可看分析结果。</p>
        </div>
        <div className="meta">共 {data?.total ?? "—"} 条</div>
      </div>
      <Status loading={loading} error={error} />
      {data && <NewsList items={data.items} />}
      <div className="toolbar" style={{ marginTop: 14 }}>
        <button className="btn secondary" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          上一页
        </button>
        <span className="meta">第 {page} / {data?.total_pages ?? 1} 页</span>
        <button
          className="btn"
          disabled={!data || page >= data.total_pages}
          onClick={() => setPage((value) => value + 1)}
        >
          下一页
        </button>
      </div>
    </section>
  );
}
