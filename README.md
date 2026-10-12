# AI & Crypto Pulse — Newsletter Agent

An automated Python agent that writes and emails a weekly newsletter about **AI, crypto, and blockchain**.

Each run it:

1. **Fetches** recent articles from 20 public RSS feeds (MIT Technology Review, TechCrunch, CoinDesk, CoinTelegraph, and others).
2. **Ranks** them by how authoritative the source is and how recent the article is.
3. **Writes** the newsletter with **Claude** (Anthropic's LLM): an introduction, one journalistic paragraph per article, and a closing.
4. **Renders** a dark-themed HTML email from a Jinja2 template.
5. **Sends** it to a list of recipients through Gmail SMTP, or any other SMTP server.

An example of real output is in [newsletter_2026-04-04.html](newsletter_2026-04-04.html). Open it in a browser to see what recipients receive.

---

## Table of contents

- [How it works (the big picture)](#how-it-works-the-big-picture)
- [Project structure](#project-structure)
- [Setup](#setup)
- [Running it](#running-it)
- [Module-by-module walkthrough](#module-by-module-walkthrough)
  - [main.py — the orchestrator](#mainpy--the-orchestrator)
  - [config/sources.py — the news sources](#configsourcespy--the-news-sources)
  - [fetchers/web_fetcher.py — fetching and ranking](#fetchersweb_fetcherpy--fetching-and-ranking)
  - [agents/summarizer.py — the Claude writer](#agentssummarizerpy--the-claude-writer)
  - [newsletter/builder.py — HTML rendering](#newsletterbuilderpy--html-rendering)
  - [templates/newsletter.html — the email design](#templatesnewsletterhtml--the-email-design)
  - [newsletter/sender.py — email delivery](#newslettersenderpy--email-delivery)
- [Unused / experimental code (Twitter and Reddit)](#unused--experimental-code-twitter-and-reddit)
- [Customization guide](#customization-guide)
- [Scheduling it to run weekly](#scheduling-it-to-run-weekly)
- [Known limitations and quirks](#known-limitations-and-quirks)
- [Troubleshooting](#troubleshooting)

---

## How it works (the big picture)

```
┌────────────────────┐    ┌──────────────────┐    ┌───────────────────┐    ┌──────────────────┐    ┌─────────────┐
│ 20 RSS feeds       │ →  │ WebFetcher       │ →  │ NewsletterSummar- │ →  │ NewsletterBuilder│ →  │ EmailSender │
│ (config/sources.py)│    │ fetch, filter,   │    │ izer (Claude API) │    │ Jinja2 → HTML    │    │ Gmail SMTP  │
│                    │    │ dedupe, score,   │    │ writes intro +    │    │                  │    │             │
│                    │    │ keep top N       │    │ paragraphs +      │    │ (optional: save  │    │ (skipped in │
│                    │    │                  │    │ closing           │    │  .html to disk)  │    │  --dry-run) │
└────────────────────┘    └──────────────────┘    └───────────────────┘    └──────────────────┘    └─────────────┘
     list of feeds          list[Article]            dict(intro, items,        HTML string           email sent
                                                     closing)
```

Data moves through the pipeline in three shapes:

| Stage | Output type | What it contains |
|---|---|---|
| Fetch & rank | `list[Article]` | Title, source, author, a short summary from the feed, URL, publish date, topic, and score |
| Summarize | `dict` | `intro` (str), `items` (list of dicts with the Claude-written paragraph plus article metadata), `closing` (str) |
| Build | `str` | The complete HTML email |

---

## Project structure

```
Agent_Newsletter/
├── main.py                      # Entry point: runs the whole pipeline, handles CLI flags
├── requirements.txt             # Python dependencies
├── .env.example                 # Template for environment variables (copy to .env)
├── newsletter_2026-04-04.html   # A real generated edition (sample output)
│
├── config/
│   ├── sources.py               # ACTIVE: RSS feeds, tiers, TOP_N, MAX_DAYS_BACK
│   └── actors.py                # UNUSED: Twitter accounts & subreddits (earlier design)
│
├── fetchers/
│   ├── web_fetcher.py           # ACTIVE: RSS fetching, scoring, deduplication
│   ├── twitter_fetcher.py       # UNUSED: Twitter/X API v2 fetcher (tweepy)
│   └── reddit_fetcher.py        # UNUSED: Reddit fetcher (praw)
│
├── agents/
│   └── summarizer.py            # Calls Claude to write the newsletter text
│
├── newsletter/
│   ├── builder.py               # Renders the Jinja2 template into HTML
│   └── sender.py                # Sends the HTML email over SMTP
│
└── templates/
    └── newsletter.html          # Jinja2 HTML email template (dark theme)
```

The `__init__.py` files in each folder are empty. They only make the folders importable as Python packages.

---

## Setup

### 1. Requirements

- **Python 3.10 or newer.** The code uses the `datetime | None` type-hint syntax, which needs 3.10+.
- An **Anthropic API key**, from <https://console.anthropic.com>.
- A **Gmail account with an App Password** (or another SMTP account) to send from.

### 2. Install dependencies

From the repository root (`AI_Agents/`), which is where the `venv/` that `.gitignore` expects lives:

```bash
python -m venv venv
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r Agent_Newsletter/requirements.txt
```

[requirements.txt](requirements.txt) installs:

| Package | Used for |
|---|---|
| `anthropic` | Calling the Claude API |
| `feedparser` | Downloading and parsing RSS/Atom feeds |
| `python-dotenv` | Loading credentials from the `.env` file |
| `jinja2` | Rendering the HTML email template |

### 3. Configure credentials

Copy the example file and fill it in:

```bash
cd Agent_Newsletter
cp .env.example .env
```

Variables the active pipeline reads:

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Claude API key |
| `EMAIL_SENDER` | Yes (unless `--dry-run`) | The Gmail address that sends the newsletter |
| `EMAIL_PASSWORD` | Yes (unless `--dry-run`) | A Gmail **App Password**, not your normal password (see below) |
| `EMAIL_RECIPIENTS` | Yes (unless `--dry-run`) | Comma-separated list, e.g. `a@x.com, b@y.com` |
| `SMTP_HOST` | No | Defaults to `smtp.gmail.com` |
| `SMTP_PORT` | No | Defaults to `587` (STARTTLS) |

The `TWITTER_BEARER_TOKEN` and `REDDIT_*` variables in `.env.example` belong to the unused fetchers. The current pipeline ignores them.

**Getting a Gmail App Password:**
1. Turn on 2-Step Verification on your Google account.
2. Go to <https://myaccount.google.com/apppasswords>.
3. Generate an App Password for "Mail".
4. Paste the 16-character code into `EMAIL_PASSWORD`.

> ⚠️ **Security:** `.env` is git-ignored, but `.env.example` is committed. Only put placeholder values in `.env.example`, never real emails or passwords.

---

## Running it

Run all commands from inside the `Agent_Newsletter/` folder. The imports (`from config.sources import ...`) and the `.env` lookup both depend on it.

```bash
python main.py                         # Full run: fetch → write → build → SEND email
python main.py --dry-run               # Build everything but do NOT send the email
python main.py --save-html             # Full run, and also save the HTML to disk
python main.py --dry-run --save-html   # Recommended for testing: build + save, no email
```

| Flag | Effect |
|---|---|
| `--dry-run` | Skips the email step. Email credentials aren't needed. |
| `--save-html` | Writes `newsletter_YYYY-MM-DD.html` to the current directory |

Every run calls the Claude API, including dry runs, so every run costs a small amount of money.

### What the console output looks like

```
14:02:11  INFO      ╔══════════════════════════════════════════╗
14:02:11  INFO      ║   AI & Crypto Pulse — Newsletter Agent   ║
14:02:11  INFO      ║   Edition: April 04, 2026                ║
14:02:11  INFO      ╚══════════════════════════════════════════╝
14:02:11  INFO      === Fetching articles from RSS feeds ===
14:02:12  INFO      [RSS] MIT Technology Review (AI & Machine Learning) → 6 articles
14:02:12  WARNING   [RSS] Some Feed: failed — ...
...
14:02:20  INFO      [RSS] Total unique articles: 143 — keeping top 5
14:02:20  INFO      === Top 5 articles selected ===
14:02:20  INFO        #01  [TechCrunch AI       ] Anthropic says Claude Code subscribers will need...
...
14:02:20  INFO      === Summarizing with Claude ===
14:02:20  INFO      [Summarizer] Calling Claude API...
14:02:35  INFO      === Building newsletter HTML ===
14:02:35  INFO      [Builder] Newsletter HTML rendered successfully.
14:02:35  INFO      === Sending email ===
14:02:36  INFO      [Sender] Newsletter sent to 1 recipient(s): ...
14:02:36  INFO      === Done! ===
```

---

## Module-by-module walkthrough

### `main.py` — the orchestrator

[main.py](main.py) connects all the pieces. In order, it:

1. Calls `load_dotenv()` **before** importing the project modules, so every module sees the environment variables from `.env`.
2. Sets up logging in the format `HH:MM:SS  LEVEL  message`.
3. Parses the `--save-html` and `--dry-run` flags.
4. Records the current time in **UTC**. That timestamp becomes the edition date everywhere (subject line, header, filename).
5. **Step 1, fetch:** creates `WebFetcher(max_days_back=MAX_DAYS_BACK)` and calls `fetch_top_articles(RSS_SOURCES, TOP_N)`. If nothing comes back (usually no internet), it logs an error and exits with code `1`.
6. Logs the selected articles as a numbered list.
7. **Step 2, summarize:** `NewsletterSummarizer().summarize(articles, date=now)`.
8. **Step 3, build:** `NewsletterBuilder().build(summary, date=now)`, then saves to disk if `--save-html` is set.
9. **Step 4, send:** `EmailSender().send(html, date=now)`, unless `--dry-run` is set.

The `EmailSender` is created only when an email is actually sent, so a dry run works without email credentials.

---

### `config/sources.py` — the news sources

[config/sources.py](config/sources.py) holds the three settings that control what goes into the newsletter.

**`RSS_SOURCES`** is a dict mapping a **topic name** to a list of feeds. Each feed has a `name`, a `url`, and a `tier` (its authority level):

| AI & Machine Learning | Tier | Crypto & Blockchain | Tier |
|---|---|---|---|
| MIT Technology Review | 1 | CoinDesk | 1 |
| VentureBeat AI | 1 | CoinTelegraph | 1 |
| TechCrunch AI | 1 | Decrypt | 1 |
| The Verge AI | 1 | The Block | 1 |
| Wired AI | 1 | Blockworks | 1 |
| OpenAI Blog | 1 | Bitcoin Magazine | 2 |
| DeepMind Blog | 1 | CryptoSlate | 2 |
| Ars Technica | 2 | BeInCrypto | 2 |
| AI News | 2 | NewsBTC | 2 |
| Hugging Face Blog | 2 | CryptoNews | 2 |

All of these are public RSS feeds, so no API keys or accounts are needed.

**`MAX_DAYS_BACK = 7`**: articles older than 7 days are dropped.

**`TOP_N = 5`**: the number of articles in the newsletter. The comment in the file says this was kept low for **cheap testing** and should be raised to `10` for a "production" run. More articles means a longer prompt and output, which costs more.

The topic names (`"AI & Machine Learning"`, `"Crypto & Blockchain"`) matter downstream. They appear as section headings in the email, and the template colors a section **blue if the topic name contains "AI"** and **green otherwise**.

---

### `fetchers/web_fetcher.py` — fetching and ranking

[fetchers/web_fetcher.py](fetchers/web_fetcher.py) does the data collection.

#### The `Article` dataclass

```python
@dataclass
class Article:
    id: str              # feed entry id (falls back to the link)
    source: str          # outlet name, e.g. "CoinDesk"
    author: str          # entry author, or the outlet name if missing
    title: str
    summary: str         # feed excerpt, HTML stripped, max 400 chars
    url: str
    published_at: datetime   # timezone-aware UTC
    topic: str           # "AI & Machine Learning" | "Crypto & Blockchain"
    score: float         # authority + recency score
    extra: dict          # currently {"tier": 1 or 2}
```

#### The process, step by step

1. **Download every feed** with `feedparser.parse(url)`. Each feed sits in its own `try/except`, so a broken or unreachable feed only logs a warning and the run continues.
2. **Find each entry's date.** `_parse_date` tries `published_parsed`, then `updated_parsed`, then `created_parsed`, and builds a UTC `datetime`. **Entries with no date are dropped.**
3. **Drop old entries** published before `now − MAX_DAYS_BACK days`.
4. **Score** each remaining article:

   ```
   score = tier_weight + recency_bonus
   ```

   | Tier | Weight | | Article age | Recency bonus |
   |---|---|---|---|---|
   | 1 | 30 | | ≤ 24 hours | 30 |
   | 2 | 20 | | ≤ 48 hours | 20 |
   | 3 | 10 | | older (up to 7 days) | 10 |

   The highest possible score is **60** (a Tier-1 source in the last 24 hours) and the lowest is **30** (a Tier-2 source, 2–7 days old). A Tier 3 exists in the code, but no current feed uses it.

   The scoring only looks at source reputation and freshness. RSS feeds don't include likes, shares, or view counts, so the code can't tell which story is "bigger".

5. **Clean the summary:** `_strip_html` removes HTML tags with a regex, collapses whitespace, and truncates to 400 characters.
6. **Deduplicate by URL** across all feeds, keeping the first occurrence.
7. **Sort by score** (highest first) and **keep the top `TOP_N`**.

Many articles end up with the same score, because the score can only take a handful of values. Python's sort is stable, so ties keep their original order: the order the feeds are listed in `sources.py`, with AI feeds before crypto feeds, and the order each feed lists its entries.

---

### `agents/summarizer.py` — the Claude writer

[agents/summarizer.py](agents/summarizer.py) is the AI part of the agent.

**Model:** `claude-haiku-4-5-20251001`, Anthropic's cheapest and fastest model at the time. A comment suggests switching to `claude-sonnet-4-6` for higher-quality "production" writing. The response limit is `max_tokens=4096`.

**Initialization** reads `ANTHROPIC_API_KEY` and raises a `ValueError` if it's missing.

#### How the prompt is built

`_format_articles_for_prompt` turns each article into a block like this:

```
ARTICLE 1:
  Topic:       AI & Machine Learning
  Source:      TechCrunch AI
  Author:      Jane Doe
  Published:   April 03, 2026 at 18:20 UTC
  Title:       ...
  Summary:     ...
  URL:         https://...
```

The prompt then asks Claude to act as **"an expert tech and finance journalist writing a premium weekly newsletter"** and write:

1. An **introduction** (3–4 sentences) that sets up the week's themes.
2. **One paragraph per article** (4–6 sentences) explaining what happened, why it matters, and the source and author, in the style of journalism rather than a summary.
3. A **closing** (2–3 sentences) looking ahead to the coming week.

The prompt says: no bullet points, only flowing prose.

#### Structured output with delimiters

So the code can split the response reliably, Claude must wrap each section in tags:

```
[INTRO] ... [/INTRO]
[ITEM_1] ... [/ITEM_1]
[ITEM_2] ... [/ITEM_2]
...
[CLOSING] ... [/CLOSING]
```

`_parse_response` finds each tag with `str.find` and extracts the text between the opening and closing tags. If Claude leaves a tag out, that section comes back as an empty string. The program does not crash.

#### What it returns

```python
{
  "intro": "…",
  "items": [
    {
      "rank": 1,                     # position in the score ranking
      "paragraph": "…",              # Claude's paragraph
      "source": "TechCrunch AI",
      "author": "…",
      "url": "…",
      "title": "…",
      "published_at": "Apr 03, 2026",
      "topic": "AI & Machine Learning",
      "summary_preview": "first 120 chars of the RSS summary…"
    },
    ...
  ],
  "closing": "…"
}
```

The metadata (title, URL, source, and so on) comes from the original `Article`, not from Claude. Links and titles are always the real ones; only the paragraphs are AI-written.

---

### `newsletter/builder.py` — HTML rendering

[newsletter/builder.py](newsletter/builder.py) loads `templates/newsletter.html` with Jinja2 and fills it in.

- **Reordering:** items are sorted so **every AI article comes before every crypto article**. Inside each group they stay in rank order. This gives the email two clean sections.
- **Template variables passed:**
  - `edition_title`: `"AI & Crypto Pulse — April 04, 2026"` (the browser tab title)
  - `date`: `"Saturday, April 04, 2026"`
  - `intro`, `items`, `closing`: from the summarizer
- **`save()`** writes the HTML to `newsletter_YYYY-MM-DD.html` in the current working directory. The included sample file was made this way.

---

### `templates/newsletter.html` — the email design

[templates/newsletter.html](templates/newsletter.html) is a single-column (680px max) **dark-theme** design with all CSS in one `<style>` block:

1. **Header:** a small "WEEKLY INTELLIGENCE BRIEF" label, the title **"AI & Crypto Pulse"** in a blue → purple → green gradient, a tagline, and the date.
2. **Intro box:** Claude's introduction, with a blue left border.
3. **Topic sections:** a colored dot and heading appear whenever the topic changes from one item to the next. This uses Jinja's `namespace()` trick to remember the previous topic inside the loop. A thin divider separates the sections.
4. **News cards**, one per article:
   - a rank badge (`#1`, `#2`, …), blue for AI and green for crypto
   - a source tag (e.g. `COINDESK`) and the publish date
   - the article title
   - Claude's paragraph
   - an italic quote of the first 120 characters of the original RSS summary
   - a "→ Read full article" link
5. **Closing box:** Claude's closing paragraph.
6. **Footer:** "Powered by Claude AI", a fixed list of example sources, and the date.

---

### `newsletter/sender.py` — email delivery

[newsletter/sender.py](newsletter/sender.py) sends the email with Python's built-in `smtplib`.

- Reads `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENTS`, and optionally `SMTP_HOST` and `SMTP_PORT`. It raises a clear `ValueError` if any required value is missing.
- Splits `EMAIL_RECIPIENTS` on commas and trims spaces, so it supports **multiple recipients**.
- Builds a `multipart/alternative` email containing:
  - a **plain-text fallback** ("Please view this email in an HTML-compatible client…")
  - the **HTML newsletter**
  - Email clients show the HTML version when they can.
- Subject line: **`AI & Crypto Pulse — April 04, 2026`**.
- Connects to the SMTP server, upgrades to TLS (`starttls`), logs in, and sends **one email** with every recipient in the `To:` header. All recipients can see each other's addresses.

---

## Unused / experimental code (Twitter and Reddit)

The project contains code from an **earlier version of the idea**: a newsletter built from **social media posts** (tweets and Reddit posts ranked by likes) instead of news articles. The RSS approach replaced it, likely because the Twitter/X API costs at least $100 a month for the tier that can read other users' tweets. The old files were never deleted:

| File | What it does | Status |
|---|---|---|
| [config/actors.py](config/actors.py) | Lists ~33 Twitter accounts (OpenAI, AnthropicAI, sama, karpathy, VitalikButerin, cz_binance, …) grouped as `ai_official`, `ai_influencers`, `crypto_official`, `crypto_influencers`, plus 12 subreddits (r/MachineLearning, r/LocalLLaMA, r/CryptoCurrency, r/ethereum, …). Also has its own `TOP_N = 10`. | Not imported anywhere |
| [fetchers/twitter_fetcher.py](fetchers/twitter_fetcher.py) | Uses `tweepy` and the Twitter API v2 to get each account's tweets from the last 24 h (no retweets or replies) and rank them by like count. Defines a `Post` dataclass. Handles "forbidden" (API tier too low) and "not found" errors. | Not imported by `main.py` |
| [fetchers/reddit_fetcher.py](fetchers/reddit_fetcher.py) | Uses `praw` to read the 50 "hot" posts of each subreddit, keep those from the last 24 h, and rank by upvotes. Reuses the `Post` dataclass. Adds the subreddit, comment count, and upvote ratio. | Not imported by `main.py` |

`tweepy` and `praw` **are not in `requirements.txt`**, so importing these files fails unless you install them yourself (`pip install tweepy praw`). Their output type (`Post`) is also different from what the summarizer expects (`Article`), so reconnecting them would take some adaptation code.

You can delete these files to tidy the project, or keep them as a starting point for adding social signals later.

---

## Customization guide

| I want to… | Change this |
|---|---|
| Include more or fewer articles | `TOP_N` in [config/sources.py](config/sources.py) |
| Allow older or only newer articles | `MAX_DAYS_BACK` in [config/sources.py](config/sources.py) |
| Add or remove a news source | Add or remove a `{"name", "url", "tier"}` entry in `RSS_SOURCES` |
| Add a whole new topic (e.g. "Quantum") | Add a new key to `RSS_SOURCES`. The template shows it in green unless the name contains "AI". |
| Get better writing quality | Change `MODEL` in [agents/summarizer.py](agents/summarizer.py) to a stronger model, e.g. a current Sonnet or Opus |
| Change tone, length, or language | Edit the prompt text in `NewsletterSummarizer.summarize` |
| Change how articles are ranked | `TIER_WEIGHTS` and the recency-bonus block in `_parse_feed` ([fetchers/web_fetcher.py](fetchers/web_fetcher.py)) |
| Change the look of the email | [templates/newsletter.html](templates/newsletter.html) |
| Change the newsletter name or subject | `edition_title` in [newsletter/builder.py](newsletter/builder.py), `subject` in [newsletter/sender.py](newsletter/sender.py), and the header in the template |
| Use Outlook or another email provider | Set `SMTP_HOST` and `SMTP_PORT` in `.env` |

---

## Scheduling it to run weekly

The script has no scheduler built in. It runs once and exits. To make it a real weekly newsletter:

**Windows (Task Scheduler):**
1. Open Task Scheduler → *Create Basic Task* → choose a weekly trigger.
2. Action: *Start a program*
   - Program: `C:\path\to\AI_Agents\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\AI_Agents\Agent_Newsletter` ← required, so imports and `.env` resolve

**macOS / Linux (cron)**, e.g. every Monday at 08:00:

```cron
0 8 * * 1 cd /path/to/AI_Agents/Agent_Newsletter && /path/to/AI_Agents/venv/bin/python main.py >> newsletter.log 2>&1
```

---

## Known limitations and quirks

These are worth knowing if you pick the project up again:

1. **No topic balancing.** The top `TOP_N` articles are chosen across all topics together. One week's newsletter could be entirely AI or entirely crypto.
2. **Rank badges can look out of order.** Ranks come from the score order, but the builder then puts all AI items first. The email can show `#2, #4` in the AI section followed by `#1, #3, #5` in the crypto section.
3. **Coarse scoring.** Scores can only be 30, 40, 50, or 60, so there are many ties, and ties are broken by feed order in `sources.py`.
4. **Near-duplicates get through.** Deduplication is by exact URL. The same story covered by CoinDesk and CoinTelegraph can appear twice.
5. **Feed URLs go stale.** Outlets change or remove their RSS feeds. Failing feeds only log a warning, so check the logs now and then for `[RSS] ...: failed` or feeds that always return 0 articles.
6. **Missing sections fail silently.** If Claude doesn't follow the `[ITEM_n]` format exactly, that card shows an empty paragraph without any error.
7. **Footer source list is hard-coded** in the template. It doesn't change when you edit `sources.py`.
8. **HTML is not escaped.** Jinja2 is created without `autoescape`, so a `<` or `&` in a title or paragraph goes into the HTML as-is. This is usually harmless for an email you send to yourself.
9. **Recipients see each other.** Everyone is placed in `To:`. Use BCC for a public mailing list.
10. **Plain-text version is a placeholder.** It doesn't contain the actual newsletter content.
11. **`--save-html` writes to the current directory**, so run the script from `Agent_Newsletter/` to keep the files together.
12. **Edition date is UTC.** If you run it late in the evening in a timezone ahead of or behind UTC, the date may differ from your local date by one day.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ModuleNotFoundError: No module named 'config'` | You aren't running from inside `Agent_Newsletter/`. `cd` there first. |
| `ModuleNotFoundError: No module named 'anthropic'` (or `feedparser`, …) | Activate the venv and run `pip install -r requirements.txt` |
| `ValueError: ANTHROPIC_API_KEY is not set` | `.env` is missing or in the wrong folder. It must be in `Agent_Newsletter/`. |
| `No articles fetched. Check your internet connection.` | No internet, or every feed failed. Check the warnings above it in the log. |
| `anthropic.AuthenticationError` | Invalid API key |
| `anthropic` error about the model not being found | The model ID in `summarizer.py` has been retired. Update `MODEL` to a current model. |
| `smtplib.SMTPAuthenticationError` (535) | You used your normal Gmail password, or 2-Step Verification is off. Use an **App Password**. |
| `ValueError: EMAIL_RECIPIENTS must be set` | Add at least one address to `.env`, or run with `--dry-run` |
| The email looks plain or broken | Some clients (notably Outlook desktop) ignore modern CSS such as gradients and flexbox. Gmail web and mobile apps render it best. |
| `TypeError: unsupported operand type(s) for \|` | Python is older than 3.10. Upgrade. |
