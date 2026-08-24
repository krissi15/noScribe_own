"""Die Wiedergabe des Editors: Klicken soll springen, nicht anhalten.

Rueckmeldung zu v0.7.3, im Wortlaut: „das Konzept soll sein, dass man die
Zeilen sieht und dabei automatisch dann hin und her springen kann in der
Audio und sehen kann wie die audio gerade ist."

Der uebernommene Editor konnte das nicht, und zwar aus einem strukturellen
Grund: `play_along()` war eine **blockierende Schleife** mit
`processEvents()`. Solange sie lief, steckte der Slot fest; ein Klick ins
Transkript konnte deshalb nur eines bewirken -- `keep_playing = False`, also
anhalten. Springen war nicht etwa vergessen worden, es war unmoeglich.

Der Umbau auf einen Timer nimmt diese Fessel weg. Diese Tests halten fest,
dass sie nicht zurueckkehrt. Sie arbeiten auf dem Syntaxbaum, weil sich
`MainWindow` ohne Tonausgabe und Bildschirm nicht bauen laesst -- die Fehler,
um die es geht, sind aber ohnehin strukturell.
"""

import ast

import pytest


@pytest.fixture(scope='module')
def source(root):
    return (root / 'noScribeEdit' / 'noScribeEdit.py').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def tree(source):
    return ast.parse(source)


def method(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f'Methode {name} fehlt')


def calls_in(node):
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


def test_playback_no_longer_blocks_in_a_loop(tree):
    """Der eigentliche Umbau. Kehrt die Schleife zurueck, ist alles Weitere
    wieder wirkungslos."""
    play = method(tree, 'play_along')
    loops = [n for n in ast.walk(play) if isinstance(n, (ast.While, ast.For))]
    assert not loops, (
        'play_along() enthaelt wieder eine Schleife. Solange sie laeuft, '
        'kann ein Klick ins Transkript nichts anderes bewirken als das '
        'Anhalten der Wiedergabe.')
    assert 'processEvents' not in calls_in(play)


def test_a_timer_drives_the_playback(source, tree):
    assert 'self.playback_timer.timeout.connect(self._playback_tick)' in source
    assert 'self.playback_timer.start()' in calls_in(method(tree, 'play_along')) or \
           'self.playback_timer.start()' in source
    method(tree, '_playback_tick')


def test_clicking_seeks_instead_of_stopping(tree):
    """Der Kern der Rueckmeldung."""
    changed = method(tree, 'cursor_changed')
    assert '_seek_to_cursor' in calls_in(changed), (
        'cursor_changed() springt nicht mehr in die Aufnahme.')

    for node in ast.walk(changed):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Attribute)
                        and target.attr == 'keep_playing'):
                    raise AssertionError(
                        'cursor_changed() setzt wieder keep_playing -- damit '
                        'haelt jeder Klick die Wiedergabe an, statt zu springen.')


def test_typing_inside_the_current_line_does_not_jump(source):
    """Ohne diese Bedingung springt jeder Tastendruck beim Korrigieren an den
    Anfang der Zeile zurueck -- der Editor waere unbenutzbar."""
    seek = source[source.index('def _seek_to_cursor'):]
    seek = seek[:seek.index('\n    def ', 1)]
    assert "ts == self.playing_ts" in seek, (
        '_seek_to_cursor() prueft nicht mehr, ob der Cursor das Segment '
        'ueberhaupt gewechselt hat.')


def test_the_running_line_is_marked_not_selected(tree):
    """Eine Textauswahl waere beim ersten Tastendruck weg -- samt Absatz.

    Deshalb `ExtraSelection`: sie hebt hervor, ohne den Schreibcursor
    anzufassen.
    """
    mark = method(tree, '_mark_segment')
    used = calls_in(mark)
    assert 'ExtraSelection' in used
    assert 'setTextCursor' not in used, (
        '_mark_segment() bewegt den Schreibcursor. Waehrend der Wiedergabe '
        'kann dann niemand mehr tippen.')


def test_search_hits_and_the_running_line_coexist(tree, source):
    """Beide benutzen Qts `extraSelections`. Wer sie einzeln setzt, loescht
    die jeweils andere."""
    setters = [n for n in ast.walk(tree)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == 'setExtraSelections']
    assert len(setters) == 1, (
        'setExtraSelections wird an mehr als einer Stelle aufgerufen -- dann '
        'loescht die Suche die Zeilenmarkierung oder umgekehrt.')
    apply_fn = method(tree, '_apply_extra_selections')
    assert 'setExtraSelections' in calls_in(apply_fn)


def test_the_position_is_remembered_before_stop_resets_it(source):
    """`QMediaPlayer.stop()` setzt die Position auf 0. Wer sie danach liest,
    faengt beim naechsten Mal wieder vorne an."""
    stop = source[source.index('def _stop_playback'):]
    stop = stop[:stop.index('\n    def ', 1)]
    assert stop.index('self.resume_pos = self.media_player.position()') < \
           stop.index('self.media_player.stop()')


def test_the_playback_timer_is_stopped_with_the_playback(source):
    """Ein weiterlaufender Timer wuerde nach dem Anhalten weiter Segmente
    weiterschalten."""
    stop = source[source.index('def _stop_playback'):]
    stop = stop[:stop.index('\n    def ', 1)]
    assert 'self.playback_timer.stop()' in stop


def test_loading_another_transcript_clears_the_old_mark(tree):
    """Sonst steht die Markierung des vorigen Transkripts im neuen."""
    assert '_clear_segment_mark' in calls_in(method(tree, '_file_open'))
