"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Status } from "@/components/Status";
import { apiGet, getToken, setToken } from "@/lib/api";
import type { UserProfile } from "@/lib/types";

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      setError("还没有登录。");
      return;
    }
    apiGet<UserProfile>("/auth/me", true)
      .then(setUser)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>个人资料</h1>
          <p>当前令牌对应的账户。</p>
        </div>
        <button className="btn secondary" onClick={() => { setToken(null); setUser(null); }}>
          退出
        </button>
      </div>
      <Status loading={loading} error={error} />
      {user && (
        <div className="panel card">
          <h2>{user.display_name || user.username}</h2>
          <p>{user.email}</p>
          <p>角色 {user.role}</p>
          <p>权限 {(user.permissions || []).join("、") || "无"}</p>
          <Link href="/settings">去设置</Link>
        </div>
      )}
      {!user && !loading && <Link href="/login">去登录</Link>}
    </section>
  );
}
