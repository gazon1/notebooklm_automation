import markdown
import pdfkit


def md_to_pdf_pdfkit(md_file, pdf_file):
    # Конвертируем MD в HTML
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content)

    # Добавляем базовый CSS для улучшения внешнего вида
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
            h1, h2, h3 {{ color: #333; }}
            code {{ background: #f4f4f4; padding: 2px 5px; }}
            pre {{ background: #f4f4f4; padding: 10px; overflow: auto; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Конвертируем HTML в PDF
    pdfkit.from_string(styled_html, pdf_file)

    print(f"Конвертировано: {md_file} -> {pdf_file}")


# Использование
md_to_pdf_pdfkit("input.md", "output.pdf")
