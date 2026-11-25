"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiSend, setToken } from "@/lib/api";
import type { AuthToken } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);
    try {
      const token = await apiSend<AuthToken>("/auth/login", { form });
      setToken(token.access_token);
      router.push("/profile");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>登录</h1>
          <p>使用用户名或邮箱。演示账户见项目说明，上线前请更换密码。</p>
        </div>
      </div>
      <form className="panel card stack" onSubmit={onSubmit} style={{ maxWidth: 420 }}>
        <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="用户名或邮箱" />
        <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="密码" />
        <button className="btn" type="submit">登录</button>
        {error && <div className="error">{error}</div>}
      </form>
    </section>
  );
}
