# Validación

## Pruebas disponibles

```bash
python3 -m unittest discover -s tests -v
python3 scripts/source_contract.py
```

Las pruebas locales comprueban rechazo de un APK vacío, ABI incorrecta o mezclada, cambios de origen y capacidad insuficiente. La validación de origen descarga una selección de archivos del commit fijado, comprueba hashes y puntos de integración, aplica los cuatro parches y repite la aplicación para comprobar que puede reanudarse. **No es una compilación C++/Java/TypeScript.**

La comprobación completa de GN y la compilación se ejecutan en `Build ARM64 APK`. Los resultados y limitaciones de la validación quedan en `source-check.json`; los de un APK compilado, en `build-metadata.json`.

## Criterios de aceptación en Android 16 ARM64

Todos están pendientes hasta ejecutarlos en un dispositivo con el APK de este proyecto.

| Prueba | Resultado necesario |
| --- | --- |
| Instalar APK | Paquete `com.zaid.chromium`, apertura y navegación sin cierre inesperado |
| Menú normal y menú con submenús | Acceso a las acciones de extensión y a administrar extensiones |
| `chrome://extensions` | Lista, modo desarrollador y cambio persistente de activar/desactivar |
| CRX3 válido | Selector, permisos visibles, instalación confirmada, extensión en la lista |
| CRX alterado, firma incorrecta o manifiesto inválido | Error visible y ninguna extensión registrada |
| Cancelación y navegación mientras está abierto el selector | Sin instalación inesperada, doble respuesta ni cierre inesperado |
| Perfil/política que prohíbe instalar | Rechazo; sin ruta alternativa que omita la restricción |
| Desempaquetada desde proveedor de documentos Android | Seleccionar carpeta con manifest.json; cargar, reiniciar y volver a cargar |
| Popup y opciones | Interacción táctil y tamaño utilizable en el teléfono |
| Persistencia | Extensiones y storage conservados al cerrar y reabrir el navegador |
| MV3 worker | Se reactiva con mensajes/alarmas después de quedar inactivo |
| Scripts y permisos por sitio | Inyección solo en sitios autorizados; revocar acceso detiene la inyección |

## Extensión MV3 incluida

Carga `tests/fixtures/mv3-smoke` con **Cargar desempaquetada**. Puedes comprimir y transferir esa carpeta al teléfono y extraerla allí. Si el proveedor de archivos no permite elegir la raíz de Descargas, usa una subcarpeta.

1. En Detalles, permite scripts de usuario para esta extensión.
2. Abre `https://example.com/` con su botón.
3. Abre las opciones o el popup y ejecuta las pruebas.
4. Comprueba los resultados de runtime, storage, tabs e inyección mediante scripting.
5. La primera ejecución registra un userscript. Recarga example.com: el atributo `data-zaid-user-script` de `<html>` debe ser `ok`.
6. Espera a que el worker quede inactivo; vuelve a ejecutar. Compara el identificador del worker y los datos persistidos de la alarma. No confundas registro de una alarma con una reactivación verificada.
7. Desactiva la extensión, recarga la página y comprueba que los marcadores ya no se inyectan. Reactiva y repite.

La prueba solo solicita acceso a example.com, no envía datos a servidores y no requiere root. Que esta prueba funcione no equivale a certificar cualquier extensión externa.

## Tampermonkey y Violentmonkey

Usa una versión MV3 obtenida del sitio oficial de cada proyecto. Registra en el resultado la versión exacta de la extensión y el SHA256 del APK. Activa el permiso de scripts de usuario en sus detalles cuando corresponda. Crea un script de prueba limitado a example.com que cambie un texto visible; comprueba activación, desactivación, almacenamiento del gestor, reinicio y acceso por sitio.

Referencia: [documentación de chrome.userScripts](https://developer.chrome.com/docs/extensions/reference/api/userScripts). No alteres políticas del perfil para convertir una prueba bloqueada en una prueba aprobada.
