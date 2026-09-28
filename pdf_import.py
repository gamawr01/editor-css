# -*- coding: utf-8 -*-
"""Extrai texto de PDF do cliente e gera HTML rascunho para modelo Ultralims."""

from __future__ import annotations

import html as html_mod
import re
from typing import Any

import pypdfium2 as pdfium

# Catálogo sugerido de variáveis (o nome final é o da Variável Relatório no Ultralims)
VARIABLE_CATALOG: list[dict[str, str]] = [
    {"id": "relatorio_numero", "label": "Nº do relatório", "token": "{{numero_relatorio}}", "hint": "Relatório de Ensaio Nº…"},
    {"id": "relatorio_titulo", "label": "Título do relatório", "token": "{{titulo_relatorio}}", "hint": "Cabeçalho principal"},
    {"id": "cliente_razao", "label": "Razão social do cliente", "token": "{{cliente_razao}}", "hint": "SOLICITANTE / Contratante"},
    {"id": "cliente_endereco", "label": "Endereço do cliente", "token": "{{cliente_endereco}}", "hint": "Endereço principal"},
    {"id": "cliente_contato", "label": "Contato do cliente", "token": "{{cliente_contato}}", "hint": "Nome do contato"},
    {"id": "cliente_email", "label": "E-mail do cliente", "token": "{{cliente_email}}", "hint": "E-mail de contato"},
    {"id": "cliente_fone", "label": "Telefone do cliente", "token": "{{cliente_fone}}", "hint": "Fone / celular"},
    {"id": "cliente_cnpj", "label": "CNPJ do cliente", "token": "{{cliente_cnpj}}", "hint": "CPF/CNPJ"},
    {"id": "proposta_numero", "label": "Nº da proposta", "token": "{{numero_proposta}}", "hint": "Proposta comercial"},
    {"id": "os_numero", "label": "Nº da OS / SS", "token": "{{numero_os}}", "hint": "Ordem de serviço"},
    {"id": "amostra_codigo", "label": "Código da amostra", "token": "{{codigo_amostra}}", "hint": "Amostra / material"},
    {"id": "amostra_descricao", "label": "Descrição da amostra", "token": "{{descricao_amostra}}", "hint": "Tipo / descrição"},
    {"id": "amostra_local", "label": "Local da coleta", "token": "{{local_coleta}}", "hint": "Ponto de coleta"},
    {"id": "data_amostragem", "label": "Data de amostragem", "token": "{{data_amostragem}}", "hint": "Data coleta"},
    {"id": "data_recebimento", "label": "Data de recebimento", "token": "{{data_recebimento}}", "hint": "Recebimento no lab"},
    {"id": "data_emissao", "label": "Data de emissão", "token": "{{data_emissao}}", "hint": "Emissão do laudo"},
    {"id": "data_analise", "label": "Data da análise", "token": "{{data_analise}}", "hint": "Execução do ensaio"},
    {"id": "resultado_ensaio", "label": "Resultado do ensaio", "token": "{{resultado_ensaio}}", "hint": "Valor medido"},
    {"id": "unidade_resultado", "label": "Unidade", "token": "{{unidade}}", "hint": "Unidade do resultado"},
    {"id": "limite_padrao", "label": "Limite / especificação", "token": "{{limite_padrao}}", "hint": "LIM / valor de referência"},
    {"id": "metodo", "label": "Método / norma", "token": "{{metodo}}", "hint": "ABNT, ISO, método interno"},
    {"id": "ensaio_nome", "label": "Nome do ensaio", "token": "{{ensaio}}", "hint": "Parâmetro analítico"},
    {"id": "lab_razao", "label": "Razão social do lab", "token": "{{lab_razao}}", "hint": "Cabeçalho do laboratório"},
    {"id": "lab_endereco", "label": "Endereço do lab", "token": "{{lab_endereco}}", "hint": "Rodapé / cabeçalho"},
    {"id": "lab_cnpj", "label": "CNPJ do lab", "token": "{{lab_cnpj}}", "hint": "Identificação do lab"},
    {"id": "lab_acreditacao", "label": "Acreditação / RBC", "token": "{{lab_acreditacao}}", "hint": "Código de acreditação"},
    {"id": "responsavel_nome", "label": "Responsável técnico", "token": "{{responsavel_tecnico}}", "hint": "Assinatura RT"},
    {"id": "observacao", "label": "Observação / nota", "token": "{{observacao}}", "hint": "Texto livre"},
]

