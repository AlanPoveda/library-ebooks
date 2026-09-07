"""Testes da história #29: relatório de verificação gramatical por
capítulo do EPUB, agregado no estilo de saída de um linter.
"""

from library_ebooks.lint import (
    ChapterLintReport,
    GrammarIssue,
    format_lint_report,
    lint_epub,
)


def test_lint_epub_returns_one_report_per_chapter_with_issues(
    monkeypatch, build_multi_chapter_epub
):
    def _fake_check_text(text, lang):
        if "erro" in text:
            return [GrammarIssue(0, 4, "Erro encontrado", "R1", ["correto"], "misspelling")]
        return []

    monkeypatch.setattr("library_ebooks.lint.check_text", _fake_check_text)

    epub_path = build_multi_chapter_epub(
        [
            ("chap1.xhtml", "<html><body><p>Texto com erro aqui.</p></body></html>"),
            ("chap2.xhtml", "<html><body><p>Texto perfeito.</p></body></html>"),
        ]
    )

    reports = lint_epub(epub_path, lang="pt")

    assert len(reports) == 1
    assert reports[0].file_name == "chap1.xhtml"
    assert reports[0].issues[0].message == "Erro encontrado"


def test_lint_epub_skips_nav_document(monkeypatch, build_multi_chapter_epub):
    calls = []

    def _fake_check_text(text, lang):
        calls.append(text)
        return []

    monkeypatch.setattr("library_ebooks.lint.check_text", _fake_check_text)

    epub_path = build_multi_chapter_epub(
        [("chap1.xhtml", "<html><body><p>Texto.</p></body></html>")]
    )

    lint_epub(epub_path, lang="pt")

    # "Livro de teste" só aparece no título do nav.xhtml, não no capítulo
    assert all("Livro de teste" not in text for text in calls)


def test_lint_epub_does_not_modify_the_epub_file(monkeypatch, build_multi_chapter_epub):
    monkeypatch.setattr("library_ebooks.lint.check_text", lambda text, lang: [])
    epub_path = build_multi_chapter_epub(
        [("chap1.xhtml", "<html><body><p>Texto.</p></body></html>")]
    )
    original_bytes = epub_path.read_bytes()

    lint_epub(epub_path, lang="pt")

    assert epub_path.read_bytes() == original_bytes


def test_lint_epub_returns_empty_list_when_no_issues_anywhere(
    monkeypatch, build_multi_chapter_epub
):
    monkeypatch.setattr("library_ebooks.lint.check_text", lambda text, lang: [])
    epub_path = build_multi_chapter_epub(
        [("chap1.xhtml", "<html><body><p>Tudo certo.</p></body></html>")]
    )

    assert lint_epub(epub_path, lang="pt") == []


def test_format_lint_report_renders_linter_style_output():
    reports = [
        ChapterLintReport(
            "chap1.xhtml",
            [
                GrammarIssue(
                    31, 12, "Erro de ortografia", "PT_SPELLING", ["concordância"], "misspelling"
                )
            ],
        )
    ]

    output = format_lint_report(reports)

    assert output == "chap1.xhtml:31: [PT_SPELLING] Erro de ortografia (sugestão: concordância)"


def test_format_lint_report_handles_multiple_chapters_and_issues():
    reports = [
        ChapterLintReport("chap1.xhtml", [GrammarIssue(0, 1, "m1", "R1", ["a"], "misspelling")]),
        ChapterLintReport("chap2.xhtml", [GrammarIssue(5, 1, "m2", "R2", [], "style")]),
    ]

    output = format_lint_report(reports)

    assert output == ("chap1.xhtml:0: [R1] m1 (sugestão: a)\n" "chap2.xhtml:5: [R2] m2")


def test_format_lint_report_empty_when_no_issues():
    assert format_lint_report([]) == ""
