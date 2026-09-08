import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class UiService {
  private welcomePopupVisible = new BehaviorSubject<boolean>(false);
  public welcomePopupVisible$ = this.welcomePopupVisible.asObservable();

  showWelcomePopup() {
    this.welcomePopupVisible.next(true);
  }

  hideWelcomePopup() {
    this.welcomePopupVisible.next(false);
  }
}
