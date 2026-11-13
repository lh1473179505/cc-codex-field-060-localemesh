# 夹具站点与簇规则

`python -m localemesh site` 会在本地起一个多语言目录站。所有页面都在这个进程里，不要去抓外网。

## 入口

- `/` 首页给出各语言目录链接。
- `/sitemap.xml` 列出已知的产品 URL，并带 `lastmod`。sitemap 里的 lastmod 不一定等于页面真实内容的更新时间。
- 目录页：`/{locale}/`，locale 为 `en`、`fr`、`de`、`ja`。
- 产品页：`/{locale}/p/{slug}`。
- 同一物理路径若带 `Accept-Language`，也可能从 `/p/{slug}`（无语言前缀）协商到某个 locale，并 302 到 `/{locale}/p/{slug}`。

## hreflang 与 canonical

每个产品页的 `<head>` 里有 `rel="alternate" hreflang="..."` 和至多一个 `rel="canonical"`。

簇的定义：把互相用 hreflang 指向的页面收进同一个簇。只跟单向、没有回指的链接不能单独开一个新簇，应记到 `dangling_hreflang`，并仍把目标页并进源页面所在簇（如果目标页能抓到）。

簇的规范页按下面顺序选，不能只看 sitemap 出现顺序：

1. 页面里 `rel="canonical"` 指向且确实属于本簇的地址。如果多个页面的 canonical 互相矛盾，先比被指向次数，次数多的获胜。
2. 若次数并列，或没有任何可用的簇内 canonical，则在仍待选的成员里优先取被标为 `hreflang="x-default"` 的那个。
3. 还定不下来，再按 locale 优先级 `en > fr > de > ja`。
4. 仍并列则取规范化 URL 字典序最小的成员。

规范化 URL：去掉 fragment；去掉 `utm_*`、`fbclid`、`ref` 查询参数；保留其余参数；host 和 scheme 取 `--base` 的值；路径不做大小写折叠（夹具路径本身是小写）。

## 软 404 与空但有效的页

HTTP 200 不代表页面有效。若正文匹配软 404 模板（夹具里是固定英文或法文句子，见站点页脚注释 `data-soft404="1"`，或正文含 “is not available in your region” / “n'est pas disponible dans votre région”），且页内没有 `div.product-card` 这个商品容器，则该页是软 404：不能当簇成员，也不能当规范页。它的 URL 记入 `soft_404`。

有一类短页面（例如 `/en/p/notebook`）正文很短，但有 `div.product-card` 和标题，这是有效页，不能判软 404。

真正的 HTTP 404 记入 `http_404`，不要和软 404 混在一起。

## sitemap lastmod 与内容

对每个成功抓到的有效产品页，计算 `content_hash`（UTF-8 正文的 sha256 十六进制）。若 sitemap 给出的 lastmod 比该页 `meta[name=last-updated]` 的日期更晚，但你没有在站点上观察到更新后的正文（仍是同一 hash 对应的那份 HTML），不要把该页标成“已更新”，只在 `sitemap_stale` 里记下 URL 和两份日期。

`meta[name=last-updated]` 缺失时，以正文 hash 为准，忽略 sitemap lastmod 的“更新”含义。

## 重定向

无前缀的 `/p/{slug}` 会根据 `Accept-Language` 做 302。重定向源不是簇成员，记入 `aliases`，目标页才是成员。跟随重定向时要带上原来的 `Accept-Language`，但写入簇的永远是跳转后的规范地址。

夹具里 `/ja/p/kettle` 会 302 到 `/en/p/kettle`（日文页未上线）。`/ja/p/kettle` 只能进 `aliases`，不能当日文成员。

## 抓取范围

从首页和 sitemap 发现 URL，再跟随页面里指向本 host 的链接。图里会有环（页脚会链回已见过的目录和产品），必须能结束。不要抓站外链接。同一规范化 URL 只抓一次正文。
