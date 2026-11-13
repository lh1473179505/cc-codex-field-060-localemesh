# 输出约定

`crawl` 在 `--out` 目录写出：

## clusters.jsonl

一行一个簇，字段：

- `cluster_id`：规范页规范化 URL 的 sha256 前 16 个十六进制字符
- `canonical_url`
- `members`：有效成员对象数组，每项含 `url`、`locale`、`title`、`content_hash`、`last_updated`（没有 meta 则为 null）
- `aliases`：重定向到本簇成员的源 URL 列表
- `dangling_hreflang`：单向 hreflang 的源和目标，形如 `{"from": "...", "to": "..."}`

`members` 按 `locale` 再按 `url` 排序。文件按 `canonical_url` 排序。

## report.json

```
{
  "pages_fetched": <int>,
  "soft_404": [<url>, ...],
  "http_404": [<url>, ...],
  "sitemap_stale": [{"url": "...", "sitemap_lastmod": "YYYY-MM-DD", "meta_last_updated": "YYYY-MM-DD"}, ...],
  "pages_skipped_duplicate": <int>
}
```

列表字段按 URL 排序。`pages_fetched` 计实际收到最终响应（含 404）的次数，不含因规范化重复而跳过的请求。`pages_skipped_duplicate` 计因规范化后已经抓过而跳过的次数。

## verify

`python -m localemesh verify --out <out> --expect fixtures/expected/clusters.json` 会比较簇的规范页、成员 locale 集合、软 404 和 sitemap_stale。比较规则见期望文件里的注释字段 `_rules`（实现时忽略以下划线开头的键）。
