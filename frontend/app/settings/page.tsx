"use client";

import { FormEvent, useEffect, useState } from "react";
import { Status } from "@/components/Status";
import { apiGet, apiSend, getToken } from "@/lib/api";

interface PreferencePayload {
  language: string;
  timezone: string;
  theme: string;
  items_per_page: number;
}

export default function SettingsPage() {
  const [form, setForm] = useState<PreferencePayload>({
    language: "zh-CN",
    timezone: "Asia/Shanghai",
    theme: "light",
    items_per_page: 20,
  });
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      setError("登录后才能读取和保存偏好。");
      return;
    }
    apiGet<PreferencePayload & { preferences?: PreferencePayload }>("/preferences/preferences", true)
      .then((result) => {
        const source = result.preferences || result;
        setForm({
          language: source.language || "zh-CN",
          timezone: source.timezone || "Asia/Shanghai",
          theme: source.theme || "light",
          items_per_page: source.items_per_page || 20,
        });
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await apiSend("/preferences/preferences", { auth: true, json: form });
      setMessage("已保存。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>设置</h1>
          <p>语言、时区、主题和每页条数会写回用户偏好。</p>
        </div>
      </div>
      <Status loading={loading} />
      <form className="panel card stack" onSubmit={onSubmit} style={{ maxWidth: 520 }}>
        <label>
          语言
          <select value={form.language} onChange={(event) => setForm({ ...form, language: event.target.value })}>
            <option value="zh-CN">中文</option>
            <option value="en">English</option>
          </select>
        </label>
        <label>
          时区
          <input value={form.timezone} onChange={(event) => setForm({ ...form, timezone: event.target.value })} />
        </label>
        <label>
          主题
          <select value={form.theme} onChange={(event) => setForm({ ...form, theme: event.target.value })}>
            <option value="light">浅色</option>
            <option value="dark">深色</option>
            <option value="auto">跟随系统</option>
          </select>
        </label>
        <label>
          每页条数
          <input
            type="number"
            min={10}
            max={50}
            value={form.items_per_page}
            onChange={(event) => setForm({ ...form, items_per_page: Number(event.target.value) })}
          />
        </label>
        <button className="btn" type="submit">保存</button>
        {message && <div className="note">{message}</div>}
        {error && <div className="error">{error}</div>}
      </form>
    </section>
  );
}
