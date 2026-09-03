# Reglas de Flujo de Trabajo en Git

1. **NUNCA modificar ni hacer commits directamente en la rama `main`**.
2. **Flujo obligatorio para nuevas tareas o cambios**:
   - Actualizar `main` mediante `git pull origin main` (o `git fetch`).
   - Crear y cambiar inmediatamente a una nueva rama de trabajo descriptiva (`git checkout -b <tipo>/<nombre-descriptivo>`).
   - Realizar todos los cambios, pruebas y commits exclusivamente en dicha rama.
