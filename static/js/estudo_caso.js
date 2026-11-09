/* Análise de ações (app estudo_caso): abas, gráficos, formulário do passo 1 e página de espera.
   Sem dependências além do plotly.js (gráficos) e do Tom Select (campo das ações), carregados pelo template. */
(function () {
    'use strict';

    // ------------------------------------------------------------------ gráficos
    // As figuras vêm prontas de graficos_plotly.py (as mesmas do app Streamlit), pensadas para fundo branco.
    // No tema escuro, as cores de fundo, texto e grade trocam pelas equivalentes do portal; as das séries ficam.
    var FONTE = "'Source Sans', 'Source Sans Pro', system-ui, 'Segoe UI', sans-serif";
    var FONTE_PORTAL = "'IBM Plex Sans', system-ui, -apple-system, sans-serif";
    var ESCURO = [
        ['"#16323F"', '"#F4F5F7"'], ['"#5B6F7A"', '"#939BA8"'], ['"#DCE4E8"', '"#2B313A"'],
        ['"#FFFFFF"', '"#1B1F26"'], ['"#FFF"', '"#1B1F26"'], ['"rgba(255,255,255,.9)"', '"rgba(27,31,38,.9)"'],
        ['"#DCE7F3"', '"#22303F"'], ['"#F4F6F7"', '"#2B313A"']
    ];
    var CONFIG = { displayModeBar: false, scrollZoom: false, responsive: true };

    function temaEscuro() {
        return document.documentElement.getAttribute('data-bs-theme') === 'dark';
    }

    function trocarTodas(texto, de, para) {
        return texto.split(de).join(para).split(de.toLowerCase()).join(para);
    }

    function figura(script) {
        var texto = trocarTodas(script.textContent, FONTE, FONTE_PORTAL);
        if (temaEscuro()) {
            ESCURO.forEach(function (par) { texto = trocarTodas(texto, par[0], par[1]); });
        }
        return JSON.parse(texto);
    }

    function visivel(el) {
        return el.offsetParent !== null;
    }

    // Um gráfico só é desenhado quando aparece (aba aberta, "Entenda melhor" aberto): escondido, o plotly erra a largura.
    function desenharVisiveis(forcar) {
        if (!window.Plotly) { return; }
        document.querySelectorAll('script.figura-plotly').forEach(function (script) {
            var alvo = document.getElementById(script.dataset.alvo);
            if (!alvo || !visivel(alvo)) { return; }
            if (alvo.dataset.desenhado && !forcar) {
                window.Plotly.Plots.resize(alvo);
                return;
            }
            var f = figura(script);
            window.Plotly.react(alvo, f.data, f.layout, CONFIG);
            alvo.dataset.desenhado = '1';
        });
    }

    // Trocar o tema redesenha tudo; os escondidos ficam para quando aparecerem.
    new MutationObserver(function () {
        document.querySelectorAll('.grafico-plotly[data-desenhado]').forEach(function (el) {
            delete el.dataset.desenhado;
        });
        desenharVisiveis(true);
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-bs-theme'] });

    document.addEventListener('toggle', function (e) {
        if (e.target.tagName === 'DETAILS' && e.target.open) { desenharVisiveis(false); }
    }, true);

    // ------------------------------------------------------------------ abas (um_por_vez)
    function abrirAba(aba) {
        var lista = aba.parentElement;
        var grupo = lista.parentElement;
        lista.querySelectorAll(':scope > .aba').forEach(function (outra) {
            var ativa = outra === aba;
            outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
            outra.tabIndex = ativa ? 0 : -1;
            var painel = document.getElementById(outra.getAttribute('aria-controls'));
            if (painel && painel.parentElement === grupo) { painel.hidden = !ativa; }
        });
        desenharVisiveis(false);
    }

    document.querySelectorAll('.um-por-vez > .abas').forEach(function (lista) {
        var abas = Array.prototype.slice.call(lista.querySelectorAll(':scope > .aba'));
        abas.forEach(function (aba, i) {
            aba.tabIndex = i === 0 ? 0 : -1;
            aba.addEventListener('click', function () { abrirAba(aba); });
            aba.addEventListener('keydown', function (e) {
                var passo = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
                if (!passo) { return; }
                e.preventDefault();
                var proxima = abas[(i + passo + abas.length) % abas.length];
                proxima.focus();
                abrirAba(proxima);
            });
        });
    });

    // ------------------------------------------------------------------ "Ir para" (navegação entre telas)
    var irPara = document.querySelector('.ir-para select');
    if (irPara) {
        irPara.addEventListener('change', function () { irPara.form.submit(); });
        var botaoIr = document.querySelector('.ir-para button');
        if (botaoIr) { botaoIr.hidden = true; }
    }

    // ------------------------------------------------------------------ formulário do passo 1
    var form = document.querySelector('form.escolhas');
    if (form) {
        var descricoes = JSON.parse(document.getElementById('descricoes-escolhas').textContent);
        var acoes = form.querySelector('select[name="tickers"]');
        var seletor = null;
        if (acoes && window.TomSelect) {
            seletor = new window.TomSelect(acoes, {
                maxItems: Number(acoes.dataset.max || 10),
                placeholder: 'Digite o código, como PETR4',
                plugins: ['remove_button'],
                hidePlaceholder: true
            });
        }

        var atualizar = function () {
            var selecao = form.querySelector('input[name="selecao"]:checked');
            var automatica = selecao && selecao.value === 'automatica';
            var n = acoes ? Array.prototype.filter.call(acoes.options, function (o) { return o.selected; }).length : 0;
            form.querySelectorAll('[data-so-manual]').forEach(function (el) { el.hidden = automatica; });
            form.querySelectorAll('[data-so-automatica]').forEach(function (el) { el.hidden = !automatica; });
            var divisao = form.querySelector('[data-campo-divisao]');
            if (divisao) { divisao.hidden = !(automatica || n >= 2); }
            var semAcao = !automatica && n === 0;
            var aviso = form.querySelector('[data-aviso-sem-acao]');
            if (aviso) { aviso.hidden = !semAcao; }
            form.querySelector('button[type="submit"]').disabled = semAcao;
            Object.keys(descricoes).forEach(function (campo) {
                var el = form.querySelector('[name="' + campo + '"]:not([type="radio"])');
                var alvo = form.querySelector('[data-descricao="' + campo + '"]');
                if (el && alvo && descricoes[campo][el.value]) { alvo.textContent = descricoes[campo][el.value]; }
            });
        };
        form.addEventListener('change', atualizar);
        if (seletor) { seletor.on('change', atualizar); }
        atualizar();
    }

    // ------------------------------------------------------------------ página de espera
    var espera = document.querySelector('[data-status-url]');
    if (espera) {
        var etapas = Array.prototype.slice.call(espera.querySelectorAll('.progresso li'));
        var fila = espera.querySelector('[data-fila]');
        var consultar = function () {
            fetch(espera.dataset.statusUrl, { headers: { Accept: 'application/json' }, cache: 'no-store' })
                .then(function (r) { return r.json(); })
                .then(function (s) {
                    if (s.situacao === 'pronto' || s.situacao === 'erro' || s.situacao === 'parado') {
                        window.location.reload();
                        return;
                    }
                    if (fila) {
                        fila.hidden = s.situacao !== 'na_fila';
                        if (s.situacao === 'na_fila') {
                            fila.textContent = s.na_frente === 1 ? 'Há 1 análise na sua frente.' : 'Há ' + s.na_frente + ' análises na sua frente.';
                        }
                    }
                    var atual = etapas.findIndex(function (li) { return li.dataset.etapa === s.etapa; });
                    etapas.forEach(function (li, i) {
                        li.classList.toggle('feita', atual > -1 && i < atual);
                        li.classList.toggle('atual', i === atual);
                    });
                    setTimeout(consultar, 3000);
                })
                .catch(function () { setTimeout(consultar, 5000); });
        };
        setTimeout(consultar, 1500);
    }

    // Desenha o que já está à vista. O plotly.js é carregado com defer, antes deste script.
    desenharVisiveis(false);
})();