# Padrões de texto que costumam ser valores dinâmicos no PDF do cliente
_DYNAMIC_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{2}/\d{2}/\d{2,4}\b", "data_emissao"),
    (r"\b\d{1,3}(\.\d{3})+/-\d{2}\b", "cliente_cnpj"),
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "cliente_email"),
    (r"\+?\d{2}\s*\d{4,5}[-\s]?\d{4}", "cliente_fone"),
    (r"\b[A-Za-z]:\s*/\s*/\s*.*", "observacao"),
    (r"\bN[º°oO]\s*[:\-]?\s*[\w./-]+", "relatorio_numero"),
    (r"\b\d{1,4}[./]\d{2,4}(?:[./]\w+)?\b", "os_numero"),
]


def _pt_to_px(pt: float) -> float:
    """Converte pontos PDF (1/72\") para px CSS (96 dpi)."""
    return pt * (96.0 / 72.0)


def _escape(text: str) -> str:
    return html_mod.escape(text, quote=True)


def _detect_suggestion(text: str) -> str | None:
    for pattern, var_id in _DYNAMIC_PATTERNS:
        if re.search(pattern, text):
            return var_id
    # rótulo + valor em memória ("Cliente: Foo")
    m = re.match(r"^\s*([^:]{2,40}):\s*(.+)$", text)
    if m and len(m.group(2).strip()) >= 3:
        label = m.group(1).strip().lower()
        if any(k in label for k in ("cliente", "solicit", "razão", "razao", "amostra", "data", "ensaio")):
            for v in VARIABLE_CATALOG:
                if v["id"] in label or any(
                    word in label for word in v["hint"].lower().split("/")[:1]
                ):
                    return v["id"]
    return None


def _extract_lines(page) -> list[dict[str, Any]]:
    """Agrupa caracteres da página em linhas (cima para baixo)."""
    textpage = page.get_textpage()
    n = textpage.count_chars()
    chars: list[dict[str, Any]] = []

    for i in range(n):
        ch = textpage.get_text_range(i, 1)
        if ch is None or ch == "":
            continue
        if ch in ("\r", "\n", "\x00"):
            continue
        box = textpage.get_charbox(i)
        # box: left, bottom, right, top (origem canto inferior esquerdo)
        left, bottom, right, top = box
        chars.append(
            {
                "ch": ch,
                "left": left,
                "right": right,
                "bottom": bottom,
                "top": top,
                "y": bottom,
                "x": left,
                "w": max(right - left, 0),
                "h": max(top - bottom, 0),
            }
        )

    if not chars:
        return []

    # ordena por y decrescente (topo da página primeiro; PDF y sobe)
    chars.sort(key=lambda c: (-c["top"], c["left"]))

    lines: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_top: float | None = None
    tol = 3.0  # pt de tolerância vertical para a mesma linha

    for c in chars:
        if current_top is None or abs(c["top"] - current_top) <= tol:
            if current_top is None:
                current_top = c["top"]
            current.append(c)
        else:
            if current:
                lines.append(current)
            current = [c]
            current_top = c["top"]
    if current:
        lines.append(current)

    out: list[dict[str, Any]] = []
    for line_chars in lines:
        line_chars.sort(key=lambda c: c["left"])
        text_parts: list[str] = []
        prev: dict[str, Any] | None = None
        for c in line_chars:
            if prev is not None:
                gap = c["left"] - prev["right"]
                # espaço amplo → espaço em branco
                if gap > max(2.5, prev["h"] * 0.35):
                    text_parts.append(" ")
            text_parts.append(c["ch"])
            prev = c
        text = "".join(text_parts)
        text = re.sub(r"[ \t]+", " ", text).strip()
        if not text:
            continue
        left = min(c["left"] for c in line_chars)
        right = max(c["right"] for c in line_chars)
        top = max(c["top"] for c in line_chars)
        bottom = min(c["bottom"] for c in line_chars)
        height = max(top - bottom, 8.0)
        out.append(
            {
                "text": text,
                "left": left,
                "right": right,
                "top": top,
                "bottom": bottom,
                "height": height,
                "font_pt": round(height * 0.85, 1),
                "suggestion": _detect_suggestion(text),
            }
        )
    # ordem de leitura: top desc
    out.sort(key=lambda r: (-r["top"], r["left"]))
    return out


def _default_token(var_id: str) -> str:
    for v in VARIABLE_CATALOG:
        if v["id"] == var_id:
            return v["token"]
    return "{{%s}}" % var_id


