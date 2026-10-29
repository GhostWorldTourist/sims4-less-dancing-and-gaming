"""Less Dancing and Gaming - build script.

Sims dance far too often, and they won't leave the Motion Gaming Mat alone.
This turns down the two things that pull them there on their own. They still
dance and game, enjoy it exactly as much, and do it whenever a party, club or
trait calls for it.

Why they do it
--------------
Full autonomy scores every interaction by what it advertises. A periodic stat
change advertises `value / interval`, where `interval` is 1 for a stat change
and the interaction's `time_overhead` (default 10) for everything else
(`StatisticOperation.get_fulfillment_rate`). Two things stand out:

- Mood. The stereo dances and the gaming mat `statistic_set_max` the Playful
  and Dazed emotion-autonomy commodities (range -100..100), which advertises up
  to 200 / 10 = 20 a minute. Fun from dancing is 0.58. Almost nothing else an
  adult can do advertises Playful, and only dancing and bar drinks advertise
  Dazed, so a Playful or Dazed Sim goes to the stereo.
- Fun. The mat advertises 2.33 Fun a minute. Computers, consoles, tablets and
  TV all advertise 0.78.

What this changes
-----------------
For each interaction in scope, every advertising Playful/Dazed set-max stops
advertising (`advertise` False, so it still fills the mood when danced) and is
replaced by a false advertisement worth MOOD_SHARE of its old pull at full
urge. On the mat, Fun is advertised at the rate EA gives every other video
game, read from the tablet so it follows any patch.

Party, club, wedding and trait pulls come through static commodities and other
stats, and are untouched. So is the real gain from every operation.

Scope, found at build time so new packs are picked up on rebuild:
- dancing: interactions named *danc* / *headbang* that advertise Playful or Dazed
- gaming:  motionBasedGaming_play_* (the four games and their gamed-out forms)
Left out on purpose: toddlers (dancing is how they learn Movement), the
house-guest and butler versions (a situation tells those Sims to dance), and
any interaction another installed mod already overrides.

Author: GhostWorldTourist
"""
import copy, glob, os, re, struct, sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.environ['LOCALAPPDATA'], 'sulskill', 'ts4-knowledge', 'lib'))
sys.path.insert(0, os.path.join(os.path.expanduser('~'), 'repos', 'sulskill', 'sulskill-modbuild', 'scripts'))
import mergedtuning, dbpf

GAME = r'C:\Games\The Sims 4'
MODS = os.path.join(os.path.expanduser('~'), 'Documents', 'Electronic Arts', 'The Sims 4', 'Mods')
T_INTERACTION = 0xE882D22F
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'GhostWorldTourist_LessDancingAndGaming.package')

MOOD_SHARE = 0.25          # how much of the old mood pull is left
FUN = '16655'              # motive_Fun
PLAYFUL, DAZED = '16468', '16470'
MOOD_RANGE = 200.0         # both commodities run -100..100; checked below
MAT_FUN = '2.33'           # what EA gives the mat; checked below
TABLET_PLAY = 14359        # tablet_Play_Adventure: the reference video-game Fun rate
DEFAULT_OVERHEAD = 10.0    # Interaction.time_overhead default

DANCE = re.compile(r'danc|headbang', re.I)
MAT = re.compile(r'^motionBasedGaming_play_', re.I)
LEAVE = re.compile(r'toddler|TemporaryStay|butler', re.I)


def sources():
    # DeltaBuild outranks FullBuild, so the delta is read first.
    deltas = [os.path.join(GAME, r'Data\Simulation\SimulationDeltaBuild0.package')]
    deltas += sorted(glob.glob(os.path.join(GAME, r'Delta\*\SimulationDeltaBuild0.package')))
    fulls = [os.path.join(GAME, r'Data\Simulation\SimulationFullBuild0.package')]
    for kind in ('EP', 'GP', 'SP'):
        fulls += sorted(glob.glob(os.path.join(GAME, kind + r'*\SimulationFullBuild0.package')))
    return deltas + fulls


def ea(want):
    """{instance id: expanded element} for ids or names `want` accepts."""
    found = {}
    for pkg in sources():
        for _, _, ct in mergedtuning.iter_resources(pkg):
            for inst in ct.instances():
                if inst.res_type not in ('interaction', 'statistic'):
                    continue
                iid = int(inst.attrs['s'])
                if iid not in found and want(iid, inst.attrs.get('n', ''), inst.res_type):
                    found[iid] = ct.expand(inst)
    return found


def stat_of(op):
    s = op.find("U/T[@n='stat']")
    return s.text if s is not None else None


def periodic_ops(si):
    ops = si.find(".//V[@n='periodic_stat_change']/U/L[@n='operations']")
    return list(ops) if ops is not None else []


def mood_ops(si):
    """Advertising set-max ops on Playful/Dazed, from the periodic change and the false ads."""
    out = []
    for parent in (si.find(".//V[@n='periodic_stat_change']/U/L[@n='operations']"),
                   si.find("L[@n='_false_advertisements']")):
        if parent is None:
            continue
        for op in parent:
            if op.get('t') == 'statistic_set_max' and stat_of(op) in (PLAYFUL, DAZED):
                adv = op.find("U/T[@n='advertise']")
                if adv is None or adv.text != 'False':
                    out.append((parent, op))
    return out


def false_ad(stat, amount, tests):
    v = ET.Element('V', t='statistic_change')
    u = ET.SubElement(v, 'U', n='statistic_change')
    ET.SubElement(u, 'T', n='amount').text = ('%.4f' % amount).rstrip('0').rstrip('.')
    ET.SubElement(u, 'T', n='stat').text = stat
    if tests is not None:
        u.append(copy.deepcopy(tests))
    return v


