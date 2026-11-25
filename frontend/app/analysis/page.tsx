"use client";

import { FormEvent, useState } from "react";
import { apiSend, getToken } from "@/lib/api";

/** 调用需要登录的高级分析接口，并把返回 JSON 原样展示，方便核对字段。 */
export default function AnalysisPage() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [result, setResult] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!getToken()) {
      setError("请先登录分析师或管理员账户。");
      return;
    }
    try {
      const data = await apiSend<unknown>("/analysis/analyze", {
        auth: true,
        json: { title, content },
      });
      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失败");
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>高级分析</h1>
          <p>提交标题和正文，后端会做情感、实体和趋势分析。未配置模型密钥时会走模拟结果。</p>
        </div>
      </div>
      <form className="panel card stack" onSubmit={onSubmit}>
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="标题" required />
        <textarea value={content} onChange={(event) => setContent(event.target.value)} placeholder="正文" required />
        <button className="btn" type="submit">开始分析</button>
        {error && <div className="error">{error}</div>}
      </form>
      {result && (
        <pre className="panel card" style={{ overflow: "auto" }}>{result}</pre>
      )}
    </section>
  );
}
