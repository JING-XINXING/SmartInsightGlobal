import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../app");

const pages = [
  "page.tsx",
  "login/page.tsx",
  "register/page.tsx",
  "news/[id]/page.tsx",
  "map/page.tsx",
  "events/page.tsx",
  "search/page.tsx",
  "dashboard/page.tsx",
  "analysis/page.tsx",
  "reports/page.tsx",
  "history/page.tsx",
  "profile/page.tsx",
  "settings/page.tsx",
];

test("V1.7 页面文件都在", () => {
  for (const page of pages) {
    assert.equal(fs.existsSync(path.join(appDir, page)), true, page);
  }
});
