"use client";

import { FormEvent, useState } from "react";
import { NewsList } from "@/components/NewsList";
import { Status } from "@/components/Status";
import { apiGet } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<SearchResult>(
        `/news/search?q=${encodeURIComponent(query.trim())}&page=1&page_size=10`
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "搜索失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>搜索</h1>
          <p>在标题、摘要和正文里查找已采集的新闻。</p>
        </div>
      </div>
      <form className="toolbar" onSubmit={onSubmit}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入关键词" />
        <button className="btn" type="submit">搜索</button>
      </form>
      <div style={{ height: 12 }} />
      <Status loading={loading} error={error} />
      {data && <NewsList items={data.items} />}
    </section>
  );
}
