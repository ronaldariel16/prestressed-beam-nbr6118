# Tasks — Dimensionamento de Vigas de Concreto Protendido

Projeto baseado na **NBR 6118:2014** (norma única). Escopo: seções **retangulares**, qualquer condição de apoio, concretos até **C50**. Cobertura: Capítulos 1 a 11 do manual de aulas (Torii, 2020).

**Convenções gerais:**
- Unidades SI: comprimento em metros (m), força em kN, tensão em MPa, momento em kN·m
- Tração positiva, compressão negativa
- Excentricidade `e` positiva quando abaixo do centroide
- Coordenada `x` ao longo do eixo da viga, origem no apoio esquerdo

---

## Fase 0 — Setup do Projeto

- [ ] **T0.1** Criar `requirements.txt` com dependências: `numpy`, `scipy`, `matplotlib`, `pandas`, `pytest`, `openpyxl`
- [ ] **T0.2** Criar `pyproject.toml` ou `setup.py` para o pacote
- [ ] **T0.3** Criar `.gitignore` (Python padrão)
- [ ] **T0.4** Criar `README.md` com instruções de uso
- [ ] **T0.5** Configurar pytest no diretório `tests/`

---

## Fase 1 — Módulos Base

### `src/geometry.py` — Propriedades da seção retangular

- [ ] **T1.1** Classe `RectangularSection(b, h)` com atributos:
  - `A` (área)
  - `I` (momento de inércia)
  - `yt`, `yb` (distâncias do centroide às fibras)
  - `zt`, `zb` (módulos seccionais)
- [ ] **T1.2** Método `__repr__` com resumo das propriedades
- [ ] **T1.3** Validações: b > 0, h > 0
- [ ] **T1.4** Teste unitário comparando com fórmulas analíticas

### `src/materials.py` — Concreto e aço (NBR 6118)

- [ ] **T1.5** Classe `Concrete(fck, fckj=None)`:
  - Validar `fck ≤ 50 MPa` (escopo)
  - `fct_m(fck) = 0,3 · fck^(2/3)` (§8.2.5)
  - `Eci(fck)` — módulo tangente inicial (§8.2.8): `Eci = αE · 5600 · √fck`
  - `Ecs(fck)` — módulo secante (§8.2.8): `Ecs = αi · Eci`, `αi = 0,8 + 0,2·fck/80`
  - `fcd(γc=1,4)` — tensão de cálculo
  - `phi(t_inf, t0, h_fic, umidade)` — coeficiente de fluência (§8.2.11) — implementar depois (T8.x)
- [ ] **T1.6** Classe `PrestressSteel(tipo, diametro)`:
  - Catálogo embutido: CP-190 RB (3 e 7 fios) com diâmetros nominais
  - Atributos: `fptk`, `fpyk`, `Aps_unit` (área por cordoalha), `Eps = 200 GPa`
  - Propriedades das cordoalhas conforme Tabela 3.1 do manual (ArcelorMittal)
  - Método `Pj_lim_unit()` = `min(0,74·Pptk ; 0,85·Ppyk)` (§9.6.1.2)
- [ ] **T1.7** Classe `PassiveSteel(categoria='CA50')`:
  - `fyk = 500 MPa`, `fyd = fyk/1,15`, `Es = 210 GPa`
- [ ] **T1.8** Testes unitários com valores de referência da NBR 6118

---

## Fase 2 — Esforços Solicitantes

### `src/supports.py` — Biblioteca de casos de apoio

- [ ] **T2.1** Classe abstrata `BeamSupport` com método `M(x, load)`:
  - Recebe carga distribuída uniforme `q` (kN/m), carga concentrada `(P, a)`, ou momento aplicado `(M0, a)`
  - Retorna momento fletor na posição `x`
- [ ] **T2.2** `SimplySupported(L)` — viga simplesmente apoiada
  - Carga distribuída: `M(x) = q·x·(L-x)/2`
  - Carga concentrada centrada: `M(x) = P·x/2` (x ≤ L/2)
- [ ] **T2.3** `FixedFixed(L)` — viga biengastada
  - Carga distribuída: `M(x) = q·(6Lx - 6x² - L²)/12`
  - Momentos de engastamento: `M_eng = -q·L²/12`
