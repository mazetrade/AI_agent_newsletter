# =============================================================================
# TRACKED ACTORS — Official accounts and top influencers
# Categories: AI, Crypto, Blockchain
# =============================================================================

# --- Twitter / X accounts ---
TWITTER_ACCOUNTS = {
    "ai_official": [
        "OpenAI",
        "AnthropicAI",
        "GoogleDeepMind",
        "Meta_AI",
        "MistralAI",
        "nvidia",
        "huggingface",
        "xai",
    ],
    "ai_influencers": [
        "sama",          # Sam Altman — OpenAI CEO
        "ylecun",        # Yann LeCun — Meta Chief AI Scientist
        "karpathy",      # Andrej Karpathy — ex-OpenAI
        "lexfridman",    # Lex Fridman — AI researcher/podcaster
        "GaryMarcus",    # Gary Marcus — AI critic/researcher
        "emollick",      # Ethan Mollick — AI in business
        "goodfellow_ian",# Ian Goodfellow — GAN inventor
    ],
    "crypto_official": [
        "ethereum",
        "Bitcoin",
        "Coinbase",
        "binance",
        "solana",
        "Uniswap",
        "chainlink",
        "0xPolygon",
        "arbitrum",
        "avalancheavax",
    ],
    "crypto_influencers": [
        "VitalikButerin",  # Ethereum co-founder
        "cz_binance",      # CZ — Binance founder
        "APompliano",      # Anthony Pompliano — crypto investor
        "aantonop",        # Andreas Antonopoulos — Bitcoin educator
        "RaoulGMI",        # Raoul Pal — macro + crypto
        "DocumentingBTC",  # Bitcoin milestones tracker
        "NovogratzM",      # Mike Novogratz — Galaxy Digital CEO
        "naval",           # Naval Ravikant — investor/philosopher
    ],
}

# --- Reddit subreddits ---
REDDIT_SUBREDDITS = {
    "ai": [
        "artificial",
        "MachineLearning",
        "singularity",
        "ChatGPT",
        "LocalLLaMA",
        "OpenAI",
    ],
    "crypto_blockchain": [
        "CryptoCurrency",
        "ethereum",
        "Bitcoin",
        "solana",
        "defi",
        "web3",
    ],
}

# --- Topic labels for the newsletter sections ---
TOPICS = {
    "AI & Machine Learning": ["ai_official", "ai_influencers", "ai"],
    "Crypto & Blockchain": ["crypto_official", "crypto_influencers", "crypto_blockchain"],
}

# Number of top posts to include in the newsletter
TOP_N = 10
