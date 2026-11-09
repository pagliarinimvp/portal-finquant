"""Configuração da análise: as escolhas da pessoa, o capital e o que fica fixo.

Os parâmetros abaixo são escolhas desta ferramenta, para simplificar a análise, e não valores de mercado
nem recomendações. As fontes dos métodos estão em `quant/referencias.py`. Tudo é texto ou número simples,
para ser preenchido por uma `forms.Form` do Django sem transformação.
"""
from dataclasses import asdict, dataclass, field
from datetime import date

from . import universo

# ---------------------------------------------------------------------------- escolhas técnicas
ANOS_HISTORICO = 10            # histórico longo cobre várias fases do mercado
FRACAO_TREINO = 0.5            # o treino inicial é a primeira metade do histórico
N_JANELAS = 5                  # a segunda metade vira 5 janelas de teste, de cerca de 1 ano cada com 10 anos de histórico
LIMITE_PESO = 0.40             # nas divisões otimizadas, nenhuma ação passa de 40% (o mesmo limite do alerta de concentração)
PESO_MINIMO = 0.005            # abaixo de 0,5% a ação não recebe dinheiro
MAX_ACOES = 10                 # limite de ações por carteira
SIGNIFICANCIA = 0.05           # nível de significância usual
N_SIMULACOES = 10_000          # embaralhamentos da ordem das operações
N_CARTEIRAS = 20_000           # carteiras sorteadas na nuvem da fronteira eficiente
LOTE = 100                     # as compras são em múltiplos de 100 ações
MIN_PREGOES = 500              # abaixo disso não sobra teste que permita concluir algo (cerca de 2 anos)
SEMENTE = 42                   # mesmas simulações a cada execução

# ---------------------------------------------------------------------------- catálogo das escolhas
SELECOES = {
    "manual": {
        "rotulo": "Eu escolho as ações",
        "descricao": "Você indica de 1 a 10 ações do Ibovespa.",
    },
    "automatica": {
        "rotulo": "Seleção automática",
        "descricao": "A ferramenta testa a regra nas ações do Ibovespa, só com os dados anteriores a cada janela de teste, e fica com até 10 melhores.",
    },
}

DIVISOES = {
    "igual": {
        "rotulo": "Partes iguais",
        "descricao": "O mesmo valor em cada ação. Não tenta prever nada.",
    },
    "min_variancia": {
        "rotulo": "Menor oscilação",
        "descricao": "Busca a mistura de ações que menos balançou no passado (mínima variância), com no máximo 40% em cada ação.",
    },
    "max_sharpe": {
        "rotulo": "Melhor retorno pelo risco",
        "descricao": "Busca a mistura que mais rendeu para cada unidade de oscilação (máximo Sharpe), com no máximo 40% em cada ação.",
    },
}

MEDIAS = {
    "rapido": {
        "curta": 10, "longa": 20, "rotulo": "Rápido (10 e 20 dias)",
        "descricao": "Reage mais cedo às mudanças e tende a operar mais vezes.",
    },
    "intermediario": {
        "curta": 12, "longa": 50, "rotulo": "Intermediário (12 e 50 dias)",
        "descricao": "Fica entre os ritmos rápido e lento.",
    },
    "lento": {
        "curta": 26, "longa": 100, "rotulo": "Lento (26 e 100 dias)",
        "descricao": "Reage mais devagar e tende a operar menos vezes.",
    },
    "muito_lento": {
        "curta": 50, "longa": 200, "rotulo": "Muito lento (50 e 200 dias)",
        "descricao": "O ritmo mais lento desta lista. Quando a média de 50 dias passa para cima da de 200, o mercado chama de cruzamento de ouro (golden cross).",
    },
}
MEDIAS_PELO_TREINO = "treino"
ROTULO_PELO_TREINO = "Deixar o treino escolher"
DESCRICAO_PELO_TREINO = "Antes de cada janela de teste, compara os 4 ritmos com os dados anteriores a ela e usa o melhor."

