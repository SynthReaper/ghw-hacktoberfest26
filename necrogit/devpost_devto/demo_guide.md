# NecroGit — 3-Minute Video Pitch & Demo Script
*Hacktoberfest 2026 Week 4: "Ghost in the Machine" (Halloween & Día de los Muertos)*

---

## ⏱️ Video Choreography (180 Seconds Total)

### 0:00 - 0:30 | The Hook & The Graveyard
- **Visual**: Camera opens on a candlelit desk or dark terminal displaying `graveyard/dead_urlfetch/urlfetch.py` with ancient Python 2 syntax (`import urllib2`, `print "fetching..."`, abandoned since 2013).
- **Audio / Script**:
  > "Over 40 million open-source repositories on GitHub lie dead in the digital graveyard. Forgotten by their creators, killed by bitrot, and haunted by deprecated APIs.
  > Today is Halloween and Día de los Muertos—the time we honor our ancestors. Why let brilliant open-source software rot in the dark when an agent can summon its spirit and bring it back to life?
  > Meet NecroGit: The Open-Source Code Necromancer."

### 0:30 - 1:15 | The Séance Crypt Dashboard & Telemetry
- **Visual**: Switch to Next.js 15 Séance Crypt Dashboard (`localhost:3000`). Show the Bitrot Meter (-94.5% drop), the tombstone cards, and click "Commence Digital Séance".
- **Audio / Script**:
  > "Here is our Séance Crypt. With one command, our Mastra agent awakens.
  > First, Prior Labs' TabPFN-3.5 analyzes historical commit dropoffs and dependency entropy to calculate the repository's exact 'Time of Death'—in this case, 2013—and detects 5 zombie dependencies with an 88% vulnerability risk.
  > Meanwhile, Browserbase and Stagehand v4 scour the Internet Archive's Wayback Machine to retrieve the original author's vintage documentation and design notes from dead Google Code archives."

### 1:15 - 2:00 | The Local Exorcism: Gemma 2 & Zero Leakage
- **Visual**: Open the Code Diff Viewer. Show the side-by-side AST comparison: raw Python 2 on the left, clean typed Python 3.13 on the right with generated pytest tests. Show Ollama running locally in terminal.
- **Audio / Script**:
  > "Here is why open innovation matters: resurrecting private or proprietary vintage code requires zero data leakage.
  > Google's Gemma 2 runs 100% locally on Ollama to banish urllib2, replace unthreadsafe code with re-entrant locks, and generate a full pytest suite with modern PEP 621 packaging. Not a single token is sent to closed cloud APIs."

### 2:00 - 2:40 | The Haunted Voice of the Codebase (ElevenLabs)
- **Visual**: Click Play on the Séance Player. Eerie voice narrates: *"Hark, traveller of the terminal. I am the ghost of urlfetch-py2..."*
- **Audio / Script**:
  > "ElevenLabs gives the resurrected repository a voice—reading the original author's final commit messages and confirming that its code breathes once more."

### 2:40 - 3:00 | Conclusion & Impact
- **Visual**: Terminal running `pytest storage/resurrected/urlfetch-py2/tests/test_revived.py` passing 100% green. Sentry agent trace showing all completed spans.
- **Audio / Script**:
  > "In under 30 seconds, a repository dead for 13 years is now hardened, tested, and running on Python 3.13.
  > Happy Día de los Muertos. Check out the code on GitHub at SynthReaper/ghw-hacktoberfest26. Thank you!"
