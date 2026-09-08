import { Component, OnDestroy, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WelcomePopupComponent } from './shared/welcome-popup/welcome-popup.component';
import { AuthService } from './auth/auth.service';
import { UiService } from './shared/ui.service';
import { Subject, takeUntil, pairwise, filter } from 'rxjs';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WelcomePopupComponent, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit, OnDestroy {
  title = 'huella-carbono-app';
  private destroy$ = new Subject<void>();

  constructor(private auth: AuthService, private ui: UiService) {}

  ngOnInit() {
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