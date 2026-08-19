# 🚜 AgroRisk AI — FIAP + Sompo Seguros | Fase 5 / Sprint 3

> **MVP funcional integrado para predição de risco operacional em frotas agrícolas.**

---

## 👨‍🎓 Integrantes

| Nome | RM | GitHub |
|------|----|--------|
| Henrique Sanches Silva | RM 570527 | [@HenriqueSanchesSilva](https://github.com/HenriqueSanchesSilva) |
| João Pedro Zavanela Andreu | RM 570231 | [@zjpza](https://github.com/zjpza) |
| Kayck Gabriel Evangelista da Silva | RM 572331 | [@Kayckxz](https://github.com/Kayckxz) |
| Luis Henrique Laurentino Boschi | RM 571352 | [@lhboschi](https://github.com/lhboschi) |
| Patrick Borges de Melo | RM 574030 | [@Trickmelo](https://github.com/Trickmelo) |

**Tutora:** Sabrina Otoni  
**Coordenador:** André Godoi

---

## 📜 Descrição

O **AgroRisk AI** é um sistema de análise preditiva de risco para equipamentos agrícolas que cruza dados ambientais, operacionais e históricos para gerar alertas preventivos antes que incidentes ocorram.

Nesta **Sprint 3 (Fase 5)**, o objetivo é **integrar os módulos desenvolvidos nas Sprints anteriores em um protótipo funcional de ponta a ponta**. Os dados de telemetria entram no sistema, são persistidos em banco, processados pelo modelo de Machine Learning treinado na Sprint 2 e apresentados em uma interface simples para Operadores, Gestores de Frota e Analistas da Seguradora.

---

## 🎯 Objetivos da Sprint 3

1. **Backend integrador** em Python que orquestra o fluxo completo: entrada → banco → modelo → saída.
2. **Engenharia de dados** consolidada, com banco relacional e pipelines de ETL rastreáveis.
3. **Integração com fontes** de telemetria, ambiente e operação (simuladas ou reais).
4. **Segurança da informação**: controle de acesso, proteção das APIs/serviços e integridade dos dados.
5. **Interface simples** (dashboard em Python) exibindo scores e alertas de forma clara.
6. **Documentação** com arquitetura integrada, fluxo de dados e justificativas técnicas.

---

## 🔄 Evolução do Projeto

| Sprint | Fase | Entrega Principal |
|--------|------|-------------------|
| Sprint 1 | Fase 2 | Planejamento: personas, user stories, dataset simulado (20 registros), arquitetura da solução. |
| Sprint 2 | Fase 4 | Implementação técnica: banco SQLite, ETL, modelo Random Forest treinado, dashboard Streamlit, métricas de avaliação. |
| **Sprint 3** | **Fase 5** | **Integração dos módulos em MVP funcional (~60%): backend orquestrador, APIs, segurança e fluxo contínuo ponta a ponta.** |

Repositórios anteriores:
- Sprint 1: [challenger-sprint-1](https://github.com/HenriqueSanchesSilva/challenger-sprint-1)
- Sprint 2: [fase-4-challange](https://github.com/zjpza/fase-4-challange)

---

## 🏗️ Arquitetura da Solução

O pipeline integrado desta Sprint segue o fluxo:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌─────────────────┐
│ Fontes de Dados │────▶│ Backend Python   │────▶│  Modelo ML  │────▶│  Dashboard /    │
│ (telemetria,    │     │ (ETL + API +     │     │  Random Forest│    │  Relatório     │
│  clima, operaç.)│     │  segurança)      │     │  (Sprint 2)  │     │  (Streamlit)   │
└─────────────────┘     └──────────────────┘     └─────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │ Banco SQLite  │
                        │ (auditoria)   │
                        └───────────────┘
```

Camadas:
1. **Entrada de dados**: simulação de sensores IoT e/ou APIs de clima (INMET/Open-Meteo).
2. **Backend orquestrador**: FastAPI/Flask que valida, persiste e aciona o modelo.
3. **Banco de dados**: SQLite relacional com tabelas de telemetria, equipamentos, scores, alertas, usuários e logs de auditoria.
4. **Modelo preditivo**: Random Forest treinado na Sprint 2, reutilizado para inferência.
5. **Interface**: dashboard simples em Streamlit/relatório exibindo scores e alertas por equipamento, operação ou região.
6. **Segurança**: RBAC, logs de uso, validação de entradas e proteção básica das APIs.

---

## 📁 Estrutura de Pastas

```
fase-5-sprint-3/
├── README.md                          # Este arquivo
├── assets/                            # Imagens, diagramas e screenshots
│   └── diagrama_arquitetura.png
├── docs/                              # Documentação complementar
│   └── fluxo_integracao.md
├── src/                               # Código fonte
│   ├── api/                           # Backend integrador (FastAPI/Flask)
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── auth.py
│   │   └── models_api.py
│   ├── data/                          # ETL e pipelines
│   │   ├── generate_dataset.py
│   │   ├── feature_engineering.py
│   │   └── load_to_sql.py
│   ├── ml/                            # Modelo preditivo e inferência
│   │   ├── models/
│   │   ├── 04_predict.py
│   │   └── risk_model.pkl
│   ├── sql/                           # Schema, views, triggers e seeds
│   │   ├── 01_schema.sql
│   │   ├── 02_seed_data.sql
│   │   └── 03_views.sql
│   ├── security/                      # RBAC, logs e proteção
│   │   ├── rbac.py
│   │   └── audit_logger.py
│   └── dashboard/                     # Interface simples
│       └── app.py
├── tests/                             # Testes básicos do fluxo integrado
├── requirements.txt                   # Dependências Python
└── .gitignore
```

---

## ⚙️ Tecnologias Utilizadas

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Backend | Python + FastAPI | Leve, rápido e com documentação automática das APIs |
| Banco de dados | SQLite / SQLAlchemy | Prototipação rápida e rastreabilidade |
| ETL | Pandas, NumPy | Manipulação e validação de dados tabulares |
| Machine Learning | Scikit-learn | Reutilização do modelo Random Forest treinado |
| Dashboard | Streamlit | Interface simples e rápida para MVP |
| Segurança | JWT / RBAC / logs | Controle de acesso e auditoria básica |

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10+
- pip

### Instalação

```bash
# Clone o repositório
git clone https://github.com/zjpza/fase-5-sprint-3.git
cd fase-5-sprint-3

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt
```

### Executar o fluxo ponta a ponta

```bash
# 1. Iniciar o backend (API)
python src/api/main.py

# 2. Em outro terminal, gerar dados e fazer predições via API
python src/api/pipeline_client.py

# 3. Iniciar o dashboard
streamlit run src/dashboard/app.py
```

---

## 🛡️ Segurança

- **Autenticação**: JWT com expiração curta.
- **Autorização**: RBAC com papéis `Operador`, `GestorFrota` e `AnalistaSeguradora`.
- **Integridade**: triggers SQL que garantem consistência entre `nivel_risco` e `alerta_gerado`.
- **Auditoria**: tabela de logs registrando chamadas à API, predições e acessos.
- **Validação**: sanitização e validação de entradas antes da persistência.

---

## 📊 User Stories Atendidas

| ID | Persona | User Story |
|----|---------|-----------|
| US-01 | Operador | Receber alerta visual antes de entrar em área de alto risco. |
| US-04 | Gestora | Visualizar em mapa o status de risco de cada equipamento. |
| US-07 | Analista | Acessar histórico de alertas emitidos antes de um sinistro. |

---

## 🎥 Apresentação em Vídeo

> 🎥 **[Vídeo da Sprint 3 — fluxo integrado ponta a ponta]()** *(não listado no YouTube — link será adicionado)*

---

## 📋 Licença

Este projeto é desenvolvido para fins acadêmicos no Challenge Sprint FIAP + Sompo Seguros.

---

> **FIAP — Inteligência Artificial | Turma: 1TIAOB-2026**
