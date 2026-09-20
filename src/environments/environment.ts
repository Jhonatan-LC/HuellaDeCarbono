// Producción: sin backend propio en el mismo origen todavía, así que el build de
// producción sigue apuntando al backend Django tal como se despliegue (ajustar
// cuando exista un dominio de producción real).
export const environment = {
  production: true,
  apiBaseUrl: 'http://localhost:8000',
};
