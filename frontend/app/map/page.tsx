"use client";

import { useEffect, useState } from "react";
import { Status } from "@/components/Status";
import { apiGet } from "@/lib/api";
import type { LocationCluster } from "@/lib/types";

function project(lat: number, lng: number): { left: string; top: string } {
  const x = ((lng + 180) / 360) * 100;
  const y = ((90 - lat) / 180) * 100;
  return { left: `${x}%`, top: `${y}%` };
}

export default function MapPage() {
  const [clusters, setClusters] = useState<LocationCluster[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<LocationCluster[]>("/map/clusters")
      .then(setClusters)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const ranked = [...clusters].sort((a, b) => b.count - a.count).slice(0, 12);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>热点地图</h1>
          <p>按国家聚合新闻数量。点位使用经纬度做等距矩形投影。</p>
        </div>
      </div>
      <Status loading={loading} error={error} />
      {!loading && !error && (
        <div className="grid">
          <div className="panel map-board" aria-label="新闻地理分布">
            {ranked.map((item) => (
              <span
                key={item.country}
                className="dot"
                style={project(item.lat, item.lng)}
                title={`${item.country_cn || item.country} ${item.count}`}
              />
            ))}
          </div>
          <div className="panel card">
            <h2>地区排行</h2>
            <div className="bars">
              {ranked.length === 0 && <div className="empty">还没有地理位置数据。</div>}
              {ranked.map((item) => (
                <div className="bar-line" key={item.country}>
                  <span>{item.country_cn || item.country}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${Math.min(100, item.count * 8)}%` }} />
                  </div>
                  <span>{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
