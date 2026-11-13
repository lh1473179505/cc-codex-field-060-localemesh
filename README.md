# localemesh

本地多语言目录站的采集工具。夹具站点由本仓库的 `localemesh.site` 提供，不访问公网。

阅读 `docs/cluster.md` 和 `docs/output.md` 后再实现采集、簇合并和软 404 判定。

```
python -m localemesh site --port 8761 --root fixtures/catalog
python -m localemesh crawl --base http://127.0.0.1:8761 --out <out> --checkpoint <ckpt.json>
python -m localemesh verify --out <out> --expect fixtures/expected/clusters.json
```
