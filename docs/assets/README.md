# docs/assets — Screenshot & Visual Assets Guide

This directory holds visual assets (screenshots, diagrams) for documentation.

## Why No Screenshots Are Pre-Committed

Screenshots of a Streamlit app must be captured from a **live running instance** to be accurate.  
Fabricated or stale screenshots erode trust in a portfolio project.  
All visuals here are added manually after a real run.

---

## How to Add Screenshots Safely

### 1. Run the pipeline
```bash
python -m traffic_analytics_demo.cli all --days 30 --seed 42 --road-segments 24 --accidents 500 --violations 1600 --sensors-rows 5000
```

### 2. Launch the dashboard
```bash
streamlit run app/streamlit_app.py
```

### 3. Capture screenshots
Use any screen capture tool. Recommended naming convention:

| File | Content |
|------|---------|
| `dashboard_overview.png` | Full dashboard landing tab |
| `dashboard_risk_map.png` | Risk map / road segment heatmap |
| `dashboard_model.png` | Model calibration + metrics tab |
| `dashboard_scenarios.png` | Scenario intervention ranking tab |
| `dashboard_executive.png` | Executive summary tab |

### 4. Optimize before committing
```bash
# Install optipng (Windows: winget install optipng, macOS: brew install optipng)
optipng -o5 docs/assets/*.png
```
Keep individual files under **500 KB**. Use PNG for UI screenshots (lossless).

### 5. Add to README
Reference in `README.md` with a relative path:
```markdown
![Dashboard Overview](docs/assets/dashboard_overview.png)
```

---

## Architecture Diagram

The ASCII architecture diagram in `README.md` is always kept in sync with code.  
If you add a rendered Mermaid diagram, save it as `docs/assets/architecture.png` and update the README link.

---

## Security Note

- Do not capture screenshots that show local file paths, environment variables, or API keys.
- Crop screenshots to exclude browser address bars if they reveal internal hostnames.
- No real data may appear in committed screenshots — only synthetic demo outputs.
