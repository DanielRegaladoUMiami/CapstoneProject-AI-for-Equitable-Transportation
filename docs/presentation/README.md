# Deloitte CEO Deck · 20-minute demo presentation

## Files
- `deloitte_ceo_deck.md` — 11 slides, Marp-formatted, Deloitte-green + Apple-minimal styling
- `speaker_script.md` — word-for-word script, paced for slow delivery (~110 wpm), 20-min total with ~8-min live demo

## Render to PDF or PPTX

```bash
# One-time install
brew install marp-cli
# or: npm install -g @marp-team/marp-cli

# Render
cd docs/presentation
marp deloitte_ceo_deck.md --pdf
marp deloitte_ceo_deck.md --pptx
marp deloitte_ceo_deck.md -w        # live preview in browser
```

## Timing budget
| Segment | Time |
|---|---|
| Slides 1–5 (intro + engine) | 6:45 |
| Slide 6 → Live demo | 8:00 |
| Slides 7–11 (payoff + close) | 5:15 |
| **Total** | **~20:00** |

## Delivery notes
- Slow down at the 51-Critical-tracts slide. That number is the emotional anchor.
- The Scenario Comparison tab is the tab a CEO will remember. Spend the most demo time there.
- Do not speak over the map-rendering pause — let the visual land.
- The "honesty" slide is deliberate. Deloitte CEOs read honesty as competence.
