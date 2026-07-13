# CSS Live Lab

Aplicação web para editar CSS em tempo real com pré-visualização, templates, exportação de CSS e geração de PDF.

## Funcionalidades

- Editor de CSS com preview ao lado
- Carregamento de HTML e CSS local
- Salvamento e recuperação de templates
- Exportação de CSS
- Geração de PDF via wkhtmltopdf
- Assistente com IA para sugestões de ajustes

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

Crie um arquivo .env com as variáveis abaixo, se quiser usar a integração com IA:

```env
NVIDIA_API_KEY=sua_chave
NVIDIA_MODEL=z-ai/glm-5.2
```

## Estrutura principal

- app.py: aplicação Flask
- templates/index.html: interface principal
- index.html: versão estática para uso direto
- css-live-lab.html: versão alternativa da interface
- saved_templates/: templates salvos pelo usuário

## Observação

Para gerar PDFs, o executável wkhtmltopdf.exe deve estar disponível junto ao projeto ou no PATH do sistema.
