# Propuesta <NNN>: <título corto>

**Caso:** <id-del-caso> · **Escrita:** <fecha> · **Estado:** propuesta | aprobada | rechazada | reemplazada
**Reemplaza a:** <número de propuesta, si aplica> · **Reemplazada por:** <número de propuesta, si aplica>

## Qué y por qué

- **Objeto a cambiar:** <archivo, query, tabla, reporte, y su versión actual>
- **Hallazgo que atiende:** <enlace a la entrada de findings.md>
- **Tipo de cambio:** técnico equivalente | regla de negocio | suposición

## El cambio

Antes:

```
<texto o lógica actual>
```

Después:

```
<texto o lógica propuesta>
```

## Si es una regla de negocio: la pregunta

<La pregunta, en palabras sencillas.>

| Opción | Qué significa | Evidencia | Etiqueta |
|---|---|---|---|
| A | | | |
| B | | | |

Solo el aprobador elige. No se aplica nada mientras esté abierta.

## Resultado esperado

- **Diferencia esperada después del cambio:** <número> en <medida>
- **Se compara contra:** base <total de A según la Spec>, tolerancia max(ε_abs, ε_rel × |base|) de la Spec
- **Cómo se medirá:** <query o peldaño de la escalera>

## Vuelta atrás

- **El respaldo quedará en:** <ruta>
- **Para revertir:** <pasos>

## Aprobación

| | Quién | Fecha |
|---|---|---|
| Regla aprobada por (solo reglas de negocio) | | |
| Permiso para aplicar dado por | | |

## Resultado (después de aplicar)

- **Aplicada el:** <fecha> · **Respaldo en:** <ruta>
- **Diferencia real:** <número> · **Esperada contra real:** COINCIDE | NO COINCIDE (salida de waterfall.py compare en la entrada <n> del registro de evidencia)
