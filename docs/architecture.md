# Arquitectura

Se utiliza la implementación Desktop Android de Chromium 153. No se simula el sistema de extensiones con un WebView ni se registra una extensión modificando archivos de preferencias.

## Componentes

| Componente | Fuente en Chromium |
| --- | --- |
| Habilitación de core | `extensions/buildflags/buildflags.gni` |
| Inicialización de ExtensionService, scripts y workers | `chrome/browser/extensions/chrome_extension_system.cc` |
| Registro y ciclo de vida | `extensions/browser/extension_registry.*`, `extension_registrar.*` |
| WebUI de administración | `chrome/browser/ui/webui/extensions/`, `chrome/browser/resources/extensions/` |
| Carpetas y permisos del proveedor Android | `DeveloperPrivateLoadUnpackedFunction`, `ResolveToVirtualDocumentPath`, `UnpackedInstaller` |
| Instalación CRX | `CrxInstaller`, `SandboxedUnpacker` |
| Entrada nueva del selector CRX | `ZaidCrxInstallHandler`, incorporado al target WebUI de Android |

`chrome://extensions` ya usa `developerPrivate` y los eventos del registro para mostrar instalaciones, cambios de estado, errores y eliminación. Se mantiene esa ruta. Las comprobaciones en `source-contract.json` verifican los puntos de integración de la revisión fijada.

## Selector CRX

El botón `Instalar CRX` se muestra en el modo desarrollador. Una llamada desde la WebUI con interacción reciente abre `SelectFileDialog`. El handler verifica el perfil, las políticas y el modo desarrollador antes de abrir y después de seleccionar. Los perfiles invitados, de incógnito e infantiles no usan esta nueva ruta.

La ruta seleccionada —incluidos los URI `content://` que entrega Android— pasa al `CrxInstaller` original. `SandboxedUnpacker` copia el archivo a su área temporal, valida el formato/firma y procesa el manifiesto; el instalador comprueba requisitos y políticas, presenta los permisos y registra la extensión. No se omite la comprobación criptográfica ni se activa una extensión silenciosamente. El archivo original no se elimina.

Solo se resuelve éxito en la WebUI cuando finaliza la instalación. La navegación invalida los callbacks de la página anterior y cierra el selector. No se aceptan rutas arbitrarias enviadas por JavaScript ni se expone este handler a páginas web o extensiones.

## Compatibilidad

La base ya incluye las APIs `runtime`, `storage`, `tabs`, `scripting` y `userScripts`, además de los service workers MV3. La disponibilidad de una API no demuestra que todas sus operaciones funcionen en Android. Las integraciones específicas del escritorio siguen siendo una limitación posible.

Se priorizan las ediciones Manifest V3 de [Tampermonkey](https://www.tampermonkey.net/) y [Violentmonkey](https://violentmonkey.github.io/get-it/). Conservan los permisos de sitios y el interruptor individual de scripts de usuario de Chromium. Las ediciones MV2 heredadas no forman parte de la garantía de compatibilidad.

No se fuerzan permisos, no se desactivan protecciones del navegador y no se insertan API keys o credenciales de Google. No se promete sincronización con cuentas de Chrome.
