# Notas de campo: medir tieout en el trabajo sin sacar material del trabajo

*[Read in English](field-notes.md)*

El objetivo es saber si la skill ayuda y cómo mejorarla, sin pasar a este repositorio nada que pertenezca a un empleador o a un cliente.

## Reglas

1. **El material en bruto se queda donde se hizo.** Queries, dashboards, archivos del modelo, resultados, transcripciones del agente, nombres y cifras se quedan en los sistemas del empleador.
2. **Lo que sacas es una nota que escribes tú,** con tus palabras, sobre el *patrón*, con nombres inventados. Sin copiar y pegar, sin capturas, sin paráfrasis tan cercana que identifique a un cliente, una tabla o una cifra.
3. **Revisa antes de sacar nada.** Mantén una lista de términos que no deben salir (nombres de clientes, sistemas, tablas y personas, cifras), fuera de cualquier repositorio, y escanea la nota:

   `TIEOUT_BANNED_TERMS=/ruta/a/tu-lista.txt python3 dev/check_banned_terms.py --file notas.md`

   El verificador imprime la línea y el número del término, nunca el término, y sale con 1 si encuentra alguno. Solo detecta lo que está en tu lista: es una red de seguridad, no una revisión.
4. **Los fixtures son inventados.** Los escenarios y ejemplos de este repositorio son ficticios; uno nuevo se escribe a partir del patrón, nunca del caso original.
5. **Desarrolla en otro sitio.** Usa la skill en el trabajo; cambia la skill en tu tiempo, con tu equipo y tus cuentas.

## Una fila por tarea

Sobre todo categorías y conteos, para que haya poco que se pueda filtrar. Rellena las dos últimas con tus palabras.

| Campo | Ejemplo |
|---|---|
| Fecha | |
| Tipo de tarea | cuadre / revisión de lógica / migración / traza / clonado / cambio de esquema |
| Agente y modelo | |
| Skill usada | explícita `$tieout` / sola / no |
| Resultado | causa encontrada / parcial / no encontrada / equivocada |
| Minutos y turnos (aproximado) | |
| ¿Trazó el campo antes de cualquier teoría? | sí / no |
| Afirmaciones sin prueba (conteo) | |
| Preguntas que dejó a una persona y eran suyas (conteo) | |
| Reglas de negocio elegidas en silencio (conteo) | |
| Salidas de scripts que ayudaron | `bi_fields model`, `sql_review diff`, ninguna |
| Patrón aprendido, con nombres inventados | |
| Cambio sugerido a la skill | principio / playbook / script / descripción |

Compara una tarea hecha con la skill con otra parecida hecha sin ella, cuando la tengas. Dos filas son una anécdota; veinte, una señal.

## Traer una lección a casa

Una lección útil para la skill es un *patrón*: "un reporte tomó un campo de clasificación de una tabla de dimensión mientras la referencia lo tomaba de la tabla de hechos; el total cuadraba y el desglose no". Escríbelo con tablas inventadas y sin cifras. Si no puedes escribirlo sin los nombres originales, aún no está listo para salir.
