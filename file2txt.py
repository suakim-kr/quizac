import fitz  # PyMuPDF
import pandas as pd
import re
import io
# from pykospacing import Spacing

# spacing = Spacing()


def extract_text_from_pdf(file) -> list:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    page_texts = []
    for page in doc:
        text = page.get_text() or ""
        page_texts.append(text.strip())
    return page_texts


def is_header_line(line: str) -> bool:
    return any(x in line for x in [
        '숙명여대 창병모', '©창병모', '© 창병모', '©숙대창병모'
    ]) or re.match(r'^\d+$', line.strip())


def is_junk_line(line: str) -> bool:
    return len(line.strip()) <= 1 or re.match(r'^[~\u00b7\u2022\u25a0]*$', line.strip())


def is_title_slide(lines: list) -> bool:
    return len(lines) <= 2 and sum(len(l.strip()) for l in lines) <= 20


def is_code_line(line: str) -> bool:
    return bool(re.search(r'[{}=\[\];<>]|^\s*(def |class |try:|except|raise|let )|>>>', line))


def preprocess_page_text(text: str) -> str:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_lines = []

    for line in lines:
        line = re.sub(r'[\uf06c\uf0a7\u2022\u25aa\u25cf\u25a0]', '', line)

        if is_header_line(line) or is_junk_line(line):
            continue

        if re.search(r'[가-힣]', line) and not is_code_line(line):
            # line = spacing(line)
            line = re.sub(r'\b([a-zA-Z]{1,2})\s+([a-zA-Z]{2,})\b', r'\1\2', line)

        cleaned_lines.append(line)

    if is_title_slide(cleaned_lines):
        return ''

    return '\n'.join(cleaned_lines).strip()


def pdf_file_to_dataframe(file) -> pd.DataFrame:
    pages = extract_text_from_pdf(file)
    df = pd.DataFrame({
        'page_num': range(1, len(pages) + 1),
        'text': pages
    })
    df['cleaned_text'] = df['text'].apply(preprocess_page_text)
    return df.drop(columns=['text'])
