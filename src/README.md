# Archivos adicionales para Chromium

Esta carpeta se superpone sobre la raíz `src` del checkout de Chromium. Los archivos nuevos de C++ viven en sus rutas definitivas y los parches incorporan sus fuentes y dependencias al grafo GN original.

`ZaidCrxInstallHandler` pertenece únicamente a la WebUI de extensiones de Android. Usa `CrxInstaller` y la confirmación de permisos originales. La lista y los cambios de estado usan los servicios de Chromium existentes.
