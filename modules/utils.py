import re, json

def robust_json_extract(text):
    """Extract valid JSON even if surrounded by text."""
    match = re.search(r"(\[.*\]|\{.*\})", text, flags=re.S)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            try:
                return json.loads(match.group(1).replace("'", '"'))
            except:
                return None
    return None

def normalized_mean_score(df_scores):
    """Convert mean (1..4) to normalized (0..1)."""
    if df_scores.empty:
        return 0.0
    m = df_scores["score"].astype(float).mean()
    return float((m - 1) / 3.0)
