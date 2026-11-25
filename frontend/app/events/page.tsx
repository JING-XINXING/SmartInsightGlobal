"use client";

import { useEffect, useState } from "react";
import { Status } from "@/components/Status";
import { apiGet } from "@/lib/api";

interface TimelineEvent {
  id?: string | number;
  title?: string;
  category?: string;
  news_count?: number;
  article_count?: number;
  summary?: string;
  keywords?: string[];
}

interface TimelineResponse {
  events?: TimelineEvent[];
  items?: TimelineEvent[];
}

export default function EventsPage() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<TimelineResponse | TimelineEvent[]>("/events/timeline?days=7&limit=10")
      .then((result) => {
        if (Array.isArray(result)) setEvents(result);
        else setEvents(result.events || result.items || []);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>事件时间轴</h1>
          <p>近 7 天按关键词相似度聚成的事件。</p>
        </div>
      </div>
      <Status loading={loading} error={error} />
      {!loading && !error && (
        <div className="panel list">
          {events.length === 0 && <div className="empty">这个时间范围内没有形成事件簇。</div>}
          {events.map((event, index) => (
            <article className="row" key={String(event.id ?? index)}>
              <div className="score neu">{event.news_count || event.article_count || index + 1}</div>
              <div>
                <h2>{event.title || event.keywords?.slice(0, 3).join(" / ") || `事件 ${index + 1}`}</h2>
                <div className="meta">
                  <span>{event.category || "综合"}</span>
                </div>
                {event.summary && <p>{event.summary}</p>}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
