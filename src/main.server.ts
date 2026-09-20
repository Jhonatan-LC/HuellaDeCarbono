import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';
import { BootstrapContext, bootstrapApplication } from '@angular/platform-browser';
import { App } from './app/app';
import { config } from './app/app.config.server';

// Bootstrap de servidor separado del de main.ts: hay que registrar el locale
// acá también o el SSR revienta con NG0701 en cualquier pipe 'number'/'date' con 'es'.
registerLocaleData(localeEs);

const bootstrap = (context: BootstrapContext) =>
    bootstrapApplication(App, config, context);

export default bootstrap;
