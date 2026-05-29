# Concreto Protendido — Dimensionamento de Vigas Retangulares

Ferramenta em Python para dimensionamento de vigas de concreto protendido com seção retangular, baseada na **NBR 6118:2014**.

## Escopo

- Seções retangulares (b × h)
- Qualquer condição de apoio (biblioteca de casos + entrada genérica)
- Concretos até **C50**
- Aços CP-190 RB (3 e 7 fios)
- Cobertura: Capítulos 1 a 11 do manual de Torii (2020)

## Funcionalidades

- Pré-dimensionamento da seção
- Diagrama de Magnel
- Definição do perfil do cabo
- Cálculo de perdas (imediatas e progressivas)
- Verificação ELU à flexão
- Verificações ELS (ELS-D, ELS-DP, ELS-DEF)
- Relatórios em texto, gráficos e Excel

## Estrutura

```
prestressed_beam/
├── src/                   # Módulos principais
├── tests/                 # Testes unitários e de integração
├── examples/              # Exemplos de uso
├── docs/                  # Documentação
├── tasks.md               # Lista de tarefas de implementação
├── requirements.txt       # Dependências
└── README.md              # Este arquivo
```

## Instalação

```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

## Uso Básico

```python
from src.beam import PrestressedBeam
from src.geometry import RectangularSection
from src.materials import Concrete, PrestressSteel
from src.supports import SimplySupported
from src.loads import Loads

# Definir viga
section = RectangularSection(b=0.30, h=0.80)
support = SimplySupported(L=10.0)
concrete = Concrete(fck=50, fckj=30)
steel = PrestressSteel('CP-190 RB', diameter=15.2)
loads = Loads(gk=20, qk=25, usage='comercial')

# Criar e dimensionar
beam = PrestressedBeam(section, support, concrete, steel, loads,
                       prestress_level='completa',
                       prestress_type='post-tension')
beam.design()

# Resultados
beam.report()
beam.plot_all()
beam.export_excel('resultado.xlsx')
```

## Referências

- NBR 6118:2014 — Projeto de estruturas de concreto - Procedimento
- Torii, A. J. (2020). *Concreto Protendido - Notas de Aula*. UNILA.
- Bhatt, P., MacGinley, T. J., Choo, B. S. (2014). *Reinforced Concrete Design to EUROCODES*.
- Bastos, P. S. (2019). *Fundamentos do Concreto Protendido*. Apostila UNESP.
