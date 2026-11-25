"use client";

import { useEffect, useState } from "react";
import { Status } from "@/components/Status";
import { apiGet } from "@/lib/api";

export default function ReportsPage() {
  const [types, setTypes] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<{ types?: Array<{ name?: string; id?: string } | string> }>("/reports/types")
      .then((result) => {
        const values = (result.types || []).map((item) =>
          typeof item === "string" ? item : item.name || item.id || "未命名类型"
        );
        setTypes(values);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>报告</h1>
          <p>后端已提供生成接口。这里先列出可用报告类型，生成仍走分析师权限。</p>
        </div>
      </div>
      <Status loading={loading} error={error} />
      {!loading && !error && (
        <div className="panel card">
          {types.length === 0 && <div className="empty">没有报告类型。</div>}
          <ul>
            {types.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
