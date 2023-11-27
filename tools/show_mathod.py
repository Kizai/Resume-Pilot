import re
from latex2mathml.converter import convert as tex2mathml

incomplete = '<font style="color:orange;" class="tooltip">&#9888;<span class="tooltiptext">formula incomplete</span></font>'
convError = '<font style="color:red" class="tooltip">&#9888;<span class="tooltiptext">LaTeX-convert-error</span></font>'


def handle_block_formula(formula):
    """
    Handle block formula conversion from LaTeX to MathML.
    :param formula: The string containing the formula.
    :return: A string with an HTML div element containing the converted formula or an error message.
    """
    mathml = convError
    try:
        mathml = tex2mathml(formula)
    except:
        pass
    return f'<div class="blockformula">{mathml}</div>\n'


def handle_inline_formula(paragraph, formula, remaining):
    """
    Handle inline formula conversion from LaTeX to MathML.
    :param paragraph: The string containing the text before the formula.
    :param formula: The string containing the formula.
    :param remaining: The string containing the text after the formula.
    :return: A string with the converted formula.
    """
    mathml = convError
    try:
        mathml = tex2mathml(formula)
    except:
        pass
    if paragraph.endswith('\n\n') or paragraph == '':
        paragraph += '&#x200b;'
    return convert(f"{paragraph}{mathml}{remaining}", splitParagraphs=False)


def split_and_convert(mdtex, delimiter, splitParagraphs):
    """
    Split Markdown-LaTeX text by the given delimiter, then convert the first formula found.
    :param mdtex: The Markdown-LaTeX text.
    :param delimiter: The delimiter regex pattern to split the text by.
    :param splitParagraphs: Boolean determining if the recursive calls should continue to split paragraphs.
    :return: A string with the converted LaTeX formula if it's found, or None if not found.
    """
    parts = re.split(delimiter, mdtex, 1)
    if len(parts) > 1:
        return handle_inline_formula(parts[0], parts[1], '' if len(parts) < 3 else parts[2])
    return None


def convert(mdtex, splitParagraphs=True):
    """
    Convert the Markdown-LaTeX mixture to HTML with MathML.
    :param mdtex: The Markdown-LaTeX text.
    :param splitParagraphs: Boolean determining if the function should split paragraphs separately (default: True).
    :return: A string containing the converted HTML content with MathML formulas.
    """
    if splitParagraphs:
        parts = re.split("\n\n", mdtex)
        return ''.join(convert(part, splitParagraphs=False) for part in parts)

    for delimiter_handler in [
        (r'\${2}', handle_block_formula),
        (r'\${1}', handle_inline_formula),
        (r'\\\[', handle_block_formula),
        (r'\\\(', handle_inline_formula)
    ]:
        delimiter, handler = delimiter_handler
        result = split_and_convert(mdtex, delimiter, splitParagraphs)
        if result:
            return result

    return mdtex
