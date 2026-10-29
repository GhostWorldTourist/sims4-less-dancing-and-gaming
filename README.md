# Less Dancing and Gaming

Sims stop running to the stereo every time they're in a good mood, and stop
camping on the Motion Gaming Mat. They still dance and game, enjoy it exactly
as much as before, and do it whenever a party, club, wedding or trait calls
for it.

## Why they did it

The game's own numbers explain it:

- **Mood.** Dancing and the gaming mat are almost the only things an adult can
  do to satisfy the Playful mood. Only dancing and making bar drinks satisfy
  Dazed. Both moods pull hard (up to 20 a minute, against 0.58 for the Fun
  from dancing). So a Playful or Dazed Sim heads for the stereo.
- **Fun.** The mat promises 2.33 Fun a minute. Computers, consoles, tablets
  and TV promise 0.78.

## What it changes

- Dancing and the mat keep a quarter of their pull on the Playful and Dazed
  moods. Dancing still lifts those moods when it happens.
- The mat promises the same Fun as every other video game, at the rate the game
  gives the tablet.

Nothing a Sim actually gets from dancing or gaming changes. Only the promise
autonomy weighs.

- Tuning only, no script. Nothing runs during play.
- 15 interaction overrides: 7 dances (stereo, wall speaker, robot stereo,
  keyboard, bonfire, mannequin, metal headbang) and the mat's 4 games plus
  their gamed-out versions.

## Left alone, on purpose

- **Toddler dancing and teaching toddlers to dance.** It's how toddlers learn
  Movement.
- **Party, club, wedding and venue dancing** (dance floors, DJ booths, dance
  battles). Those pulls come from the event, not the Sim's mood.
- **House-guest and butler dancing**, which a situation tells those Sims to do.
- **The gamed-out mat's negative Fun.** It's EA's own "I'm sick of this" brake.
- **Dance With and Teach Me Rumba Sim**: LittleMsSam's
  AutonomousPickerDanceWatchTVPlayDollhouse and TeachMeRumbasim already override
  those, so they're left to her.
- Other gaming devices. They already advertise normal amounts.

## Build

```
py build.py
```

This reads the interactions from your installed game and writes
`GhostWorldTourist_LessDancingAndGaming.package`. It stops if a patch has
changed the numbers above, and it skips anything another installed mod already
overrides. `MOOD_SHARE` in `build.py` sets how much mood pull is kept.

Author: GhostWorldTourist
