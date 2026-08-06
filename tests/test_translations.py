"""Alle neun Sprachdateien müssen denselben Schlüsselsatz haben.

Fehlt ein Schlüssel in einer Sprache, zeigt die Oberfläche dort den
Schlüsselnamen an -- ein Fehler, den man nur sieht, wenn man die Anwendung
zufällig in genau dieser Sprache startet.
"""

import re

import pytest
import yaml

PLACEHOLDER = re.compile(r'%\{(\w+)\}')
LEAD_LOCALE = 'de'


def _catalogues(root):
    """Sprachkürzel -> Schlüssel/Text-Zuordnung.

    Eine Datei kann mehrere Blöcke enthalten: noScribe.zh-CN.yml führt neben
    `zh-CN` noch `zh` als Alias, damit python-i18n auch das kurze Kürzel
    findet. Maßgeblich ist der Block, der zum Dateinamen passt.
    """
    result = {}
    for path in sorted((root / 'trans').glob('noScribe.*.yml')):
        locale = path.name[len('noScribe.'):-len('.yml')]
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        assert locale in data, f'{path.name} enthält keinen Block "{locale}"'
        result[locale] = data[locale]
    return result


def test_there_are_nine_catalogues(root):
    assert len(_catalogues(root)) == 9


def test_every_locale_has_the_same_keys(root):
    catalogues = _catalogues(root)
    expected = set(catalogues[LEAD_LOCALE])
    for locale, entries in catalogues.items():
        missing = expected - set(entries)
        extra = set(entries) - expected
        assert not missing, f'{locale}: fehlende Schlüssel {sorted(missing)}'
        assert not extra, f'{locale}: unbekannte Schlüssel {sorted(extra)}'


def test_no_value_is_empty(root):
    for locale, entries in _catalogues(root).items():
        empty = [key for key, value in entries.items()
                 if value is None or str(value).strip() == '']
        assert not empty, f'{locale}: leere Texte {sorted(empty)}'


def test_placeholders_match_the_lead_language(root):
    """`%{dir}` in einer Sprache und `%{ordner}` in einer anderen wirft zur
    Laufzeit einen Fehler statt einen falschen Text."""
    catalogues = _catalogues(root)
    lead = catalogues[LEAD_LOCALE]
    for locale, entries in catalogues.items():
        if locale == LEAD_LOCALE:
            continue
        for key, value in entries.items():
            expected = set(PLACEHOLDER.findall(str(lead[key])))
            actual = set(PLACEHOLDER.findall(str(value)))
            assert expected == actual, (
                f'{locale}/{key}: Platzhalter {sorted(actual)} '
                f'statt {sorted(expected)}')
