<h1 align="center">
  <img src="assets/banner.svg" width="680" height="200" alt="tieout: evidencia, aprobación y vuelta atrás para cada cambio de datos">
</h1>

<p align="center"><a href="README.md">Read in English</a></p>

**tieout es un método para cambiar trabajo de datos con evidencia, empaquetado como una skill para agentes.** Cubre editar queries, modelos, esquemas y reportes, revisar lógica, hallar dónde dos versiones no coinciden y mover queries entre motores SQL.

Cuando un agente hace ese trabajo, tieout le exige mostrar su evidencia, respaldar antes de editar y preguntar a una persona con nombre antes de decidir una regla de negocio. Su verificación central es el *tie-out* (cuadre): demostrar que dos versiones de la misma cifra coinciden, o explicar con exactitud por qué no, con un script y no con una corazonada.

Sigue el formato [Agent Skills](https://agentskills.io), así que los agentes que lo lean pueden usarla (solo se ha probado Claude Code), y no depende de una base de datos ni de una herramienta de BI concretas.

> [!WARNING]
> Borrador temprano, probado con datos sintéticos y solo en Claude Code. Mira el [estado](#estado).

## Cómo es una respuesta

Toda respuesta que toca o analiza un objeto termina con las mismas cuatro líneas. Ejemplo, tras un cambio aprobado que excluye las cuentas TEST de una query de KPI mensual (de ahí que los totales cambien):

```
Backup:      tieout/backups/kpi_query.sql.20261030T0915
Checked:     la query se analiza sin error; totales antes y después: 1.204,50 y 1.171,00
Not checked: que account_type exista en la tabla del almacén [assumption]
Pending:     que la jefa de Finanzas confirme que las cuentas TEST nunca cuentan
```

## Cuándo usarla

- "Estas dos cifras no coinciden"
- "Traduce esta query a BigQuery"
- "Copié este reporte para otro equipo; revísalo antes de publicarlo"
- "Voy a cambiar cómo se define esta métrica"

Se invoca con `/tieout:tieout` y la tarea. Para investigar sin cambiar nada, dilo: `/tieout:tieout solo lectura, no crees ni cambies archivos: ¿por qué estas dos queries devuelven totales distintos?`

Funciona mejor con contexto. Adjunta lo que tengas (diccionario de datos, esquema, documentación, una query de ejemplo) y el agente redacta `tieout/context.md` a partir de eso, citando el archivo de cada línea; sin nada que adjuntar, hace unas pocas preguntas. Ese archivo se queda en tu proyecto: añade `tieout/context.md` a tu `.gitignore` si es privado.

## Instalación

**Claude Code**
```
claude plugin marketplace add sorenriosdev/tieout-skill
claude plugin install tieout@tieout-skill
```

**Codex**: mira [docs/codex.es.md](docs/codex.es.md). **Otros agentes**: copia `skills/tieout/` en la carpeta de skills del agente y pídela por nombre. Los scripts necesitan Python 3.11 o superior y `pip install sqlglot duckdb` para el trabajo con SQL.

## Cómo funciona

Cada tarea empieza eligiendo un peso y diciendo cuál:

| Peso | Cuándo | Qué escribe |
|---|---|---|
| **light** | Un objeto, y el cambio está indicado o ya aprobado | Un respaldo, el cambio, una línea en un registro de decisiones |
| **decision** | Una regla tiene dos lecturas, o la elección es de otra persona | Una propuesta con la pregunta y las opciones. No se cambia nada |
| **full** | Dos versiones no coinciden, o es un cuadre, una migración o una auditoría | Spec, línea base, hallar la diferencia, proponer, aprobar, aplicar, verificar, registrar |

Un cuadre se cierra con Δ = B − A = Σ efectos + residual. A es la cifra de referencia y B la candidata. Los efectos son las diferencias que mediste; el residual es lo que dejan sin explicar y debe caer dentro de una tolerancia que acordaste de antemano (cuánta diferencia cuenta como igual). Lo comprueba un script, no el agente. Las reglas que hayas aprobado van en `tieout/rules.local.md`; la skill las aplica y trata una regla sin aprobador como una pregunta.

| Playbook (`skills/tieout/playbooks/`) | Para qué |
|---|---|
| `reconcile` | Cuadrar dos cifras que deberían coincidir |
| `trace` | Hallar qué campo o paso hace que una cifra difiera de una referencia |
| `logic-review` | Comparar dos versiones de una query, con o sin acceso a la base |
| `migrate-sql` | Mover queries entre motores SQL |
| `clone-bi` | Copiar o revisar un reporte (adaptadores opcionales para archivos de Power BI y Tableau) |
| `change-schema` | Añadir, renombrar, cambiar el tipo o eliminar una tabla o columna |

## Qué no hace

- No decide reglas de negocio: si una regla tiene dos lecturas, escribe la pregunta con opciones y evidencia y espera a un aprobador con nombre.
- No estima impacto financiero ni prescribe soluciones.
- No hace a mano lo que debería hacer una herramienta: si falta sqlglot o un cliente de base de datos, lo dice y se detiene o declara un modo reducido.

## Estado

Trece escenarios sintéticos, dos o tres ejecuciones cada uno: puntaje medio **0,90 con tieout y 0,56 sin ella**, con un coste de alrededor de 1,8 veces. Ayudó más donde un agente se habría saltado un paso (nombrar una herramienta faltante, respaldar, cerrar con un script, preguntar en vez de elegir una regla) y nada en la comprobación de una columna inexistente. La skill y los escenarios se ajustaron a la vez, así que tómalo como una primera señal: [resultados](evals/RESULTS-2026-10-26.md).

Aún sin hacer:
- Ninguna ejecución con datos reales de Power BI, Tableau o un almacén (esos adaptadores son opcionales y se probaron con archivos armados a mano)
- SQL en motores distintos de DuckDB, y agentes distintos de Claude Code
- La CI todavía no pasa

El catálogo de comprobaciones (23 causas frecuentes de un descuadre, la mayoría con una prueba SQL) sale de la experiencia de una persona. Ejecutarlo sobre tu propio trabajo y reportar lo que se le escapa es la forma más rápida de mejorarlo: mira [docs/field-test.es.md](docs/field-test.es.md). Pendientes: [ROADMAP.md](ROADMAP.md).

## Licencia

[MIT](LICENSE), © 2026 sorenriosdev.
