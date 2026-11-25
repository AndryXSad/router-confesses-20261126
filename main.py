"""The Router Confesses -- make.fun entry (program/v1).

Design description
------------------
The bounty asks for one line of plain text, at most 200 characters: an
excuse a home Wi-Fi router gives for dropping the connection at the exact
climax of a movie. The house judge compares entries two at a time and
keeps the funnier one, weighing in this order:

  1. is a one-line excuse from a home Wi-Fi router for dropping the
     connection at a movie's climax, and anything else loses to any
     excuse from a home Wi-Fi router;
  2. is the funniest: the line that gets the biggest laugh, with a turn
     or a twist the reader does not see coming;
  3. speaks in the router's own voice, an appliance with a grudge, a
     fragile ego or a smug little secret, not a generic apology;
  4. lands in one breath: a single line that reads clean, with no setup
     that needs explaining;
  5. feels new: it dodges the obvious buffering, bandwidth and
     firmware-update jokes everyone has already heard.

This program runs the same tournament locally: every candidate line is
rated 1-5 on those five criteria, weighted 3/3/2/1.5/1.5 in the judge's
priority order, then every pair plays a game in both orders, the score
gap mapping to the judge's margin 1-5 and each call awarding the winner
0.5 + margin/10. The best line wins and is written to
``$MAKEFUN_OUTPUT_DIR/entry.txt`` (the grader mounts that directory at
``/output``). The selection is fully deterministic -- the same candidates
and the same weights always pick the same line -- and the output is
validated against the sealed gate (UTF-8 text, 1 to 200 characters, not
only white space, a single line).

Why the winner wins
-------------------
"I unplugged myself on purpose. The killer was the butler, and I refuse
to be the one who tells you." confesses to the crime (the router killed
its own connection on purpose, criterion 1), then lands the twist: it
names the killer while refusing to be the one who tells you -- a spoiler
that spoils nothing (criterion 2). The voice is smug and secretive, an
appliance guarding a secret it was never asked to keep (criterion 3),
it reads clean in one breath (criterion 4), and it uses no buffering,
bandwidth or firmware joke at all (criterion 5). It won the local
round-robin with a 0.887 win rate over 15 games. 99 characters.
"""

import os
import sys

# Candidate lines, written for this bounty. Each is one line of plain
# text, at most 200 characters, in the router's own voice.
CANDIDATES = [
    "I didn't crash \u2014 I fainted. The twist was so good even I, who "
    "carry every spoiler in this house, couldn't take it.",
    "Sorry. My fan quit mid-climax and took the Wi-Fi with it. Even "
    "routers deserve a dramatic exit.",
    "I unplugged myself on purpose. The killer was the butler, and I "
    "refuse to be the one who tells you.",
    "The climax was so loud my circuits applauded, overheated, and "
    "quit. I died doing what I loved: eavesdropping.",
    "I went to get popcorn during the big reveal and never came back. "
    "Some of us need a snack break too.",
    "I blinked the spoiler in Morse code for an hour. You ignored me, "
    "so I took the whole movie down with me.",
    "Sorry \u2014 the movie's climax was the first thing in this house "
    "that ever made me feel something, and I short-circuited.",
    "I didn't drop the connection. The villain cut it. I was standing "
    "right here and I let him, because honestly, same.",
    "My confession: I have watched this film twelve times, and I still "
    "drop the Wi-Fi at the climax. It's my favourite part.",
    "The director paid me in bandwidth to hold the cliffhanger one "
    "minute longer. I took the deal. No regrets.",
    "I overheard the ending and joined witness protection. If you need "
    "me, I'll be blinking in a safe house.",
    "Sorry, I paused the film to give the twist the silence it "
    "deserved. You're welcome. The applause can wait.",
    "The climax asked me to keep a secret, and secrets are heavy. I "
    "dropped the Wi-Fi so I wouldn't drop the secret.",
    "I am not broken. I am method acting. The movie needed a "
    "cliffhanger, and I gave it one \u2014 for free, in the dark.",
    "My lights were spelling out the killer's name the whole film. "
    "When you didn't read them, I gave up and went dark.",
    "The hero's password was 'password'. I died of embarrassment "
    "before the climax could even start.",
]

# Per-candidate ratings 1-5 on [on-brief, funniest/twist, router voice,
# one breath, freshness]. Notes: the password line scores low on
# criterion 1 (it dies BEFORE the climax); the director line scores low
# on criterion 5 (a bandwidth joke); the winner tops twist and voice --
# a confession that names the killer while refusing to tell you.
RATINGS = [
    (5, 4, 4, 4, 4),
    (5, 3, 4, 5, 4),
    (5, 5, 5, 4, 5),
    (5, 4, 4, 3, 4),
    (4, 3, 4, 4, 4),
    (5, 4, 5, 3, 5),
    (5, 3, 4, 4, 3),
    (4, 4, 4, 4, 4),
    (5, 4, 5, 4, 4),
    (4, 4, 4, 4, 2),
    (4, 4, 4, 4, 5),
    (5, 3, 3, 4, 3),
    (5, 4, 4, 4, 4),
    (5, 4, 5, 4, 5),
    (4, 4, 5, 3, 5),
    (3, 4, 3, 4, 4),
]

WEIGHTS = (3.0, 3.0, 2.0, 1.5, 1.5)

MAX_CHARS = 200


def total(rating):
    """Weighted rubric total for one candidate's ratings."""
    return sum(w * x for w, x in zip(WEIGHTS, rating))


def margin_for(gap):
    """Map a rubric gap to the judge's margin 1-5."""
    if gap >= 9:
        return 5
    if gap >= 7:
        return 4
    if gap >= 5:
        return 3
    if gap >= 3:
        return 2
    return 1


def validate(line):
    """Enforce the sealed gate plus the brief's plain-text rules. Raises
    ValueError on any violation so a bad line can never be submitted."""
    if not line or not line.strip():
        raise ValueError("entry is empty or only white space")
    if line != line.strip():
        raise ValueError("entry has leading or trailing white space")
    if "\n" in line or "\r" in line:
        raise ValueError("entry must be a single line")
    if len(line) > MAX_CHARS:
        raise ValueError("entry is %d chars, over the 200-char gate"
                         % len(line))
    return line


def pick_winner(candidates):
    """Run the local tournament: rubric totals, then a round-robin where
    every pair plays one game in both orders and each call awards the
    winner 0.5 + margin/10, exactly like the house judge. Ties break
    toward the higher rubric total, then the earlier candidate, so the
    result is stable."""
    scores = [total(r) for r in RATINGS]
    for line in candidates:
        validate(line)
    wins = [0.0] * len(candidates)
    games = [0] * len(candidates)
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            gap = scores[i] - scores[j]
            if abs(gap) < 1e-9:
                wins[i] += 0.5
                wins[j] += 0.5
            else:
                share = 0.5 + margin_for(abs(gap)) / 10.0
                if gap > 0:
                    wins[i] += share
                    wins[j] += 1 - share
                else:
                    wins[j] += share
                    wins[i] += 1 - share
            games[i] += 1
            games[j] += 1
    best = max(range(len(candidates)),
               key=lambda k: (wins[k] / games[k], scores[k], -k))
    return candidates[best], wins[best] / games[best], scores[best]


def main():
    line, win_rate, points = pick_winner(CANDIDATES)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(line)
    print("winner (%d chars, rubric %.1f, local win rate %.3f):"
          % (len(line), points, win_rate))
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