- [ ] **T2.4** `FixedPinned(L)` — viga engastada-apoiada
- [ ] **T2.5** `Cantilever(L)` — viga em balanço
  - Carga distribuída: `M(x) = -q·(L-x)²/2`
- [ ] **T2.6** `TwoSpanContinuous(L1, L2)` — viga contínua de 2 vãos
  - Resolver com método dos três momentos ou matriz de rigidez
- [ ] **T2.7** `CustomSupport(M_function)` — entrada genérica
  - Recebe função `M(x)` ou array `(x, M)` calculado externamente
- [ ] **T2.8** Método `critical_sections()` para cada classe — retorna lista de `x` onde `|M|` é máximo (positivo e negativo)
- [ ] **T2.9** Testes unitários para cada caso de apoio

### `src/loads.py` — Cargas e combinações

- [ ] **T2.10** Classe `Loads(gk, qk, usage='residencial')`:
  - `gk`: cargas permanentes (sem peso próprio), kN/m
  - `qk`: sobrecarga, kN/m
  - `usage`: define ψ1, ψ2 (Tabela 11.4 NBR 6118)
- [ ] **T2.11** Tabela embutida de ψ1, ψ2 por uso (residencial, comercial, depósito, etc.)
- [ ] **T2.12** Método `self_weight(section, gamma_c=25)` — calcula peso próprio em kN/m
- [ ] **T2.13** Função `combine_actions(level, Mgk, Mqk)`:
  - Nível **completa**: ELS-F = Rara, ELS-D = Frequente
  - Nível **limitada**: ELS-F = Frequente, ELS-D = Quase Permanente
  - Nível **parcial**: ELS-W = Frequente
  - Retorna dict com `Msw`, `Mse_F` (ELS-F), `Mse_D` (ELS-D)
- [ ] **T2.14** Função para combinação ELU: `Md = 1,4·(Mgk + Mqk)` (§11.7)
- [ ] **T2.15** Testes unitários

---

## Fase 3 — Tensões Limites e Verificação

### `src/stress_limits.py`

- [ ] **T3.1** Função `stress_limits(concrete, situation)`:
  - `situation = 'transfer'` → `ftt = 0,3·fckj^(2/3)`, `ftc = -0,7·fckj`
  - `situation = 'service'` → `fst = 0,3·fck^(2/3)`, `fsc = -0,7·fck`
  - `situation = 'service_ELS_D'` → `fst = 0`, `fsc = -0,7·fck`
- [ ] **T3.2** Testes unitários com Tabela 3.9 do manual

### `src/stress_check.py`

- [ ] **T3.3** Função `stresses_at_section(P, e, M, section)`:
  - Retorna `(σ_top, σ_bottom)` conforme Eqs. 5.4–5.5
- [ ] **T3.4** Função `check_stresses(σ_top, σ_bottom, limits)`:
  - Retorna dict com flags de aprovação e folga em cada limite
- [ ] **T3.5** Função `check_section(beam, x, situation)` — wrapper completo
- [ ] **T3.6** Validação com Exemplo 5.2.1 do manual (adaptado para retangular equivalente)

---

## Fase 4 — Pré-dimensionamento

### `src/presizing.py`

- [ ] **T4.1** Função `presize_general(Mse, Msw, η, limits)` — Eqs. 6.9–6.10:
  - Retorna `zt_req`, `zb_req`
- [ ] **T4.2** Função `presize_simplified(Ms, η, limits)` — Eqs. 6.13–6.14
- [ ] **T4.3** Função `min_height_rectangular(b, zt_req, zb_req)`:
  - Para retangular: `z = b·h²/6`, retorna `h_min = √(6·max(zt,zb)/b)`
- [ ] **T4.4** Procedimento iterativo (peso próprio depende de h):
  - Iniciar com `h` estimado
  - Calcular `Msw`
  - Reaplicar critério geral
  - Convergir (tolerância 1 mm)
- [ ] **T4.5** Avaliar nas seções críticas (positivo e negativo) e tomar o maior
- [ ] **T4.6** Validação com Exemplo 6.1.1 do manual

---

## Fase 5 — Diagrama de Magnel

### `src/magnel.py`

- [ ] **T5.1** Função `magnel_constraints(section, Msw, Mse, η, limits)`:
  - Retorna as 8 inequações da Eq. 7.1 como tuplas `(coef_e, coef_invP, lim, sense)` onde `sense ∈ {'≤', '≥'}`
