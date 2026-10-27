// Gráfico de evolução mês a mês dos simuladores, desenhado em SVG sem biblioteca.
// Lê os pontos de <script id="pontos-grafico"> (gerado por json_script, formato
// [{mes, saldo}, ...]) e desenha em <svg id="grafico-evolucao-svg">, com o tooltip
// em #grafico-evolucao-tooltip. Estilos em static/css/grafico.css.
(function () {
    var dadosEl = document.getElementById('pontos-grafico');
    var svg = document.getElementById('grafico-evolucao-svg');
    var tooltip = document.getElementById('grafico-evolucao-tooltip');
    if (!dadosEl || !svg || !tooltip) return;

    var pontos = JSON.parse(dadosEl.textContent);
    if (!pontos.length) return;

    var NS = 'http://www.w3.org/2000/svg';
    // O viewBox acompanha o tamanho real renderizado (em vez de um 800x320 fixo)
    // para que o font-size dos rótulos, em px, corresponda a pixels de tela de
    // verdade — sem isso, o texto encolhe junto com a largura do card no mobile
    // e fica ilegível.
    var caixaSvg = svg.getBoundingClientRect();
    var largura = Math.round(caixaSvg.width) || 800;
    var altura = Math.round(caixaSvg.height) || 320;
    svg.setAttribute('viewBox', '0 0 ' + largura + ' ' + altura);
    var margem = { topo: 14, direita: 16, baixo: 32, esquerda: 68 };

    function criarEl(tag, atributos) {
        var el = document.createElementNS(NS, tag);
        for (var chave in atributos) {
            el.setAttribute(chave, atributos[chave]);
        }
        return el;
    }

    function passoAgradavel(valorMax, numTicks) {
        var passoBruto = valorMax / numTicks;
        if (passoBruto <= 0) return 1;
        var expoente = Math.floor(Math.log(passoBruto) / Math.LN10);
        var fracao = passoBruto / Math.pow(10, expoente);
        var fracaoAgradavel = fracao <= 1 ? 1 : fracao <= 2 ? 2 : fracao <= 5 ? 5 : 10;
        return fracaoAgradavel * Math.pow(10, expoente);
    }

    function formatarReais(valor, comCentavos) {
        return 'R$ ' + valor.toLocaleString('pt-BR', {
            minimumFractionDigits: comCentavos ? 2 : 0,
            maximumFractionDigits: comCentavos ? 2 : 0,
        });
    }

    // Versão compacta (8 mil, 1,2 mi, 9,9 bi...) para o eixo Y: um período longo, ou
    // uma dívida que nunca quita (600 meses de juros compostos), pode gerar saldos
    // com dezenas de dígitos, que um rótulo por extenso jamais caberia na margem.
    function formatarReaisEixo(valor) {
        if (Math.abs(valor) < 1e15) {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency', currency: 'BRL', notation: 'compact', maximumFractionDigits: 1,
            }).format(valor);
        }
        return 'R$ ' + valor.toExponential(1).replace('.', ',').replace('e+', 'e');
    }

    var maxSaldo = Math.max.apply(null, pontos.map(function (p) { return p.saldo; }));
    var passoY = passoAgradavel(maxSaldo, 4);
    var eixoMaxY = Math.max(passoY, Math.ceil(maxSaldo / passoY) * passoY);

    var valoresEixoY = [];
    for (var v = 0; v <= eixoMaxY + 0.01; v += passoY) valoresEixoY.push(v);
    var rotulosEixoY = valoresEixoY.map(formatarReaisEixo);

    // Mede a largura real dos rótulos para dimensionar a margem esquerda —
    // caso contrário, rótulos muito largos (números muito grandes) ficam cortados.
    var medidor = document.createElement('canvas').getContext('2d');
    medidor.font = '13px sans-serif';
    var larguraMaxRotulo = Math.max.apply(null, rotulosEixoY.map(function (t) {
        return medidor.measureText(t).width;
    }));
    margem.esquerda = Math.min(140, Math.max(56, larguraMaxRotulo + 16));

    var areaLargura = largura - margem.esquerda - margem.direita;
    var areaAltura = altura - margem.topo - margem.baixo;

    function escalaX(i) {
        return margem.esquerda + (pontos.length === 1 ? 0 : (i / (pontos.length - 1)) * areaLargura);
    }
    function escalaY(v) {
        return margem.topo + areaAltura - (v / eixoMaxY) * areaAltura;
    }

    // Grade e rótulos do eixo Y
    valoresEixoY.forEach(function (v, indice) {
        var y = escalaY(v);
        svg.appendChild(criarEl('line', {
            class: 'grade', x1: margem.esquerda, x2: largura - margem.direita, y1: y, y2: y,
        }));
        var rotuloY = criarEl('text', {
            class: 'rotulo', x: margem.esquerda - 8, y: y + 3, 'text-anchor': 'end',
        });
        rotuloY.textContent = rotulosEixoY[indice];
        svg.appendChild(rotuloY);
    });

    // Rótulos do eixo X: até ~6 marcações, mas menos em telas estreitas —
    // como o texto agora tem tamanho real (ver viewBox acima), rótulos "Mês N"
    // se sobrepõem se tentarmos manter sempre 6 num gráfico estreito no mobile.
    var textoXMaisLargo = 'Mês ' + pontos[pontos.length - 1].mes;
    var larguraRotuloX = medidor.measureText(textoXMaisLargo).width + 24;
    var numTicksXDesejado = Math.max(2, Math.min(6, Math.floor(areaLargura / larguraRotuloX)));
    var passoX = Math.max(1, Math.round((pontos.length - 1) / numTicksXDesejado) || 1);
    var indicesX = [];
    for (var i = 0; i < pontos.length; i += passoX) indicesX.push(i);
    if (indicesX[indicesX.length - 1] !== pontos.length - 1) indicesX.push(pontos.length - 1);

    // O último rótulo é alinhado pela direita (ver abaixo) para não ser cortado
    // na borda do viewBox, o que o deixa mais largo para o lado esquerdo do que
    // um rótulo centralizado comum — se não sobrar espaço, o penúltimo rótulo
    // encosta nele. Remove o penúltimo nesse caso (mantendo sempre o primeiro).
    if (indicesX.length >= 3) {
        var iPenultimo = indicesX[indicesX.length - 2];
        var iUltimo = indicesX[indicesX.length - 1];
        var larguraUltimo = medidor.measureText('Mês ' + pontos[iUltimo].mes).width;
        var larguraPenultimo = medidor.measureText('Mês ' + pontos[iPenultimo].mes).width;
        var espaco = (escalaX(iUltimo) - larguraUltimo) - (escalaX(iPenultimo) + larguraPenultimo / 2);
        if (espaco < 8) indicesX.splice(indicesX.length - 2, 1);
    }

    indicesX.forEach(function (i) {
        // O último rótulo fica centralizado exatamente na borda direita da área
        // do gráfico — com text-anchor "middle" metade do texto ultrapassaria o
        // viewBox e seria cortada, então esse aqui é alinhado pela direita.
        var ehUltimo = i === pontos.length - 1;
        var rotuloX = criarEl('text', {
            class: 'rotulo', x: escalaX(i), y: altura - margem.baixo + 18,
            'text-anchor': ehUltimo ? 'end' : 'middle',
        });
        rotuloX.textContent = 'Mês ' + pontos[i].mes;
        svg.appendChild(rotuloX);
    });

    // Eixo base (mês 0)
    svg.appendChild(criarEl('line', {
        class: 'eixo', x1: margem.esquerda, x2: largura - margem.direita,
        y1: altura - margem.baixo, y2: altura - margem.baixo,
    }));

    // Área e linha do saldo
    var coordenadas = pontos.map(function (p, i) { return escalaX(i) + ',' + escalaY(p.saldo); });
    var yBase = altura - margem.baixo;
    var dArea = 'M' + escalaX(0) + ',' + yBase + ' L' + coordenadas.join(' L') + ' L' + escalaX(pontos.length - 1) + ',' + yBase + ' Z';
    var dLinha = 'M' + coordenadas.join(' L');
    svg.appendChild(criarEl('path', { class: 'area-saldo', d: dArea }));
    svg.appendChild(criarEl('path', { class: 'linha-saldo', d: dLinha }));

    // Marcador no ponto final
    var ultimo = pontos[pontos.length - 1];
    svg.appendChild(criarEl('circle', {
        class: 'marcador-final', cx: escalaX(pontos.length - 1), cy: escalaY(ultimo.saldo), r: 5,
    }));

    // Crosshair (escondido até interação)
    var crosshairLinha = criarEl('line', { class: 'crosshair-linha', y1: margem.topo, y2: yBase });
    var crosshairPonto = criarEl('circle', { class: 'crosshair-ponto', r: 5 });
    var crosshairGrupo = criarEl('g', { style: 'display:none' });
    crosshairGrupo.appendChild(crosshairLinha);
    crosshairGrupo.appendChild(crosshairPonto);
    svg.appendChild(crosshairGrupo);

    function indiceMaisProximo(xSvg) {
        var proporcao = (xSvg - margem.esquerda) / areaLargura;
        var i = Math.round(proporcao * (pontos.length - 1));
        return Math.max(0, Math.min(pontos.length - 1, i));
    }

    function mostrarCrosshair(i) {
        var p = pontos[i];
        var x = escalaX(i);
        var y = escalaY(p.saldo);
        crosshairLinha.setAttribute('x1', x);
        crosshairLinha.setAttribute('x2', x);
        crosshairPonto.setAttribute('cx', x);
        crosshairPonto.setAttribute('cy', y);
        crosshairGrupo.style.display = '';

        tooltip.innerHTML = '';
        var valorEl = document.createElement('strong');
        valorEl.textContent = formatarReais(p.saldo, true);
        var mesEl = document.createElement('span');
        mesEl.textContent = 'Mês ' + p.mes;
        tooltip.appendChild(valorEl);
        tooltip.appendChild(document.createElement('br'));
        tooltip.appendChild(mesEl);
        tooltip.hidden = false;
        tooltip.style.left = ((x / largura) * 100) + '%';
        tooltip.style.top = ((y / altura) * 100) + '%';
    }

    function esconderCrosshair() {
        crosshairGrupo.style.display = 'none';
        tooltip.hidden = true;
    }

    var overlay = criarEl('rect', {
        class: 'grafico-overlay', x: margem.esquerda, y: margem.topo, width: areaLargura, height: areaAltura,
    });
    overlay.addEventListener('pointermove', function (evento) {
        var retangulo = svg.getBoundingClientRect();
        var escalaViewBox = largura / retangulo.width;
        var xSvg = (evento.clientX - retangulo.left) * escalaViewBox;
        mostrarCrosshair(indiceMaisProximo(xSvg));
    });
    overlay.addEventListener('pointerleave', esconderCrosshair);
    svg.appendChild(overlay);

    var indiceFoco = pontos.length - 1;
    svg.addEventListener('keydown', function (evento) {
        if (evento.key === 'ArrowLeft') {
            indiceFoco = Math.max(0, indiceFoco - 1);
            mostrarCrosshair(indiceFoco);
            evento.preventDefault();
        } else if (evento.key === 'ArrowRight') {
            indiceFoco = Math.min(pontos.length - 1, indiceFoco + 1);
            mostrarCrosshair(indiceFoco);
            evento.preventDefault();
        }
    });
    svg.addEventListener('focus', function () { mostrarCrosshair(indiceFoco); });
    svg.addEventListener('blur', esconderCrosshair);
})();
