# Spec: <nombre del caso>

**Caso:** <id-del-caso> · **Escrito:** <fecha> · **Última actualización:** <fecha>

Esta página define qué significa "igual" en este caso. No se compara, cambia ni cierra nada hasta que esté completa y acordada.

## Qué comparamos

| | A (referencia) | B (candidato) |
|---|---|---|
| Sistema | | |
| Objeto (query, tabla, reporte, página) | | |
| Versión o fecha del objeto | | |
| Dueño | | |

## Qué es una fila

- **Grano:** <una fila es un ...>
- **Llave:** <columna(s) que identifican una fila>

## La medida

| | A | B |
|---|---|---|
| Nombre | | |
| Definición (en palabras) | | |
| Unidad y moneda | | |

## Alcance

- **Periodo:** <desde> a <hasta>
- **Filtros aplicados en ambos lados:** <...>
- **Fecha y hora de corte:** <el momento en que se leen ambos lados>

## Cuándo cuenta como igual

- **Tolerancia absoluta (ε_abs):** <monto>
- **Tolerancia relativa (ε_rel):** <fracción de A, p. ej. 0.0001 = 0,01 %>
- **Qué debe cuadrar:** solo el total / el total y cada periodo / el total, cada periodo y cada <dimensión>

Una diferencia se acepta cuando |residual| ≤ max(ε_abs, ε_rel × |A|).

## Quién decide

| Tipo de decisión | Aprobador (nombre o rol) |
|---|---|
| Definiciones de medidas | |
| Filtros y tipos de registro | |
| Calendario y corte | |
| Equivalencias entre códigos | |
| Permiso para cambiar archivos o sistemas | |

## Preguntas abiertas

| # | Pregunta | A quién | Fecha | Respuesta |
|---|---|---|---|---|
| 1 | | | | |