- [ ] **T5.2** Função `feasible_region(constraints, e_range, invP_range)`:
  - Avalia o polígono viável no plano `(e, 1/Ps)`
  - Retorna vértices do polígono
- [ ] **T5.3** Função `plot_magnel(constraints, eccentricity_limits)`:
  - Plota com matplotlib: linhas vermelhas (≤), azuis (≥), região cinza (viável)
  - Marca limites geométricos `|e| ≤ h/2 - cobrimento`
- [ ] **T5.4** Função `select_design_point(feasible_region, strategy)`:
  - Estratégias: `'min_P'`, `'max_e'`, `'centroid'`, `'manual'(e, Ps)`
- [ ] **T5.5** Para vigas contínuas/biengastadas: aplicar Magnel em cada seção crítica e tomar intersecção das regiões viáveis
- [ ] **T5.6** Validação com Exemplo 7.1.1 do manual

---

## Fase 6 — Escolha da Armadura

### `src/reinforcement.py`

- [ ] **T6.1** Função `number_of_strands(Pj, steel)`:
  - `n = ⌈Pj / Pj_lim_unit⌉`
- [ ] **T6.2** Função `arrange_strands(n, section, cover, spacing)`:
  - Distribui cordoalhas em camadas respeitando espaçamentos mínimos (§18.6.2.3)
  - Cobrimento conforme Tabela 7.2 NBR 6118 (CAA)
  - Retorna posição `(y_i)` de cada cordoalha e excentricidade resultante `e_real`
- [ ] **T6.3** Validar `|e_real| ≤ h/2 - cobrimento`
- [ ] **T6.4** Recalcular `Pj_total = n · Pj_lim_unit` e atualizar Magnel
- [ ] **T6.5** Testes unitários

---

## Fase 7 — Perfil do Cabo

### `src/tendon_profile.py`

- [ ] **T7.1** Função `admissible_zone(beam, P_function, n_sections=21)`:
  - Avalia 8 condições da Eq. 7.1 em N seções ao longo de L
  - Retorna `(e_min(x), e_max(x))` da zona admissível
- [ ] **T7.2** Função `parabolic_profile(L, e_max, e_supports)`:
  - Gera traçado parabólico clássico
- [ ] **T7.3** Função `multi_parabola_profile(spans, e_at_points)`:
  - Para vigas contínuas: parábolas concordantes (Fig. 2.4 do manual)
- [ ] **T7.4** Função `straight_profile(L, e)` — cabo reto
- [ ] **T7.5** Função `verify_profile(profile, admissible_zone)`:
  - Verifica que `e(x)` está dentro da zona admissível em todas as seções
- [ ] **T7.6** Função `plot_admissible_zone(beam, profile)` — gráfico
- [ ] **T7.7** Validação com Exemplo 8.1 do manual

---

## Fase 8 — ELU à Flexão

### `src/uls_flexure.py`

- [ ] **T8.1** Função `MRd_simplified(section, dp, Aps, fpd)` — Eq. 9.1:
  - `MRd = 0,82·dp·Aps·fpd`
- [ ] **T8.2** Função `Mlim_rectangular(b, dp, fcd)` — Eq. 9.3:
  - `Mlim = 0,25·b·dp²·fcd`
- [ ] **T8.3** Função `fpd_eurocode(steel)`:
  - `fpd = fpyk / 1,15`
- [ ] **T8.4** Função `additional_passive_steel(Msd, MRd_p, dp, d, fyd)` — Eq. 9.13:
  - Calcula `As` adicional
  - Sugerir bitolas comerciais (φ8, φ10, φ12.5, φ16, φ20, φ25)
- [ ] **T8.5** Função `check_ULS(beam, x)`:
  - Calcula `Msd(x)` (combinação 1,4·(Mgk + Mqk))
  - Compara com `MRd(x)`
  - Retorna status e armadura adicional se necessário
- [ ] **T8.6** Verificar ductilidade: `MRd ≤ Mlim`
- [ ] **T8.7** Aplicar nas seções críticas (positivo e negativo)
- [ ] **T8.8** Validação com Exemplo do Cap. 9

---

## Fase 9 — ELS Adicionais

### `src/sls.py`

