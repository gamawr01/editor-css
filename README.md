# Modelos de Relatório Ultralims

Aplicação local para montar **Relatório Padrão** do Ultra LIMS a partir de um **PDF base do cliente** (PDF → HTML → variáveis → export).

## Funcionalidades

- **Importar PDF do cliente** e gerar rascunho HTML (modo fluxo em tabelas ou layout fiel)
- Editor de **HTML e CSS** com preview ao lado
- **Catálogo de variáveis** e sugestões automáticas (data, CNPJ, e-mail, nº de relatório…)
- Exportar **HTML final** embutindo o CSS (para colar no Codex Ultralims)
- Templates salvos, geração de PDF de conferência (wkhtmltopdf)
- Assistente com IA orientado a modelos de relatório Ultra LIMS

## Fluxo típico

1. **Importar PDF** do cliente (ou carregar HTML/CSS existente)
2. Ajustar estrutura no editor HTML/CSS
3. Abrir **Variáveis** → mapear trechos dinâmicos para `{{tokens}}`
4. Conferir no preview / Gerar PDF
5. **Exportar HTML Ultralims** e colar em *Gerais → Relatórios e Variáveis → Relatório Padrão*

> Os `{{tokens}}` são sugestões: confirme o nome exato da **Variável Relatório** no sistema.

## Requisitos

- Python 3.10+
- Dependências listadas em requirements.txt
- wkhtmltopdf instalado no PATH ou disponível junto ao executável

## Instalação

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

```bash
python app.py
```

A aplicação ficará disponível em http://127.0.0.1:5000.

## Variáveis de ambiente

Crie um arquivo `.env` para habilitar o assistente de IA. Todos os provedores suportados usam o protocolo da OpenAI, então trocar de provedor é só mudar `LLM_PROVIDER`:

```env
LLM_PROVIDER=groq         # groq | nvidia | gemini | cerebras | ollama
LLM_API_KEY=sua_chave
# LLM_MODEL=openai/gpt-oss-120b   # opcional, sobrepõe o padrão do provedor
# LLM_BASE_URL=                       # opcional, sobrepõe a URL base
```

Onde obter a chave: Groq em https://console.groq.com/keys, NVIDIA NIM em https://build.nvidia.com, Gemini em https://aistudio.google.com/apikey, Cerebras em https://cloud.cerebras.ai. O Ollama roda local e não precisa de chave.

## Estrutura principal

- app.py: aplicação Flask
- pdf_import.py: extração de PDF do cliente → HTML + sugestão de variáveis
- templates/index.html: interface principal
- AI_CONTEXT.md: system prompt do assistente
- saved_templates/: templates salvos pelo usuário

## Observação

Para gerar PDFs, o executável wkhtmltopdf.exe deve estar disponível junto ao projeto ou no PATH do sistema.

PDFs **escaneados (imagem)** não têm texto: use OCR antes ou carregue HTML/Word do cliente.