def false_ads(si):
    fa = si.find("L[@n='_false_advertisements']")
    if fa is None:
        fa = ET.SubElement(si, 'L', n='_false_advertisements')
    return fa


def silence(op):
    u = op.find('U')
    adv = u.find("T[@n='advertise']")
    if adv is None:
        adv = ET.SubElement(u, 'T', n='advertise')
    adv.text = 'False'
    u[:] = sorted(u, key=lambda e: e.get('n', ''))


def fun_rate(si):
    for op in periodic_ops(si):
        if op.get('t') == 'statistic_change' and stat_of(op) == FUN:
            adv = op.find("U/T[@n='advertise']")
            if adv is None or adv.text != 'False':
                return op, op.find("U/T[@n='amount']").text
    return None, None


def overridden_elsewhere(ids):
    """Interaction ids that another installed package already overrides."""
    taken = {}
    for path in glob.glob(os.path.join(MODS, '**', '*.package'), recursive=True):
        if os.path.basename(path) == os.path.basename(OUT):
            continue
        try:
            with open(path, 'rb') as f:
                head = f.read(96)
                if head[:4] != b'DBPF':
                    continue
                count, = struct.unpack_from('<I', head, 0x24)
                isize, = struct.unpack_from('<I', head, 0x2C)
                ioff = struct.unpack_from('<Q', head, 0x40)[0] or struct.unpack_from('<I', head, 0x28)[0]
                f.seek(ioff); ix = f.read(isize)
        except OSError:
            continue
        flags, = struct.unpack_from('<I', ix, 0); p = 4; const = {}
        for bit, key in ((0, 't'), (1, 'g'), (2, 'h')):
            if flags & (1 << bit):
                const[key], = struct.unpack_from('<I', ix, p); p += 4
        for _ in range(count):
            vals = {}
            for key in ('t', 'g', 'h'):
                if key in const:
                    vals[key] = const[key]
                else:
                    vals[key], = struct.unpack_from('<I', ix, p); p += 4
            lo, = struct.unpack_from('<I', ix, p); p += 4
            p += 8
            fsz, = struct.unpack_from('<I', ix, p - 4)
            p += 4
            if fsz & 0x80000000:
                p += 4
            iid = (vals['h'] << 32) | lo
            if vals['t'] == T_INTERACTION and iid in ids:
                taken.setdefault(iid, os.path.relpath(path, MODS))
    return taken


def main():
    found = ea(lambda iid, n, kind: (kind == 'statistic' and str(iid) in (PLAYFUL, DAZED)) or
               (kind == 'interaction' and (iid == TABLET_PLAY or DANCE.search(n) or MAT.match(n))))

    # Stop loudly if a patch moved anything this mod's numbers rest on.
    for sid in (PLAYFUL, DAZED):
        c = found[int(sid)]
        lo, hi = c.find("T[@n='min_value_tuning']").text, c.find("T[@n='max_value_tuning']").text
        if float(hi) - float(lo) != MOOD_RANGE:
            raise SystemExit('%s now runs %s..%s, not a range of %g - review MOOD_RANGE'
                             % (c.get('n'), lo, hi, MOOD_RANGE))
    _, game_fun = fun_rate(found[TABLET_PLAY])
    if game_fun is None:
        raise SystemExit('tablet_Play_Adventure no longer advertises Fun - pick a new reference')

    chosen = {}
    for iid, si in found.items():
        n = si.get('n', '')
        if si.find("T[@n='allow_autonomous']") is not None and si.find("T[@n='allow_autonomous']").text == 'False':
            continue
        if LEAVE.search(n):
            continue
        if MAT.match(n) or (DANCE.search(n) and mood_ops(si)):
            chosen[iid] = si
    taken = overridden_elsewhere(set(chosen))

    resources, report = [], []
    for iid, si in sorted(chosen.items(), key=lambda kv: kv[1].get('n').lower()):
        n = si.get('n')
        if iid in taken:
            report.append('  left to %s: %s' % (taken[iid], n))
            continue
        node = si.find("T[@n='time_overhead']")
        overhead = float(node.text) if node is not None else DEFAULT_OVERHEAD
        notes = []
        for parent, op in mood_ops(si):
            share = MOOD_SHARE * MOOD_RANGE / overhead
            tests = op.find("U/L[@n='tests']")
            if parent.get('n') == '_false_advertisements':
                parent.remove(op)          # already a false ad: replace it outright
            else:
                silence(op)
            false_ads(si).append(false_ad(stat_of(op), share, tests))
            notes.append('%s %.0f->%g' % ('Playful' if stat_of(op) == PLAYFUL else 'Dazed',
                                         MOOD_RANGE / overhead, share))
        if MAT.match(n):
            op, rate = fun_rate(si)
            # Gamed-out games advertise negative Fun: EA's own deterrent, kept.
            if op is not None and float(rate) > 0:
                if rate != MAT_FUN:
                    raise SystemExit('%s now advertises %s Fun, not %s - review before rebuilding'
                                     % (n, rate, MAT_FUN))
                silence(op)
                false_ads(si).append(false_ad(FUN, float(game_fun), None))
                notes.append('Fun %s->%s' % (rate, game_fun))
        if not notes:
            continue
        si[:] = sorted(si, key=lambda e: e.get('n', ''))
        xml = b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(si, encoding='utf-8')
        resources.append((T_INTERACTION, 0, iid, xml))
        report.append('  %-44s %s' % (n, ', '.join(notes)))

    print('\n'.join(report))
    if not resources:
        raise SystemExit('nothing to write - the scope matched nothing')
    count, size = dbpf.write(OUT, resources)
    print('\nwrote %s\n  %d resources, %d bytes' % (OUT, count, size))
    return 0


if __name__ == '__main__':
    sys.exit(main())
