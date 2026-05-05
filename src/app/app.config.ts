import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  importProvidersFrom,
} from '@angular/core';
import {provideRouter} from '@angular/router';
import {MatIconModule} from '@angular/material/icon';
import {LucideAngularModule, Shield, Wifi, Users, Signal, AlertTriangle, Search, Trash2, Plus} from 'lucide-angular';

import {routes} from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(), 
    provideRouter(routes),
    importProvidersFrom(
      MatIconModule,
      LucideAngularModule.pick({ Shield, Wifi, Users, Signal, AlertTriangle, Search, Trash2, Plus })
    )
  ],
};
