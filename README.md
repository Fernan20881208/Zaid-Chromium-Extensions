# Zaid Chromium Extensions

Fork experimental de Chromium Android ARM64, basado en **153.0.8010.36**, con la integración **Desktop Android** de Chromium y un selector nativo de archivos CRX.

[Validación](https://github.com/Fernan20881208/Zaid-Chromium-Extensions/actions/workflows/bootstrap.yml) · [Compilar APK](https://github.com/Fernan20881208/Zaid-Chromium-Extensions/actions/workflows/build-arm64.yml) · [Releases](https://github.com/Fernan20881208/Zaid-Chromium-Extensions/releases)

## Estado real

Hay código, cuatro parches aplicables, configuración ARM64, herramientas de descarga/compilación/empaquetado y workflows. **Todavía no hay una compilación completa ni pruebas en un dispositivo que demuestren compatibilidad total.** Una validación de parches correcta no significa que exista un APK.

La versión base es estable; el soporte Desktop Android de extensiones sigue siendo experimental. El proyecto no promete ejecutar todas las extensiones de escritorio.

| Función | Implementación |
| --- | --- |
| `chrome://extensions`, lista, activar/desactivar, eliminar, modo desarrollador | Interfaz y servicios originales de Chromium habilitados mediante Desktop Android |
| Menú Android | Conserva el menú de acciones y añade acceso directo a administrar extensiones en el menú sin submenús |
| Cargar desempaquetadas | Selector de carpetas de Android y `UnpackedInstaller` existentes en la base |
| Instalar `.crx` | Botón en el modo desarrollador → selector Android → `CrxInstaller` → validación, permisos e instalación |
| Manifest V3 y service workers | Componentes de Chromium habilitados; incluye extensión para pruebas en dispositivo |
| Tampermonkey / Violentmonkey | Prioridad de pruebas: versiones MV3; funcionamiento en este APK aún no verificado |
| Android 16 ARM64 | Objetivo; el empaquetado comprueba ABI, firma, paquete y `minSdk <= 36` |

## Compilar

El runner necesita Ubuntu x86_64, **100 GiB libres antes de sincronizar**, al menos 16 GiB de RAM (32+ recomendados) y acceso a los servidores de Chromium. El APK resultante es ARM64. En runners alojados por GitHub se libera el SDK Android y otros toolchains preinstalados que esta build no usa. Si aun así falta espacio, el workflow se detiene antes de descargar el código. Se recomiendan 200 GiB libres para disponer de margen.

```bash
scripts/build-apk.sh --install-deps
```

En GitHub, configura `CHROMIUM_RUNNER` con una etiqueta o lista de etiquetas **en JSON**, por ejemplo `"ubuntu-24.04-32core"` si ese runner existe en tu cuenta, o `["self-hosted","Linux","X64","chromium"]`. El valor predeterminado es `"ubuntu-24.04"`; no se contrata ni aprovisiona infraestructura automáticamente.

El workflow se ejecuta al modificar código en `main`, al enviar un tag `zaid-v*` o manualmente desde Actions. Ejecuta depot_tools, gclient, GN y autoninja para construir `chrome_public_apk`. Solo sube el artifact del APK si la compilación y la verificación terminan correctamente.

- [Compilación y firma](docs/build.md)
- [Arquitectura y alcance](docs/architecture.md)
- [Pruebas en Android 16](docs/testing.md)
- [Sistema de parches](patches/README.md)

## Estructura

| Ruta | Contenido |
| --- | --- |
| `.github/workflows/` | Validación, build manual/automático, artifacts y releases |
| `chromium/` | Versión, commits, args GN y contratos del código base |
| `patches/` | Cambios sobre los archivos originales de Chromium |
| `src/` | Archivos nuevos que se copian sobre el checkout de Chromium |
| `scripts/` | Sincronización, aplicación de parches, compilación y empaquetado |
| `tests/` | Pruebas de herramientas y extensión MV3 para el dispositivo |
| `docs/` | Compilación, integración y criterios de aceptación |

El código completo de Chromium se obtiene en `work/src` durante la compilación. No se incorpora su historial gigante en este repositorio.