def _apply_suggestions(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Substitui valores dinâmicos por tokens {{...}}; preserva rótulos estáticos."""
    result = []
    for line in lines:
        text = line["text"]
        sug = line.get("suggestion")
        token = _default_token(sug) if sug else None
        # se a linha só é o valor, troca tudo; se tem "Rótulo: valor", só o valor
        if token and ":" in text and not text.strip().endswith(":"):
            label, _, value = text.partition(":")
            if value.strip() and len(value.strip()) >= 2:
                new_text = f"{label}: {token}"
            else:
                new_text = token
        elif token and re.fullmatch(r"[\w\s./:@+-]{3,}", text or ""):
            # linha parece só um valor
            new_text = token
        else:
            new_text = text
        row = dict(line)
        row["text_original"] = text
        row["text"] = new_text
        row["mapped"] = bool(token)
        result.append(row)
    return result


def _is_heading(line: dict[str, Any]) -> bool:
    t = line["text"].strip()
    if not t:
        return False
    if len(t) > 80:
        return False
    if t.isupper() or (t[:1].isupper() and t.endswith(":")):
        return True
    if line["font_pt"] and line["font_pt"] >= 12:
        return True
    if re.match(r"^\d{1,2}[.)]\s", t):
        return True
    return False


def _looks_like_table_row(lines: list[dict[str, Any]], idx: int) -> bool:
    """Detecta rótulo: valor + valor na mesma faixa horizontal."""
    if idx + 1 >= len(lines):
        return False
    a, b = lines[idx], lines[idx + 1]
    # mesma linha (topo próximo) mas colunas diferentes
    if abs(a["top"] - b["top"]) < 6 and a["right"] < b["left"] - 4:
        return True
    if ":" in a["text"] and len(a["text"]) < 60:
        return True
    return False


def lines_to_flow_html(lines: list[dict[str, Any]], page_width_pt: float) -> str:
    """Gera HTML em fluxo (tables/sections) — estilo Ultralims."""
    if not lines:
        return "<!-- PDF sem texto extraível (pode ser imagem escaneada) -->\n<p>(sem texto)</p>"

    parts: list[str] = []
    parts.append(
        f'<div class="modelo-importado" style="width:{_pt_to_px(page_width_pt):.0f}px;'
        " margin:0 auto; font-family:Arial,Helvetica,sans-serif; font-size:11px; color:#000;"
        ' background:#fff;">'
    )
    parts.append("<!-- Rascunho gerado a partir do PDF do cliente. Ajuste no editor. -->")

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        text = line["text"]
        # agrupa linhas muito próximas em bloco de tabela quando há rótulo e valor
        if _is_heading(line) and not (":" in text and len(text) < 40):
            parts.append(
                f'<div class="secao-titulo" style="font-weight:bold; margin:10px 0 4px;'
                f' border-bottom:1px solid #000; padding-bottom:2px;">{_escape(text)}</div>'
            )
            i += 1
            continue

        # coleta "colunas" na mesma faixa (row de tabela)
        row_group = [line]
        j = i + 1
        while j < n and abs(lines[j]["top"] - line["top"]) < 6 and lines[j]["left"] > line["right"]:
            row_group.append(lines[j])
            j += 1

        if len(row_group) >= 2 and any(":" in r["text"] for r in row_group):
            cells = "".join(
                f'<td class="{"nomeCampoRelatDir" if ":" in r["text"] else "valorCampoRelatEsq"}'
                f'" style="vertical-align:top; padding:2px 4px; border:1px solid #ccc;">'
                f"{_escape(r['text'])}</td>"
                for r in row_group
            )
            parts.append(
                f'<table class="relatorio" style="border-collapse:collapse; width:100%;'
                f' margin:2px 0; font-size:11px;"><tbody><tr>{cells}</tr></tbody></table>'
            )
            i = j
            continue

        # parágrafo simples
        if ":" in text and len(text.split(":")[0]) < 40:
            label, _, value = text.partition(":")
            parts.append(
                '<table class="relatorio" style="border-collapse:collapse; width:100%;'
                ' margin:2px 0; font-size:11px;"><tbody><tr>'
                f'<td class="nomeCampoRelatDir" style="width:28%; padding:2px 4px; border:1px solid #ccc; font-weight:bold;">'
                f"{_escape(label.strip())}:</td>"
                f'<td class="valorCampoRelatEsq" style="padding:2px 4px; border:1px solid #ccc;">'
                f"{_escape(value.strip())}</td></tr></tbody></table>"
            )
        else:
            style = ""
            if line.get("suggestion") and "{{" in text:
                style = ' data-variavel="1" style="background:#fff3cd;"'
            parts.append(f"<p{style} style=\"margin:3px 0;{_style_for(line)}\">{_escape(text)}</p>")
        i += 1

    parts.append("</div>")
    return "\n".join(parts)


def _style_for(line: dict[str, Any]) -> str:
    size = line.get("font_pt") or 11
    return f" font-size:{max(9, min(size + 2, 18)):.0f}px;"


def lines_to_layout_html(lines: list[dict[str, Any]], page_w: float, page_h: float) -> str:
    """HTML com posicionamento absoluto — fidelidade visual ao PDF."""
    w = _pt_to_px(page_w)
    h = _pt_to_px(page_h)
    # PDF origem inferior-esquerda → CSS top
    parts = [
        f'<div class="pdf-page" style="position:relative; width:{w:.0f}px; height:{h:.0f}px;'
        ' background:#fff; overflow:hidden; font-family:Arial,Helvetica,sans-serif; color:#000;">'
    ]
    for idx, line in enumerate(lines):
        # top do CSS = page_h - line.top  (em pt), depois * 96/72
        top_pt = page_h - line["top"]
        left_pt = line["left"]
        size = max(8, (line.get("font_pt") or 10))
        top_px = _pt_to_px(top_pt)
        left_px = _pt_to_px(left_pt)
        bold = " font-weight:bold;" if _is_heading(line) else ""
        bg = " background:#fff3cd;" if line.get("mapped") else ""
        token = _escape(line["text"])
        parts.append(
            f'<div class="linha-pdf" data-i="{idx}" style="position:absolute;'
            f" left:{left_px:.1f}px; top:{top_px:.1f}px;"
            f" font-size:{size:.1f}px; white-space:nowrap; line-height:1.15;{bold}{bg}\">"
            f"{token}</div>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def extract_pdf_to_html(pdf_bytes: bytes, mode: str = "fluxo") -> dict[str, Any]:
    """
    mode:
      - fluxo: HTML em blocos/tabelas (recomendado para Ultralims)
      - layout: posicionamento absoluto igual ao PDF
    """
    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        pages_meta = []
        all_lines: list[dict[str, Any]] = []
        page_html_parts: list[str] = []

        for pi in range(len(doc)):
            page = doc[pi]
            pw, ph = page.get_size()
            lines = _extract_lines(page)
            lines = _apply_suggestions(lines)
            for ln in lines:
                ln["page"] = pi + 1
            all_lines.extend(lines)
            pages_meta.append({"page": pi + 1, "width_pt": pw, "height_pt": ph, "lines": len(lines)})

            if mode == "layout":
                page_html_parts.append(
                    f"<!-- página {pi + 1} -->\n" + lines_to_layout_html(lines, pw, ph)
                )
            else:
                page_html_parts.append(
                    f'<!-- página {pi + 1} -->\n<div class="pagina-{pi + 1}" '
                    f'style="page-break-after:always; min-height:10px;">\n'
                    + lines_to_flow_html(lines, pw)
                    + "\n</div>"
                )

        if mode == "layout":
            css = (
                "body{margin:0;background:#e8e8e8;}\n"
                ".pdf-page{margin:12px auto; box-shadow:0 4px 16px rgba(0,0,0,.18);}\n"
                ".linha-pdf:hover{outline:1px solid #0b3d91; cursor:text;}\n"
                "[data-variavel],.linha-pdf[data-mapped]{background:#fff3cd;}\n"
            )
        else:
            css = (
                "body{margin:0;background:#fff; font-family:Arial,Helvetica,sans-serif;}\n"
                ".modelo-importado{padding:8px;}\n"
                ".secao-titulo{background:#f0f4fa;}\n"
                "table.relatorio td{font-size:11px;}\n"
                "p[data-variavel]{background:#fff3cd; display:inline-block; padding:1px 3px;}\n"
                "@media print{ body{background:#fff;} }\n"
            )

        mapped = [l for l in all_lines if l.get("mapped")]
        suggestions = []
        for l in mapped:
            if l.get("suggestion"):
                suggestions.append(
                    {
                        "page": l.get("page"),
                        "original": l.get("text_original", l["text"]),
                        "variable_id": l["suggestion"],
                        "token": _default_token(l["suggestion"]),
                    }
                )

        return {
            "html": "\n".join(page_html_parts),
            "css": css,
            "mode": mode,
            "pages": pages_meta,
            "line_count": len(all_lines),
            "suggestions": suggestions[:80],
            "variables": VARIABLE_CATALOG,
            "text_only": "\n".join(l["text_original"] for l in all_lines if l.get("text_original") or l.get("text")),
            "has_text": len(all_lines) > 0,
        }
    finally:
        doc.close()


def map_tokens_in_html(html: str, replacements: list[dict[str, str]]) -> str:
    """Aplica pares {find, replace} no HTML (substituição literal segura)."""
    out = html
    for item in replacements:
        find = item.get("find") or ""
        repl = item.get("replace") or ""
        if find and find in out:
            out = out.replace(find, repl)
    return out
