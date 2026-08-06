"""Die Entscheidungen, die vor jeder Transkription getroffen werden.

Diese Tests halten vier konkrete Fehler fest, die vorher niemandem auffielen,
weil sie sich nur in Laufzeit und Nacharbeit äußerten, nie in einer
Fehlermeldung.
"""

import types

import pytest

from conftest import load_module


@pytest.fixture(scope='module')
def wa():
    return load_module('noScribe/whisper_args.py')


def make_job(**overrides):
    """Ein Auftrag mit genau den Feldern, die build_transcribe_options liest."""
    defaults = dict(whisper_model=types.SimpleNamespace(path='/models/precise'),
                    whisper_compute_type='default',
                    whisper_beam_size=1,
                    language_name='German',
                    disfluencies=False)
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def options(wa, job, **overrides):
    kwargs = dict(device='cpu', number_threads=8, language_code='de',
                  vad_threshold=0.5, vocabulary=[],
                  condition_on_previous_text=False, locale='de')
    kwargs.update(overrides)
    return wa.build_transcribe_options(job, **kwargs)


# -- Rechengenauigkeit ---------------------------------------------------

def test_cpu_gets_int8_instead_of_float32(wa):
    """'default' bedeutete auf der CPU float32 -- die langsamste Möglichkeit
    war die Voreinstellung."""
    for configured in ('default', 'auto', '', None):
        assert wa.resolve_compute_type(configured, 'cpu') == 'int8'


def test_gpu_gets_float16(wa):
    assert wa.resolve_compute_type('default', 'cuda') == 'float16'


def test_an_explicit_setting_wins(wa):
    """Der Ausweg für den Fall, dass int8 irgendwo Ärger macht."""
    assert wa.resolve_compute_type('float32', 'cpu') == 'float32'
    assert wa.resolve_compute_type('int8_float16', 'cuda') == 'int8_float16'


# -- Wiederholungsschleifen ----------------------------------------------

def test_condition_on_previous_text_is_carried_through(wa):
    assert options(wa, make_job())['condition_on_previous_text'] is False
    assert options(wa, make_job(), condition_on_previous_text=True)[
        'condition_on_previous_text'] is True


# -- beam_size -----------------------------------------------------------

def test_beam_size_comes_from_the_job(wa):
    """Vorher stand im Elternprozess fest 5, während die Konfiguration 1 sagte
    und das Protokoll auch 1 schrieb."""
    assert options(wa, make_job(whisper_beam_size=1))['beam_size'] == 1
    assert options(wa, make_job(whisper_beam_size=5))['beam_size'] == 5


def test_beam_size_is_an_int_even_if_yaml_made_it_a_string(wa):
    assert options(wa, make_job(whisper_beam_size='3'))['beam_size'] == 3


# -- Wortliste -----------------------------------------------------------

def test_prompt_keeps_the_style_example_first(wa):
    prompt = wa.build_prompt('Äh, das ist, ähm, nicht so einfach.',
                             ['Beschuldigter', 'Aktenzeichen'])
    assert prompt.startswith('Äh, das ist, ähm, nicht so einfach.')
    assert 'Beschuldigter' in prompt
    assert 'Aktenzeichen' in prompt


def test_prompt_drops_duplicates_regardless_of_case(wa):
    prompt = wa.build_prompt('', ['Zeuge', 'zeuge', 'ZEUGE', 'Gericht'])
    assert prompt.count('euge') == 1
    assert 'Gericht' in prompt


def test_prompt_is_truncated_at_term_boundaries(wa):
    """Whisper verwirft alles über 224 Token stillschweigend. Gekürzt wird
    deshalb hier -- und nie mitten in einem Wort, das würde das Modell in die
    falsche Richtung schieben."""
    terms = [f'Fachbegriff{i:04d}' for i in range(500)]
    prompt = wa.build_prompt('', terms)
    assert len(prompt) <= wa.MAX_PROMPT_CHARS
    # Kein angeschnittener Begriff am Ende.
    for term in prompt.split(', '):
        assert term in terms


def test_an_empty_vocabulary_leaves_the_style_example_alone(wa):
    assert wa.build_prompt('Ähm, ja.', []) == 'Ähm, ja.'


def test_everything_empty_gives_an_empty_prompt(wa):
    assert wa.build_prompt('', []) == ''


# -- Wortlistendatei -----------------------------------------------------

def test_vocabulary_file_skips_comments_and_blank_lines(wa, tmp_path):
    path = tmp_path / 'vocabulary.txt'
    path.write_text('# Kommentar\n\nBeschuldigter\n  Aktenzeichen  \n'
                    'Zeuge # nachgestellter Kommentar\n', encoding='utf-8')
    assert wa.load_vocabulary_file(path) == ['Beschuldigter', 'Aktenzeichen', 'Zeuge']


def test_a_missing_vocabulary_file_is_not_an_error(wa, tmp_path):
    """Die eigene Wortliste ist optional; sie fehlt beim ersten Start immer."""
    assert wa.load_vocabulary_file(tmp_path / 'gibtsnicht.txt') == []


def test_the_shipped_justiz_vocabulary_fits_in_the_prompt(wa, root):
    """Sonst wäre der hintere Teil der Liste wirkungslos, ohne dass es
    auffällt."""
    terms = wa.load_vocabulary_file(root / 'prompts' / 'vocab_justiz_de.txt')
    assert terms, 'Die mitgelieferte Wortliste ist leer.'
    prompt = wa.build_prompt('Äh, das ist, es ist, ähm, nicht so einfach.', terms)
    for term in terms:
        assert term in prompt, (
            f'"{term}" fällt aus dem Prompt heraus -- die mitgelieferte Liste '
            f'ist zu lang für {wa.MAX_PROMPT_CHARS} Zeichen.')