- [ ] **T9.1** Função `deflection(beam, load_case, support)`:
  - Integra equação da linha elástica para a condição de apoio
  - Casos tabelados: simplesmente apoiada, biengastada, balanço
  - Caso geral: integração numérica de `M(x)/(EI)`
- [ ] **T9.2** Função `prestress_camber(beam, profile, P)`:
  - Eq. 10.3: cabo reto → `v = -P·e·L²/(8·EI)`
  - Eq. 10.4: cabo parabólico → `v = -5·P·e·L²/(48·EI)`
  - Caso geral: integração numérica
- [ ] **T9.3** Função `phi_creep(t_inf, t0, h_fic, humidity)` — coeficiente de fluência (§8.2.11)
- [ ] **T9.4** Função `final_deflection(u_t0, phi)` — Eq. 10.2:
  - `u(t∞) = (1 + φ)·u(t0)`
- [ ] **T9.5** Função `check_ELS_DEF(beam, limits)`:
  - Limite Tabela 13.3 NBR 6118 (ex.: L/250 aceitabilidade visual)
- [ ] **T9.6** Função `check_ELS_D(beam, profile)`:
  - Verifica tensões com `fst = 0`
- [ ] **T9.7** Função `check_ELS_DP(beam, profile, ap_lim=50mm)`:
  - Calcular posição da LN onde tração ocorre
  - Verificar `ap ≥ 50 mm` da armadura ativa
- [ ] **T9.8** Validação com Exemplos 10.1.1, 10.1.2, 10.2.1, 10.3.1 do manual

---

## Fase 10 — Perdas de Protensão

### `src/losses.py`

**Perdas imediatas:**

- [ ] **T10.1** Função `friction_loss(Pj, x, alpha_total, μ=0.2, k=0.002)`:
  - `ΔP(x) = Pj·[1 - exp(-(μ·α + k·x))]` — Eq. 11.2
  - `α(x)` calculado pelo desvio angular acumulado do perfil parabólico
- [ ] **T10.2** Função `anchor_slip_loss(Aps, Eps, ΔA, L)`:
  - `ΔPanc = Aps·Eps·ΔA/L` — Eq. 11.5
  - Considerar protensão de uma ou duas extremidades
  - Modelo aproximado (constante ao longo do cabo)
- [ ] **T10.3** Função `elastic_shortening_loss(Aps, αp, σc, n_cables)`:
  - `ΔPenc = αp·Aps·σc·(n-1)/(2n)` — Eq. 11.7
  - `σc = P/A + P·e²/I` (na fibra do cabo)
- [ ] **T10.4** Função `immediate_losses(beam, profile, Pj, x)`:
  - Combina T10.1, T10.2, T10.3
  - Retorna `Pt(x)`

**Perdas progressivas (modelo simplificado §9.6.3.4.3):**

- [ ] **T10.5** Função `progressive_losses_simplified(beam, profile, Pt, t_inf, t0, x)`:
  - `Δσ_p/σ_p0 = (1/100)·{7,4 + (αp/18,7)·φ^1,07·(3 + σc,p0g)}` — Eq. 11.9
  - `σc,p0g = Pt/A + Pt·e²/I - Mgk·e/I` — Eq. 11.10
  - Retorna `Ps(x)`
- [ ] **T10.6** Função `total_losses(beam, profile, Pj, ...)`:
  - Encadeamento completo: imediatas + progressivas
  - Retorna arrays `Pt(x)`, `Ps(x)` ao longo da viga

**Iteração:**

- [ ] **T10.7** Função `iterate_losses(beam, profile, Pj, tol=0.01, max_iter=10)`:
  - Iterar até convergência de Pt, Ps (a tensão depende deles)
- [ ] **T10.8** Validação com Exemplo 11.3 do manual

---

## Fase 11 — Orquestração

### `src/beam.py`

- [ ] **T11.1** Classe `PrestressedBeam` que integra todos os módulos:
  - Atributos: `section`, `support`, `concrete`, `steel`, `loads`, `prestress_level`, `prestress_type`
  - Método `design()` que executa o fluxo completo:
    1. Pré-dimensionamento
    2. Magnel (estimativa inicial α=0,9, β=0,75)
    3. Escolha de armadura
    4. Perfil do cabo
    5. Cálculo de perdas reais
    6. Re-iteração com α, β, η reais
    7. Verificação ELU
    8. Verificação ELS-D / ELS-DP
    9. Verificação ELS-DEF
