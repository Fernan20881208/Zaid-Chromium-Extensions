# Parches de Chromium

`series` determina el orden. Los parches están vinculados a la revisión exacta de `chromium/revision.json`.

1. `0001-enable-extensions-core.patch`: selecciona Desktop Android como valor predeterminado de este fork. Los flags del core también están explícitos en `chromium/args.gn`.
2. `0002-android-extensions-menu.patch`: acceso a administrar extensiones en el menú Android normal; conserva el menú de acciones y los submenús existentes.
3. `0003-native-crx-picker.patch`: conecta el handler nuevo al target WebUI, añade el botón CRX, estado/error y disposición adaptable. El código del handler está en `src/`.
4. `0004-zaid-branding.patch`: nombre del producto Zaid Chromium Extensions.

ExtensionService, ExtensionRegistry, workers, APIs MV3 y carga de carpetas ya existen en esta base. Se reutilizan sus implementaciones y se comprueban sus puntos de integración; no se añaden servicios vacíos para simular soporte.

```bash
python3 scripts/apply_patches.py --source /ruta/chromium/src
```

La aplicación admite repetir una serie ya aplicada. Un cambio inesperado de contexto o un archivo overlay diferente causa un error. No se usa `patch || true`, no se silencian conflictos y no se restablece destructivamente el checkout.
