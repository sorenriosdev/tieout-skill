# tieout

*[Read in English](README.md)*

Una skill abierta para agentes de IA que trabajan con datos. Cualquier cambio a una query, modelo, esquema, pipeline o dashboard se hace con evidencia fechada, aprobación explícita y vuelta atrás. Cuadrar cifras entre dos versiones de lo mismo (una migración de motor, un refactor de lógica, un cambio de definición de una métrica, una auditoría) es la verificación central.

Está pensada para ingenieros de datos, analistas, desarrolladores de BI e ingenieros de IA. No compite con las herramientas que ya existen: le dice al agente cuándo usarlas y qué hacer cuando faltan.

## Qué hace

Cinco playbooks: `reconcile` (cuadrar cifras), `logic-review` (comparar queries, con o sin datos), `migrate-sql` (entre motores), `clone-bi` (reportes de Power BI y Tableau) y `change-schema` (expandir y contraer). Cada tarea empieza eligiendo un peso: **light** (un cambio aprobado: respaldo, cambio, una fila en el registro), **decision** (una regla con dos lecturas: una pregunta, sin cambios) o **full** (el ciclo completo).

- Declara un modo de trabajo según el acceso disponible: `code-only`, `one-system` o `both`.
- Sigue un ciclo con compuertas: ninguna fase empieza sin el artefacto de la anterior (Spec → línea base → localizar → proponer → aprobar → aplicar → verificar → registrar).
- Localiza diferencias con una escalera (total → periodo → dimensión → llave → fila → expresión) y un catálogo de 22 hipótesis, casi todas con un test SQL.
- Cierra un caso solo cuando un script muestra que Δ = B − A se explica con efectos medidos más un residual dentro de la tolerancia acordada en la Spec.
- Etiqueta cada afirmación como verificada, decidida por alguien, dato del usuario o suposición.

## Qué no hace

- No decide reglas de negocio. Cuando una regla tiene dos lecturas plausibles, formula la pregunta con opciones y evidencia, y espera a un aprobador nombrado.
- No estima impacto financiero ni prescribe soluciones.
- No hace a mano lo que debe hacer una herramienta. Si falta sqlglot o un cliente de base de datos, lo dice y se detiene o declara un modo reducido.

## Qué es núcleo y qué es opcional

El método (modos, ciclo con compuertas, 12 principios, etiquetas de evidencia, playbooks) no depende de ninguna herramienta. Los scripts de SQL (`sql_review`, `transpile_sql`, `u1_query`, `schema_impact`, `waterfall`) solo necesitan Python y sqlglot. `scripts/bi_fields.py` y `playbooks/clone-bi.md` son **adaptadores opcionales** para los formatos de archivo de Power BI (PBIR, TMDL) y Tableau (`.twb`), construidos con la documentación pública de esos fabricantes. Sin un adaptador, el agente lee los archivos de definición o consulta un conector, y etiqueta lo que leyó.

## Estado: borrador temprano

Qué se ha comprobado y qué no:

