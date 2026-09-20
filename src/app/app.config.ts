import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { provideEchartsCore } from 'ngx-echarts';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { csrfInterceptor } from './auth/csrf.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    // Sin zone.js: cada actualización de estado fuera de un evento de plantilla o del
    // async pipe (p.ej. dentro de un subscribe() a HttpClient) debe avisarle a Angular
    // con ChangeDetectorRef.markForCheck() — si no, la vista no se refresca sola.
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([csrfInterceptor])),
    provideClientHydration(withEventReplay()),
    provideCharts(withDefaultRegisterables()),
    provideEchartsCore({ echarts: () => import('echarts') }),
  ]
};
