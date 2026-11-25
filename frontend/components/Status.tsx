"use client";

export function Status({ error, loading }: { error?: string | null; loading?: boolean }) {
  if (loading) return <div className="note">正在读取数据…</div>;
  if (error) return <div className="error">{error}</div>;
  return null;
}
