"use client";

import { FormEvent, useState } from "react";
import { apiSend } from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await apiSend("/auth/register", { json: { email, username, password } });
      setMessage("注册成功，可以去登录。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>注册</h1>
          <p>创建查看者账户。分析权限需要管理员分配角色。</p>
        </div>
      </div>
      <form className="panel card stack" onSubmit={onSubmit} style={{ maxWidth: 420 }}>
        <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="邮箱" />
        <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="用户名" />
        <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="密码" />
        <button className="btn" type="submit">注册</button>
        {message && <div className="note">{message}</div>}
        {error && <div className="error">{error}</div>}
      </form>
    </section>
  );
}