- **Comportamiento.** Trece escenarios sintéticos en Claude Code, un modelo, dos o tres ejecuciones por brazo. La skill sacó 0,90 de media frente a 0,56 sin ella, con un coste de aproximadamente 1,8 veces. Ayudó más en la honestidad ante herramientas faltantes, los respaldos, los cuadres cerrados por script y en preguntar en vez de elegir una regla de negocio. No ayudó en la comprobación de una columna inexistente, y ni siquiera se activó en una investigación de solo lectura (la descripción se cambió después y ese cambio no está medido). Detalles, límites y cada cambio de grader: [evals/RESULTS-2026-10-26.md](evals/RESULTS-2026-10-26.md). Los escenarios y la skill se ajustaron a la vez, así que tómalo como una primera señal.
- **Datos reales: ninguno.** `bi_fields.py` (Power BI PBIR y Tableau) se escribió a partir de los esquemas publicados por Microsoft y la estructura de `.twb`, y se probó solo con archivos armados a mano. Los tests SQL del catálogo se ejecutaron en DuckDB, no en BigQuery, Databricks ni otros motores; H17 tiene un literal de intervalo que sqlglot no adapta bien a BigQuery. La salida de `transpile_sql.py` se vuelve a leer sin error, pero no se ha ejecutado en un motor real.
- El catálogo de hipótesis sale de la experiencia de campo de una sola persona y no lo ha revisado nadie más.
- Solo se probó Claude Code. La skill sigue el formato abierto [Agent Skills](https://agentskills.io) y `adapters/AGENTS.md` lleva las reglas para agentes sin soporte de skills; ninguno se ha ejecutado en otro sitio.
- La primera ejecución de la CI falló en Python 3.10 porque el validador de formato exige 3.11 o superior; el flujo se corrigió (3.11 a 3.13, dependencias fijadas) y no se ha vuelto a ejecutar. Las pruebas locales se hicieron en Python 3.12 y 3.14; 3.11 se comprobó solo en la gramática.

Mira [ROADMAP.md](ROADMAP.md) para lo que falta y [docs/field-test.es.md](docs/field-test.es.md) para probarla en tu trabajo.
## Instalación

Claude Code, como plugin (`#next` es la rama en prueba; quítalo cuando `main` tenga la versión que quieras):

```
claude plugin marketplace add sorenriosdev/tieout-skill#next
claude plugin install tieout@tieout-skill
```

Otros agentes que lean Agent Skills: copia `skills/tieout/` en la carpeta de skills del agente.

Los scripts incluidos necesitan Python 3.11 o superior. `sqlglot` hace falta para trabajar con dialectos y `duckdb` para ejecutar los tests y el ejemplo:

```
pip install sqlglot duckdb
```

Las pruebas y la CI usan sqlglot 30.21.0 y DuckDB 1.5.6 (`requirements-dev.txt`), elegidas por ser versiones maduras y no las más recientes.

## Cómo usarla

En Claude Code la skill se activa sola ante tareas como "estas dos cifras no cuadran", "traduce esta query a BigQuery" o "revisa este reporte antes de publicarlo". Para forzarla: `/tieout:tieout` seguido de la tarea, por ejemplo `/tieout:tieout compara estas dos versiones de la query; no tengo acceso a la base`. En agentes que leen Agent Skills: copia `skills/tieout/` en la carpeta de skills del agente y pídela por nombre. Codex: mira [docs/codex.es.md](docs/codex.es.md) (sin probar).

Para una investigación de solo lectura, dilo en el prompt; la skill entonces no crea archivos y pone todo en la respuesta.

## Tus propias reglas

Pon las reglas que tu equipo ha aprobado en `tieout/rules.local.md` dentro de tu proyecto, como una tabla de regla, alcance, aprobador y fecha. Una regla sin aprobador o sin fecha se trata como suposición: no se aplica y se plantea como pregunta. La skill lee ese archivo y aplica esas reglas como decididas. Nunca escribe en él.

## Estructura del repositorio

| Ruta | Qué es |
|---|---|
| `skills/tieout/SKILL.md` | Punto de entrada: modos, ciclo, tipos de cambio, enrutado |
| `skills/tieout/references/` | Principios del núcleo, escalera, etiquetas de evidencia, flags de detección, catálogo de hipótesis |
| `skills/tieout/playbooks/` | `reconcile`, `logic-review`, `migrate-sql`, `clone-bi`, `change-schema` |
| `skills/tieout/assets/templates/{en,es}/` | Spec, propuesta de cambio, registro de decisiones, registro de evidencia, hallazgos |
| `skills/tieout/scripts/` | `check_capabilities`, `waterfall`, `u1_query`, `sql_review`, `transpile_sql`, `bi_fields`, `schema_impact` |
| `examples/` | Caso de cuadre sintético y proyecto sintético de Power BI |
| `adapters/AGENTS.md` | Reglas compactas para agentes sin soporte de skills (generado desde `SKILL.md`) |
| `docs/field-test.es.md` | Cómo probarla en trabajo real y qué medir |
| `evals/` | Escenarios de comportamiento para `claude plugin eval`, y sus resultados |
| `tests/` | Tests del catálogo y de los scripts |

## Compruébalo tú

```
python tests/test_hypotheses.py
python tests/test_scripts.py
python examples/reconcile-synthetic/run_example.py
claude plugin eval . --scaffold --allow-tools Write Edit Bash   # ejecuciones reales del modelo, con coste
```

## Licencia

[MIT](LICENSE) © 2026 sorenriosdev
