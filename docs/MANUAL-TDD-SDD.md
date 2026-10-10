# Manual de Operación — Ciclo SDD (OpenSpec) + TDD (tdd-cycle) + Deuda Heredada

## 1. Mapa del sistema
- Flows (.agent/workflows/opsx-*.md) = puertas que TÚ invocas desde el chat de Antigravity (modo Agent).
- Skills (.agent/skills/*) = procedimiento que el agente ejecuta o que otro flow invoca
  (archive→sync, strangle→propose, bugfix→update, apply→tdd-cycle). Nunca invocar skill y flow gemelos a la vez.
- Invariantes (AGENTS.md 1-15) = disciplina de ejecución heredada por toda la sesión.
- config.yaml = restricciones permanentes del proyecto (sin casos de uso).

## 2. Ciclo de vida completo
  [bug viejo] ──► /opsx-bugfix ──► commit fix + métrica
  [change nuevo] ──► /opsx-explore ──► /opsx-propose ──► /opsx-triage ──┬─ R1 ─► /opsx-apply + tdd-cycle (fases 1-6)
                                                                       ├─ R4/R5 ─► [/opsx-characterize] ─► /opsx-apply --incremental + legacy-guard
                                                                       ├─ R3 ─► /opsx-strangle
                                                                       └─ R2 ─► /opsx-bugfix
  Todo camino termina en: Fases 4→5→6 ─► /opsx-sync ─► /opsx-archive (como COMPUERTA, no trámite)

## 3. Tabla de triage (primera regla que matchea gana)
R1 GREENFIELD: todos los archivos nuevos → flujo puro actual.
R2 BUG: defecto contra comportamiento vigente → bugfix.
R3 STRANGLE: legacy con deuda sobre umbrales Y reescritura de comportamiento → strangle.
R4 LEGACY-TOUCH: legacy sin caracterización → characterize + apply --incremental + legacy-guard.
R5 LEGACY-COVERED: legacy caracterizado → apply --incremental + legacy-guard.

## 4. Guion de operación (un mensaje por etapa; revisar entre etapas)
M1: Procede con /opsx-triage <change>
    → esperas tabla de routing; ella dice qué mensaje sigue.
M2 (solo R4/R5 sin baseline): Procede con /opsx-characterize <módulos tocados> — comportamiento
    ACTUAL, tags @legacy-baseline y @known-bug, suite verde contra código intocado, commit baseline.
M3: Procede con /opsx-apply <change> aplicando estrictamente el skill tdd-workflows-tdd-cycle
    [si R4/R5: en modo --incremental y con legacy-guard: tras cada GREEN y REFACTOR ejecuta la suite
    @legacy-baseline; si flipa, STOP y pregúntame].
    Aplica compuerta Fase 2 (RED): tests primero, fallo legítimo en terminal antes de tocar producción.
    Commit del estado RED antes de implementar. Luego Fase 3 GREEN (suite completa + cobertura 80/75/100).
    NO termines en GREEN: Fase 4 REFACTOR, Fase 5 integración RED→GREEN, Fase 6 edge/stress + review.
    Commit por cada compuerta.
M4: Procede con /opsx-sync <change> y luego /opsx-archive <change>. Solo si DoD completa;
    si algo falla NO archives: rutéame a /opsx-bugfix o /opsx-update según corresponda.
M-bug (en cualquier momento): Procede con /opsx-bugfix "<descripción>" — test de regresión primero,
    fallo legítimo en terminal antes de tocar producción.

## 5. Compuertas y evidencia
| Fase | GATE | Evidencia | Commit |
|---|---|---|---|
| RED | todos fallan por la razón correcta | output terminal | RED |
| GREEN | suite completa verde + cobertura 80/75/100 | output + reporte | GREEN |
| REFACTOR | verde tras cada cambio + triggers medidos | output + métricas | REFACTOR |
| baseline | verde contra código intocado | output terminal | baseline |
| INTEGRATION (F5) | integración verde | output terminal | INTEGRATION |
| HARDENING (F6) | edge/stress + review críticos aplicados | review report | HARDENING |
| parity (strangle) | caracterización pasa contra lo nuevo | output terminal | routing |
| CIERRE | DoD completa | checklist §7 | sync+archive |

## 6. Protocolo de bugs
Bug → ¿cambia spec acordada? SÍ → /opsx-update-change primero. NO → RED (regresión) → GREEN mínimo →
REFACTOR condicional → commit fix → métrica escape +1. Si toca seguridad/protocolos: spec+design
aprobado antes (invariante 14). Si vive en legacy sin baseline: characterize antes de fijar.

## 7. Definition of Done (por change)
[ ] Cada task pasó RED→GREEN→REFACTOR con evidencia. [ ] Commit por compuerta.
[ ] Cobertura 80/75/100 reportada por fase. [ ] Triggers de refactor medidos.
[ ] Suite unit < 5 s verde; integración y caracterización verdes.
[ ] Fases 5 y 6 completas. [ ] Ningún test modificado para pasar.
[ ] legacy-guard sin flips no decididos. [ ] sync + archive ejecutados. [ ] Métricas registradas.

## 8. Métricas (registrar en cada archive)
Tiempo por fase · ciclos test-implementación · progresión de cobertura · frecuencia de refactoring ·
defect escape rate · legacy ratio · % legacy caracterizado · @known-bug cerrados.

## 9. Deuda heredada (estrategia)
No refactor masivo. (a) Sweep inicial único: inventario legacy sin caracterización ordenado por
(contacto reciente × deuda). (b) Boy-scout: todo change que toque legacy pasa por triage→characterize.
(c) Strangler planificado para top-3 módulos calientes (changes migrate-*).

## 10. Failure Recovery
STOP → identificar fase violada → rollback al último commit de compuerta → retomar desde la fase
correcta → documentar lección en notes del change.

## 11. Instalación del kit
1. Copiar .agent/workflows/*.md del kit a <repo>/.agent/workflows/.
2. Agregar el contenido de AGENTS-append.md al final de <repo>/AGENTS.md.
3. Aplicar patches/config-yaml-patch.md (única adición al bloque context).
4. Guardar este manual en <repo>/docs/MANUAL-TDD-SDD.md.
5. Reiniciar sesión de Antigravity para reindexar workflows y skills.