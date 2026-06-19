-- ============================================================
-- Portal FinQuant — Script de Criação do Banco de Dados
-- Supabase / PostgreSQL
-- ============================================================
-- Execute este script no SQL Editor do Supabase:
-- Dashboard → SQL Editor → New Query → Cole o conteúdo → Run
-- ============================================================


-- ── Tabela: usuarios_perfil ─────────────────────────────────────────────────
-- Armazena os dados do questionário de perfil preenchido na Página 2.

CREATE TABLE IF NOT EXISTS public.usuarios_perfil (
    id                  UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome                TEXT        NOT NULL,
    email               TEXT        NOT NULL,
    idade               INTEGER     CHECK (idade BETWEEN 14 AND 100),
    genero              TEXT,
    faixa_renda         TEXT,
    produtos_financeiros TEXT[],
    nivel_renda_variavel TEXT,
    nivel_estatistica   TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()  -- atualizado automaticamente via trigger
);

-- Habilita Row Level Security: cada usuário acessa apenas seus próprios dados.
ALTER TABLE public.usuarios_perfil ENABLE ROW LEVEL SECURITY;

-- Política: o usuário pode inserir seu próprio registro.
CREATE POLICY "Inserir proprio perfil"
    ON public.usuarios_perfil
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Política: o usuário pode ler seu próprio registro.
CREATE POLICY "Ler proprio perfil"
    ON public.usuarios_perfil
    FOR SELECT
    USING (auth.uid() = id);

-- Política: o usuário pode atualizar seu próprio registro.
CREATE POLICY "Atualizar proprio perfil"
    ON public.usuarios_perfil
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);


-- ── Tabela: avaliacoes ──────────────────────────────────────────────────────
-- Armazena as avaliações do portal preenchidas na Página 5.

CREATE TABLE IF NOT EXISTS public.avaliacoes (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id           UUID        REFERENCES auth.users(id) ON DELETE CASCADE,
    facilidade_uso       INTEGER     CHECK (facilidade_uso BETWEEN 1 AND 5),
    clareza_conteudo     INTEGER     CHECK (clareza_conteudo BETWEEN 1 AND 5),
    aprendizado_percebido INTEGER    CHECK (aprendizado_percebido BETWEEN 1 AND 5),
    confianca_pos_portal INTEGER     CHECK (confianca_pos_portal BETWEEN 1 AND 5),
    recomendaria         BOOLEAN,
    comentario_livre     TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Habilita Row Level Security.
ALTER TABLE public.avaliacoes ENABLE ROW LEVEL SECURITY;

-- Política: o usuário pode inserir sua própria avaliação.
CREATE POLICY "Inserir propria avaliacao"
    ON public.avaliacoes
    FOR INSERT
    WITH CHECK (auth.uid() = usuario_id);

-- Política: o usuário pode ler sua própria avaliação.
CREATE POLICY "Ler propria avaliacao"
    ON public.avaliacoes
    FOR SELECT
    USING (auth.uid() = usuario_id);


-- ── Índices de Performance ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_usuarios_perfil_created_at ON public.usuarios_perfil(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_created_at ON public.avaliacoes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_usuario_id ON public.avaliacoes(usuario_id);

-- ── Trigger: updated_at automático em usuarios_perfil ─────────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_usuarios_perfil_updated_at ON public.usuarios_perfil;
CREATE TRIGGER trg_usuarios_perfil_updated_at
  BEFORE UPDATE ON public.usuarios_perfil
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ============================================================
-- Consultas para Análise dos Dados da Pesquisa
-- (Execute separadamente no SQL Editor conforme necessário)
-- ============================================================

-- Ver todos os perfis cadastrados
-- SELECT * FROM public.usuarios_perfil ORDER BY created_at DESC;

-- Distribuição por gênero
-- SELECT genero, COUNT(*) as total
-- FROM public.usuarios_perfil
-- GROUP BY genero ORDER BY total DESC;

-- Distribuição por faixa de renda
-- SELECT faixa_renda, COUNT(*) as total
-- FROM public.usuarios_perfil
-- GROUP BY faixa_renda ORDER BY total DESC;

-- Distribuição do nível de conhecimento em renda variável
-- SELECT nivel_renda_variavel, COUNT(*) as total
-- FROM public.usuarios_perfil
-- GROUP BY nivel_renda_variavel ORDER BY total DESC;

-- Médias das avaliações recebidas
-- SELECT
--     ROUND(AVG(facilidade_uso), 2)       AS media_facilidade,
--     ROUND(AVG(clareza_conteudo), 2)     AS media_clareza,
--     ROUND(AVG(aprendizado_percebido), 2) AS media_aprendizado,
--     ROUND(AVG(confianca_pos_portal), 2) AS media_confianca,
--     COUNT(*)                            AS total_respostas,
--     SUM(CASE WHEN recomendaria THEN 1 ELSE 0 END) AS total_recomendariam
-- FROM public.avaliacoes;
