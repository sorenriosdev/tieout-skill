# Usar tieout con Codex

*[Read in English](codex.md)*

`tieout` es una carpeta estándar de Agent Skills (`SKILL.md` más `scripts/`, `references/`, `assets/`). La documentación de Codex de OpenAI (leída el 2026-10-29) dice que Codex carga skills con esa forma. **No se ha ejecutado en Codex**: aquí no había Codex para probarlo. Toma esta página como el camino esperado y avisa de lo que difiera.

## Instalar sin clonar el repositorio

Instala desde una etiqueta de versión (por ejemplo `v0.1.0`, que se crea al publicar) y no desde `main`, para que un cambio posterior no altere lo que instalaste. Un repositorio privado necesita credenciales en esa máquina (`gh auth login`, o un token en `GITHUB_TOKEN`); uno público no.

**Opción A: el instalador de Codex.** La página de OpenAI dice que puedes pedirle al instalador que descargue skills de otros repositorios. En Codex:

```
$skill-installer install https://github.com/sorenriosdev/tieout-skill/tree/v0.1.0/skills/tieout
```

Descripciones de terceros del instalador (no la página de OpenAI) dicen que acepta una URL de árbol o `--repo owner/repo --path skills/tieout`, instala en `$CODEX_HOME/skills` (por defecto `~/.codex/skills`) y se niega a sobrescribir una carpeta existente. Quien lo instaló así reportó el mismo destino. La página de OpenAI señala `~/.agents/skills` como ubicación del usuario y no menciona `~/.codex/skills`. Por eso, tras instalar, ejecuta `/skills`; si `tieout` no aparece, mueve la carpeta a `~/.agents/skills/tieout` y reinicia Codex.

**Opción B: solo git, sin clon completo.**

```
git clone --depth 1 --filter=blob:none --sparse --branch main https://github.com/sorenriosdev/tieout-skill.git /tmp/tieout-src
git -C /tmp/tieout-src sparse-checkout set skills/tieout
mkdir -p ~/.agents/skills && cp -r /tmp/tieout-src/skills/tieout ~/.agents/skills/tieout
rm -rf /tmp/tieout-src
```

**Opción C: la CLI abierta `skills`** (herramienta de terceros que necesita npm; revisa la política de tu empresa sobre paquetes de terceros). Su documentación pública muestra:

```
npx skills add sorenriosdev/tieout-skill --list
npx skills add sorenriosdev/tieout-skill --skill tieout -a codex -g
```

Revisa antes `npx skills add --help`: las opciones y los agentes soportados cambian entre versiones.

Para actualizar, borra `~/.agents/skills/tieout` e instala de nuevo. Para usarla solo en un repositorio, cópiala a `<repo>/.agents/skills/tieout`.

La skill necesita Python 3.11 o superior. `scripts/bi_fields.py` usa solo la biblioteca estándar; el resto se instala con `pip install sqlglot duckdb` si tu entorno lo permite (los scripts dicen qué falta y se detienen).

**Windows (PowerShell), aún sin ejecutar en Windows:** usa `py` para Python, entrecomilla las rutas con espacios e instala con `py -m pip install --user sqlglot==30.21.0 duckdb==1.5.6`. Los scripts escriben UTF-8 y funcionan con una página de códigos antigua en la consola. La propia skill comprueba qué paquetes faltan y dice qué funciones quedan reducidas; no los instales en silencio.

**Qué hacen los scripts:** no hacen llamadas de red ni lanzan otros programas. El único archivo que puede escribir cualquiera de ellos es el archivo nuevo que le pases a `transpile_sql.py --out`, y se niega a sobrescribir.

## Prueba de humo (tres minutos, sin datos)

1. Reinicia Codex y ejecuta `/skills`: debe aparecer `tieout`.
2. En una terminal: `python3 ~/.agents/skills/tieout/scripts/waterfall.py --help`.
3. En Codex: `$tieout dime qué herramientas tienes para trabajo con SQL y en qué modo estás`. Debe ejecutar `check_capabilities.py`, nombrar lo que falta y declarar `code-only`, `one-system` o `both`.

## Usar

- Explícito: escribe `$tieout` (o `/skills` y elígela), seguido de la tarea. Por ejemplo: `$tieout el desglose por Canal de esta query no coincide con el reporte de referencia; el total cuadra`.
- Implícito: Codex puede elegirla por la descripción cuando la tarea encaja. No cuentes con eso, sobre todo en investigaciones de solo lectura: en las pruebas con Claude Code un agente que pensó "solo lectura" no aplicó la skill. Nómbrala.
- Los scripts están en la carpeta de la skill (`scripts/`). La skill los nombra relativos a su propia carpeta; si el agente no los encuentra, dile dónde la copiaste.

## Si Codex no carga la skill

Codex también lee `AGENTS.md`. Añade `adapters/AGENTS.md` (las 12 reglas, los tres pesos y el bloque de cierre, unas 470 palabras) al `AGENTS.md` de tu proyecto. Pierdes los playbooks y scripts pero conservas la disciplina. Sin la carpeta de la skill el agente no puede ejecutar los scripts; si puede leer archivos, indícale una copia de `skills/tieout/`.

## Qué comprobar la primera vez

- La lista de skills de Codex es limitada (alrededor del 2 % de la ventana de contexto, u 8.000 caracteres si no se conoce). Codex acorta primero las descripciones y puede omitir skills con un aviso. Si `tieout` no aparece, quita otras skills o sube `skills.max_context_tokens`.
- El sandbox y las aprobaciones de Codex deciden si puede ejecutar `python3 scripts/...` y escribir la carpeta `tieout/`. Una configuración de solo lectura sirve para investigar: la skill no crea archivos en modo `code-only` ni cuando se le dice que es de solo lectura.
- Revisa lo que imprime antes de fiarte: cada afirmación debe llevar etiqueta (`[verified: ...]`, `[assumption]`) y cada respuesta debe terminar con Backup, Checked, Not checked y Pending.

## No cubierto aquí

No se incluyen plugins de Codex ni `agents/openai.yaml` (interfaz y política de invocación). Los hooks, líneas de estado y otras partes propias de cada agente quedan fuera.
