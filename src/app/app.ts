import { Component, OnDestroy, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WelcomePopupComponent } from './shared/welcome-popup/welcome-popup.component';
import { ToastComponent } from './shared/toast/toast.component';
import { AuthService } from './auth/auth.service';
import { UiService } from './shared/ui.service';
import { ThemeService } from './shared/theme.service';
import { Subject, takeUntil, pairwise, filter } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WelcomePopupComponent, ToastComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit, OnDestroy {
  title = 'huella-carbono-app';
  private destroy$ = new Subject<void>();

  constructor(private auth: AuthService, private ui: UiService, private theme: ThemeService) {}

  ngOnInit() {
    // Aplica el tema guardado (o el del SO) apenas arranca la app — ver ThemeService.
    this.theme.init();

    this.auth.isAuthenticated$.pipe(
      takeUntil(this.destroy$),
      pairwise(),
      filter(([was, is]) => !was && is)
    ).subscribe(() => {
      this.ui.showWelcomePopup();
    });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}