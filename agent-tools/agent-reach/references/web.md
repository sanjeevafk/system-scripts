# 网页阅读

通用网页、RSS。

## 通用网页 (Jina Reader)

```bash
# 读取任意网页内容
curl -s "https://r.jina.ai/URL"

# 示例
curl -s "https://r.jina.ai/https://example.com/article"
```

**适用场景**: 大多数网页可以直接用 Jina Reader 读取。

## Web Reader (MCP)

```bash
# 读取网页内容 (Markdown 格式)
mcporter call 'web-reader.webReader(url: "https://example.com")'

# 保留图片
mcporter call 'web-reader.webReader(url: "https://example.com", retain_images: true)'

# 纯文本格式
mcporter call 'web-reader.webReader(url: "https://example.com", return_format: "text")'
```

**适用场景**: 需要更精确控制输出格式时使用。

## RSS (feedparser)

```python
python3 -c "
import feedparser
for e in feedparser.parse('FEED_URL').entries[:5]:
    print(f'{e.title} — {e.link}')
"
```

**适用场景**: 订阅博客、新闻源、播客等 RSS feed。

## Medium Reading List & Unpaywalled Articles

```bash
# 1. Fetch Medium Reading List / Bookmarks
medium list -n 20

# 2. Read & unpaywall ANY Medium article via Freedium + Jina Reader
medium read "https://medium.com/@username/article-title"

# Output list as JSON
medium list -n 20 --json
```

**适用场景**: 读取 Medium 个人 Reading List (书签)，或通过 Freedium (`freedium-mirror.cfd`) 免 Paywall 提取全文 Markdown。

## 选择指南

| 场景 | 推荐工具 |
|-----|---------|
| 通用网页 | Jina Reader (`curl r.jina.ai`) |
| Medium 个人 Reading List | `medium list -n 20` |
| Medium 文章阅读 (免 Paywall) | `medium read <URL>` |
| 需要图片/格式控制 | web-reader MCP |
| RSS 订阅 | feedparser |

