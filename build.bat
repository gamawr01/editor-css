@echo off
REM ============================================================
REM  Build do CSS Live Lab .exe
REM  Gera dist/CSSLiveLab.exe (arquivo único)
REM ============================================================
echo.
echo  ============================================
echo   CSS Live Lab - Gerando .exe
echo  ============================================
echo.

REM instala dependencias (se faltar alguma)
pip install -r requirements.txt

REM limpa builds anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist app.spec del /q app.spec
if exist CSSLiveLab.spec del /q CSSLiveLab.spec

REM gera o .exe (arquivo unico, sem console, com todos os arquivos embutidos)
"C:\Users\Projetos\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\pyinstaller.exe" --onefile --name CSSLiveLab --add-binary "wkhtmltopdf.exe;." --add-data "templates;templates" --add-data "AI_CONTEXT.md;." --add-data ".env;." app.py

echo.
if exist dist\CSSLiveLab.exe (
  echo  ============================================
  echo   SUCESSO! .exe gerado em:
  echo   dist\CSSLiveLab.exe
  echo  ============================================
  echo.
  echo  Copie o CSSLiveLab.exe para qualquer pasta.
  echo  A pasta saved_templates\ sera criada ao lado dele.
  echo  Duplo clique para abrir no navegador.
) else (
  echo  ============================================
  echo   ERRO: o .exe nao foi gerado.
  echo   Verifique as mensagens acima.
  echo  ============================================
)
echo.
pause