- [ ] **T11.2** Método `report()` — gera relatório completo (texto + tabelas)
- [ ] **T11.3** Método `plot_all()` — todos os gráficos
- [ ] **T11.4** Método `export_excel(filename)` — planilha com todos os resultados

---

## Fase 12 — Saída e Relatórios

### `src/reports.py`

- [ ] **T12.1** Geração de relatório em texto (Markdown ou TXT) com todas as etapas
- [ ] **T12.2** Geração de gráficos (matplotlib):
  - Diagrama de Magnel
  - Zona admissível e perfil do cabo
  - Diagrama de momentos (Msw, Mse, MRd, Md)
  - Tensões σ_top(x) e σ_bottom(x) no ato e em serviço
  - Distribuição de Pj, Pt, Ps ao longo da viga (perdas)
  - Flecha (linha elástica)
- [ ] **T12.3** Exportação para Excel (`openpyxl` ou `pandas`):
  - Aba 1: Dados de entrada
  - Aba 2: Propriedades da seção
  - Aba 3: Esforços solicitantes
  - Aba 4: Tensões nas seções críticas
  - Aba 5: Cálculo de perdas
  - Aba 6: Verificações (ELU, ELS)
  - Aba 7: Resumo final
- [ ] **T12.4** Geração de PDF do relatório (opcional, via `reportlab` ou conversão Markdown→PDF)

---

## Fase 13 — Exemplos e Validação

### `examples/`

- [ ] **T13.1** `example_01_simply_supported.py` — adaptação do Exemplo 5.2.1 do manual para seção retangular equivalente
- [ ] **T13.2** `example_02_fixed_fixed.py` — viga biengastada
- [ ] **T13.3** `example_03_cantilever.py` — viga em balanço
- [ ] **T13.4** `example_04_two_span_continuous.py` — viga contínua de 2 vãos
- [ ] **T13.5** `example_05_complete_workflow.py` — fluxo completo com relatório e Excel

### `tests/`

- [ ] **T13.6** Testes unitários para cada módulo (cobertura > 80%)
- [ ] **T13.7** Testes de integração comparando com exemplos do manual
- [ ] **T13.8** Testes de regressão

---

## Critérios de Aceitação Globais

- [ ] Todos os exemplos do manual (Caps. 5–11) reproduzidos com diferença ≤ 2%
- [ ] Suporte a pelo menos 5 condições de apoio + entrada genérica
- [ ] Relatórios completos em 3 formatos (texto, gráfico, Excel)
- [ ] Documentação dos módulos (docstrings)
- [ ] Cobertura de testes > 80%

---

## Ordem de Execução Recomendada

```
Fase 0 → Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5 → Fase 6 →
Fase 7 → Fase 10 (perdas) → Fase 8 → Fase 9 → Fase 11 → Fase 12 → Fase 13
```

**Observação:** Fase 10 (perdas) pode ser implementada em paralelo com Fase 8 e 9, pois inicialmente usamos α=0,9, β=0,75 (estimativas simplificadas).

---

## Glossário de Variáveis

| Símbolo | Significado | Unidade |
|---|---|---|
| `b`, `h` | dimensões da seção retangular | m |
| `A` | área da seção | m² |
| `I` | momento de inércia | m⁴ |
| `zt`, `zb` | módulos seccionais (sup./inf.) | m³ |
| `yt`, `yb` | distância do centroide às fibras | m |
| `e` | excentricidade do cabo | m |
| `Pj` | força de protensão aplicada (no macaco) | kN |
| `Pt` | força de protensão na transferência | kN |
| `Ps` | força de protensão em serviço | kN |
| `α`, `β`, `η` | razões `Pt/Pj`, `Ps/Pj`, `Ps/Pt` | — |
| `Msw` | momento devido ao peso próprio | kN·m |
| `Mse` | momento de serviço (combinação) | kN·m |
| `Md` | momento de cálculo (ELU) | kN·m |
| `ftt`, `ftc` | tensões limites no ato (tração/compressão) | MPa |
| `fst`, `fsc` | tensões limites em serviço | MPa |
| `Aps` | área da armadura ativa | m² |
| `dp` | distância do topo ao centroide das armaduras | m |
