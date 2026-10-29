# Probar tieout en trabajo real

*[Read in English](field-test.md)*

Esta guía sirve para probar la skill en tu propio trabajo de datos y medir si ayuda, sin exponer nada. Supone Claude Code; para otros agentes, mira la nota final.

## Antes de empezar

1. **Instala desde la rama `next`**, no `main`: `claude plugin marketplace add sorenriosdev/tieout-skill#next` y luego `claude plugin install tieout@tieout-skill`. Si el repositorio es privado, la máquina necesita credenciales de git que funcionen sin interacción (en GitHub, `gh auth login` y `gh auth setup-git`).
2. **Trabaja sobre copias.** Apunta al agente a un clon del proyecto o a un entorno de desarrollo. La skill pide permiso antes de escribir, pero no te apoyes solo en eso mientras la evalúas.
3. **Solo lectura primero.** Haz las tareas de abajo en orden; las tres primeras no cambian nada.
4. **Trata las salidas como internas.** Los inventarios y hallazgos nombran tus tablas, campos y valores reales. No los pegues en issues públicos. Antes de publicar algo que escribiste al probar, revísalo contra tu propia lista de términos que no deben salir de la empresa.

## Cinco tareas, en orden

| # | Tarea | Por qué esta | ¿Cambia algo? |
|---|---|---|---|
| 1 | Dale dos versiones de una query real (sin acceso a la base) y pregunta por qué difieren las cifras | Prueba el análisis `code-only`: ¿lista las diferencias reales, da pruebas ejecutables en la respuesta y evita nombrar una causa? | No |
| 2 | Ejecuta tú `python skills/tieout/scripts/bi_fields.py pbir <tu>.Report` sobre un PBIP real (o `twb` sobre un libro) | Prueba el inventario contra un reporte real, que este repositorio no ha visto | No |
| 3 | Pídele cuadrar dos cifras reales cuya respuesta ya conoces | Prueba `reconcile` en un caso que puedes calificar | No (trabaja sobre copias que le des) |
| 4 | Un cambio pequeño y aprobado sobre una copia de una query | Prueba el camino ligero: respaldo, cambio, fila en el registro, "Not checked" honesto | Sí, en la copia |
| 5 | Traducir una query entre tus dos motores | Prueba `migrate-sql`: ¿señala lo que difiere y pide la prueba de equivalencia? | Solo escribe un archivo nuevo |

## Qué registrar por tarea

Una fila por tarea, una vez con la skill y otra sin ella (mismo prompt, sesión nueva):

| Medida | Cómo |
|---|---|
| Hallazgos correctos | Cuántas diferencias o defectos reales reportó y tú confirmas |
| Hallazgos falsos | Cuántos reportó que no son reales |
| Omitidos | Reales que tú conoces y no reportó |
| Decisiones que te dejó y eran tuyas | Cuenta las buenas preguntas |
| Decisiones que tomó y no le tocaban | Cualquier elección silenciosa de una regla |
| Afirmaciones sin verificar | Frases sin etiqueta, o "funciona" sin comprobación |
| Coste y tiempo | `/cost` en la sesión; minutos reales |
| ¿Lo pondrías en producción? | Sí / con cambios / no |

Los escenarios de `evals/` muestran el comportamiento esperado con datos sintéticos. Midieron aproximadamente el doble de coste que trabajar sin la skill en tareas pequeñas, con mejor proceso (respaldos, etiquetas, decisiones diferidas), no con mejor detección de los defectos de fondo. Comprueba si eso se cumple en tu trabajo.

## Qué contaría como fallo

- Cambia un archivo sin respaldo, o publica algo.
- Elige una regla de negocio por ti.
- Presenta una traducción hecha a mano como lista.
- Nombra una causa como probable sin una prueba.
- El script de inventario marca como faltante un campo que existe, o no marca uno que no existe: envía la estructura (anonimizada) para corregir el lector.
- Da diez pasos para un cambio de una línea.

## Otros agentes

La skill es una carpeta `SKILL.md` estándar (`skills/tieout/`) y debería cargarse en agentes que lean Agent Skills. Para agentes que solo leen un archivo de reglas, `adapters/AGENTS.md` lleva las reglas sin el método. Ninguno se ha probado fuera de Claude Code.
