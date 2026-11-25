"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "新闻" },
  { href: "/map", label: "地图" },
  { href: "/events", label: "事件" },
  { href: "/search", label: "搜索" },
  { href: "/dashboard", label: "仪表盘" },
  { href: "/analysis", label: "分析" },
  { href: "/reports", label: "报告" },
  { href: "/history", label: "历史" },
  { href: "/settings", label: "设置" },
  { href: "/login", label: "登录" },
];

/** 监测台外壳：桌面顶栏导航，窄屏改为换行，不使用营销式三列卡片。 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <strong>智察全球</strong>
          <span>SmartInsight Global · 监测台</span>
        </div>
        <nav className="nav">
          {LINKS.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link key={link.href} href={link.href} className={active ? "active" : ""}>
                {link.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main className="main">{children}</main>
    </div>
  );
}
