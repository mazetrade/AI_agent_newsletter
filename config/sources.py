# =============================================================================
# RSS FEED SOURCES — Major news outlets, newsletters & blogs
# Covering: AI, Crypto, Blockchain
# No API key required — all public RSS feeds
# =============================================================================

# Tier 1 = Top-tier, most authoritative sources (score weight: 30)
# Tier 2 = Specialized & well-known sources (score weight: 20)
# Tier 3 = Good secondary sources (score weight: 10)

RSS_SOURCES = {
    "AI & Machine Learning": [
        {
            "name": "MIT Technology Review",
            "url": "https://www.technologyreview.com/feed/",
            "tier": 1,
        },
        {
            "name": "VentureBeat AI",
            "url": "https://venturebeat.com/category/ai/feed/",
            "tier": 1,
        },
        {
            "name": "TechCrunch AI",
            "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "tier": 1,
        },
        {
            "name": "The Verge AI",
            "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
            "tier": 1,
        },
        {
            "name": "Wired AI",
            "url": "https://www.wired.com/feed/category/ai/latest/rss",
            "tier": 1,
        },
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "tier": 2,
        },
        {
            "name": "AI News",
            "url": "https://www.artificialintelligence-news.com/feed/",
            "tier": 2,
        },
        {
            "name": "Hugging Face Blog",
            "url": "https://huggingface.co/blog/feed.xml",
            "tier": 2,
        },
        {
            "name": "OpenAI Blog",
            "url": "https://openai.com/blog/rss.xml",
            "tier": 1,
        },
        {
            "name": "DeepMind Blog",
            "url": "https://deepmind.google/blog/rss.xml",
            "tier": 1,
        },
    ],

    "Crypto & Blockchain": [
        {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "tier": 1,
        },
        {
            "name": "CoinTelegraph",
            "url": "https://cointelegraph.com/rss",
            "tier": 1,
        },
        {
            "name": "Decrypt",
            "url": "https://decrypt.co/feed",
            "tier": 1,
        },
        {
            "name": "The Block",
            "url": "https://www.theblock.co/rss.xml",
            "tier": 1,
        },
        {
            "name": "Bitcoin Magazine",
            "url": "https://bitcoinmagazine.com/feed",
            "tier": 2,
        },
        {
            "name": "CryptoSlate",
            "url": "https://cryptoslate.com/feed/",
            "tier": 2,
        },
        {
            "name": "BeInCrypto",
            "url": "https://beincrypto.com/feed/",
            "tier": 2,
        },
        {
            "name": "NewsBTC",
            "url": "https://www.newsbtc.com/feed/",
            "tier": 2,
        },
        {
            "name": "CryptoNews",
            "url": "https://cryptonews.com/news/feed/",
            "tier": 2,
        },
        {
            "name": "Blockworks",
            "url": "https://blockworks.co/feed",
            "tier": 1,
        },
    ],
}

# How many days back to look for articles (max 7)
MAX_DAYS_BACK = 7

# Total articles to include in the newsletter
# Keep at 5 for low-cost testing, raise to 10 for full production run
TOP_N = 5
