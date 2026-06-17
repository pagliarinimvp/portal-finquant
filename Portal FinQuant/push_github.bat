@echo off
chcp 65001 >nul
echo =============================================
echo   Portal FinQuant — Push para o GitHub
echo =============================================
echo.

cd /d "%~dp0"

echo [1/5] Inicializando repositório Git...
git init
git branch -M main

echo.
echo [2/5] Configurando remote origin...
git remote remove origin 2>nul
git remote add origin https://github.com/pagliarinimvp/portal-finquant.git

echo.
echo [3/5] Adicionando todos os arquivos...
git add .

echo.
echo [4/5] Criando commit inicial...
git commit -m "feat: Portal FinQuant completo - Streamlit + Supabase integrado"

echo.
echo [5/5] Fazendo push para o GitHub...
git push -u origin main

echo.
echo =============================================
echo   PUSH CONCLUIDO COM SUCESSO!
echo   Acesse: https://github.com/pagliarinimvp/portal-finquant
echo =============================================
echo.
pause
