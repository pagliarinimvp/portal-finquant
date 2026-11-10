"""Gera as imagens da marca em static/img/: favicon, ícone da Apple e prévia de link.

Uso (na raiz do projeto, com o venv ativo): python scripts/gerar_imagens_marca.py

O desenho é o mesmo de templates/ilustracoes/marca.svg (quadro com três
barras), nas cores fixas da navbar (--fq-nav-bg/--fq-nav-fg em site.css).
O favicon.svg é escrito à mão; os PNG e o .ico saem daqui porque o WhatsApp,
o Safari e o /favicon.ico não aceitam SVG. Fonte: DejaVu (a mesma do PDF da
análise de ações), já versionada em estudo_caso/fontes/.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / 'static' / 'img'
FONTES = RAIZ / 'estudo_caso' / 'fontes'

FUNDO = '#14161A'      # --fq-nav-bg
TINTA = '#F4F5F7'      # --fq-nav-fg
ACENTO = '#6C93B8'     # --fq-teal do tema escuro
SUAVE = '#A9B1BC'


def desenhar_marca(draw, x, y, lado, cor, espessura):
    """Quadro com três barras, nas proporções do viewBox 24x24 do marca.svg."""
    u = lado / 24
    draw.rounded_rectangle(
        [x + 2.5 * u, y + 2.5 * u, x + 21.5 * u, y + 21.5 * u],
        radius=3 * u, outline=cor, width=max(1, round(1.6 * u * espessura)),
    )
    largura = max(1, round(1.8 * u * espessura))
    for bx, topo in ((7, 12), (12, 8), (17, 10.5)):
        draw.line([x + bx * u, y + 16 * u, x + bx * u, y + topo * u], fill=cor, width=largura)
        # Ponta arredondada, como o stroke-linecap="round" do SVG.
        r = largura / 2
        for by in (16, topo):
            draw.ellipse([x + bx * u - r, y + by * u - r, x + bx * u + r, y + by * u + r], fill=cor)


def icone(lado):
    img = Image.new('RGB', (lado, lado), FUNDO)
    desenhar_marca(ImageDraw.Draw(img), 0, 0, lado, TINTA, espessura=1.4)
    return img


def previa():
    largura, altura = 1200, 630
    img = Image.new('RGB', (largura, altura), FUNDO)
    draw = ImageDraw.Draw(img)
    negrito = ImageFont.truetype(str(FONTES / 'DejaVuSans-Bold.ttf'), 76)
    normal = ImageFont.truetype(str(FONTES / 'DejaVuSans.ttf'), 38)
    pequeno = ImageFont.truetype(str(FONTES / 'DejaVuSans.ttf'), 28)

    desenhar_marca(draw, 90, 120, 150, TINTA, espessura=1.2)
    draw.text((90, 300), 'Portal FinQuant', font=negrito, fill=TINTA)
    draw.text((90, 400), 'Finanças quantitativas,', font=normal, fill=SUAVE)
    draw.text((90, 450), 'explicadas de forma simples', font=normal, fill=SUAVE)
    # Régua com marcações (.fq-regua), o motivo de assinatura do site.
    draw.line([90, 540, 1110, 540], fill=ACENTO, width=3)
    for i in range(0, 11):
        x = 90 + i * 102
        draw.line([x, 540, x, 528 if i % 5 else 520], fill=ACENTO, width=3)
    draw.text((90, 560), 'Artigos · Simuladores · Análise de ações', font=pequeno, fill=SUAVE)
    return img


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    icone(180).save(DESTINO / 'apple-touch-icon.png', optimize=True)
    icone(256).save(DESTINO / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    previa().save(DESTINO / 'previa.png', optimize=True)
    for nome in ('apple-touch-icon.png', 'favicon.ico', 'previa.png'):
        print(nome, (DESTINO / nome).stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
