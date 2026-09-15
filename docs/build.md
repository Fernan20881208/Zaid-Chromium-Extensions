# Compilación y releases

## Base reproducible

`chromium/revision.json` fija la versión, el commit de Chromium y el commit de depot_tools. La etiqueta se verifica contra el commit antes de sincronizar. `gclient` descarga las dependencias declaradas por esa revisión.

La base fijada fue publicada como actualización estable general para Android: [Chrome Releases, septiembre de 2026](https://chromereleases.googleblog.com/2026/09/). Las versiones etiquetadas como Early Stable se tratan por separado. No se sigue `main` silenciosamente.

## Runner

Ubuntu 22.04/24.04 x86_64, 200 GiB libres iniciales y 16 GiB de RAM mínimo; se recomiendan 32–64 GiB y un disco de 300 GiB o más. Son límites conservadores de este proyecto, no una garantía de duración. Chromium puede superar las seis horas del job según CPU y red. El host de compilación x86_64 genera un APK `arm64-v8a`.

El runner debe permitir `sudo -n` para las dependencias. Usa un runner dedicado cuando configures uno propio. Las PR externas solo ejecutan la validación en un runner alojado; no ejecutan código de una PR en tu máquina de compilación.

Variable del repositorio `CHROMIUM_RUNNER` (Settings → Secrets and variables → Actions → Variables):

- Runner propio: `["self-hosted","Linux","X64","chromium"]`.
- Runner alojado de mayor capacidad: su etiqueta existente como cadena JSON, por ejemplo `"ubuntu-24.04-32core"`.
- Sin variable: `"ubuntu-24.04"`. Si no tiene recursos, el workflow termina con un diagnóstico antes de descargar Chromium.

## Comandos

```bash
python3 -m unittest discover -s tests -v
python3 scripts/source_contract.py
scripts/build-apk.sh --install-deps
```

La secuencia de build es:

1. Comprobar recursos y sincronizar depot_tools y Chromium.
2. Ejecutar `build/install-build-deps.sh --android --no-prompt` y `gclient runhooks`.
3. Aplicar los parches en orden y copiar `src/` sobre el checkout.
4. Copiar `chromium/args.gn` y ejecutar `gn gen --fail-on-unused-args --check`.
5. Ejecutar `autoninja -C out/ZaidArm64 chrome_public_apk`, con Siso como ejecutor local actual de Chromium y sin ejecución remota.
6. Verificar el APK y generar los archivos de `dist/`.

`is_desktop_android = true` es necesario además de los flags de extensiones. Se conserva `is_official_build = true`, con PGO y ThinLTO desactivados para evitar perfiles de optimización externos y reducir el costo de enlace. Esto no convierte al fork en un producto oficial de Google.

Para reanudar un checkout que ya tiene los parches (se exigen 40 GiB libres de margen, en vez de los 200 GiB previos a una descarga inicial):

```bash
scripts/build-apk.sh --skip-sync
```

Para usar otro disco: `--work /ruta/zaid-build`. No se ejecuta `git reset --hard` sobre un checkout existente. Un cambio de base requiere un directorio de trabajo nuevo o una limpieza hecha conscientemente por quien lo administra.

## APK y firma

El paquete es `com.zaid.chromium`. El APK original se encuentra en `work/src/out/ZaidArm64/apks/ChromePublic.apk`.

Sin secretos, se conserva la firma de desarrollo de Chromium y el nombre termina en `-development.apk`. Sirve para pruebas y no se publica como release. No uses esa clave pública de desarrollo para distribución de confianza ni esperes instalar después una build con otra firma como actualización.

Para una release, configura estos cuatro secretos de Actions:

| Secreto | Valor |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Tu keystore codificado en base64 |
| `ANDROID_KEYSTORE_PASSWORD` | Contraseña del keystore |
| `ANDROID_KEY_ALIAS` | Alias de la clave |
| `ANDROID_KEY_PASSWORD` | Contraseña de la clave |

La clave se decodifica temporalmente con permisos restringidos; no se almacena en el repositorio ni en artifacts. Guarda tú una copia duradera: la misma clave es necesaria para futuras actualizaciones. El workflow no genera ni sustituye una identidad de firma automáticamente.

Activa `publish_release` en la ejecución manual o sube un tag `zaid-v*`. La publicación exige una compilación exitosa, firma de release y procedencia del mismo commit. Se publica como **prerelease experimental** hasta completar las pruebas en Android. `is_official_build` no sustituye la firma del APK.

`dist/` incluye APK, `SHA256SUMS`, `build-metadata.json`, revisión, args GN, certificado público y datos del manifiesto. `build-metadata.json` distingue compilación de pruebas en dispositivo; nunca marca Tampermonkey o Violentmonkey como probados automáticamente.

## Actualizar Chromium

Comprueba la actualización estable general en la fuente oficial, actualiza versión y commit en `revision.json`, revisa los parches, renueva los hashes de `source-contract.json` contra los archivos exactos y ejecuta validación y compilación. Un cambio de hash detiene la validación para obligar a revisar cambios de API.

Referencia de compilación: [instrucciones de Chromium Android](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/android_build_instructions.md).