PROTECOES = {
    "sem": {
        "stop": None, "alvo": None, "rotulo": "Sem saída automática",
        "descricao": "Só a regra das médias decide a saída.",
    },
    "1_1": {
        "stop": 10.0, "alvo": 10.0, "rotulo": "Perda de 10% ou ganho de 10%",
        "descricao": "Sai ao perder 10% ou ao ganhar 10%. Sem custos, empata acertando metade das vezes.",
    },
    "2_1": {
        "stop": 10.0, "alvo": 20.0, "rotulo": "Perda de 10% ou ganho de 20%",
        "descricao": "Arrisca 1 para tentar ganhar 2. Sem custos, empata acertando uma vez em três.",
    },
    "3_1": {
        "stop": 10.0, "alvo": 30.0, "rotulo": "Perda de 10% ou ganho de 30%",
        "descricao": "Arrisca 1 para tentar ganhar 3. Sem custos, empata acertando uma vez em quatro.",
    },
}

CUSTOS = {
    "tarifas_b3": {
        "pct": 0.03, "imposto": True, "rotulo": "Tarifas da B3 e imposto",
        "descricao": "0,03% em cada compra e venda e imposto sobre o lucro, como na vida real.",
    },
    "sem_custo": {
        "pct": 0.0, "imposto": False, "rotulo": "Sem custo e sem imposto",
        "descricao": "Serve para ver o quanto tarifas e imposto pesam no resultado.",
    },
}

N_COMBINACOES = len(MEDIAS) * len(PROTECOES)      # tentativas oferecidas: entram no desconto do Sharpe


def inicio_historico(hoje: date | None = None) -> str:
    """Data mais antiga da análise (hoje − ANOS_HISTORICO anos), no formato AAAA-MM-DD."""
    hoje = hoje or date.today()
    try:
        return hoje.replace(year=hoje.year - ANOS_HISTORICO).isoformat()
    except ValueError:                                  # 29/02
        return hoje.replace(year=hoje.year - ANOS_HISTORICO, day=28).isoformat()


@dataclass
class ConfigAnalise:
    tickers: list = field(default_factory=lambda: ["PETR4"])
    selecao: str = "manual"                # manual | automatica (na automática, `tickers` é ignorado)
    divisao: str = "igual"                 # só vale com 2 ou mais ações
    medias: str = "intermediario"          # chave de MEDIAS ou MEDIAS_PELO_TREINO
    protecao: str = "2_1"
    custo: str = "tarifas_b3"
    capital: float = 100_000.0
    fonte: str = "yfinance"                # yfinance | csv
    pasta_cache: str = "cache_dados"

    def validar(self) -> "ConfigAnalise":
        if self.selecao not in SELECOES:
            raise ValueError(f"Seleção desconhecida: {self.selecao}")
        if self.selecao == "manual":
            self.tickers = universo.validar_tickers(self.tickers)
            if len(self.tickers) > MAX_ACOES:
                raise ValueError(f"Escolha no máximo {MAX_ACOES} ações.")
        if self.divisao not in DIVISOES:
            raise ValueError(f"Divisão do dinheiro desconhecida: {self.divisao}")
        if self.medias != MEDIAS_PELO_TREINO and self.medias not in MEDIAS:
            raise ValueError(f"Ritmo das médias desconhecido: {self.medias}")
        if self.protecao not in PROTECOES:
            raise ValueError(f"Proteção desconhecida: {self.protecao}")
        if self.custo not in CUSTOS:
            raise ValueError(f"Custo desconhecido: {self.custo}")
        if self.capital < 1_000:
            raise ValueError("Use um capital de ao menos R$ 1.000.")
        if self.fonte not in ("yfinance", "csv"):
            raise ValueError("fonte deve ser 'yfinance' ou 'csv'.")
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict | None) -> "ConfigAnalise":
        d = d or {}
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
