import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Toast {
  id: number;
  mensaje: string;
  tipo: 'success' | 'error';
}

let siguienteToastId = 1;

@Injectable({
  providedIn: 'root'
})
export class UiService {
  private welcomePopupVisible = new BehaviorSubject<boolean>(false);
  public welcomePopupVisible$ = this.welcomePopupVisible.asObservable();

  private toasts = new BehaviorSubject<Toast[]>([]);
  public toasts$ = this.toasts.asObservable();

  showWelcomePopup() {
    this.welcomePopupVisible.next(true);
  }

  hideWelcomePopup() {
    this.welcomePopupVisible.next(false);
  }

  showToast(mensaje: string, tipo: Toast['tipo'] = 'success', duracionMs = 4000) {
    const toast: Toast = { id: siguienteToastId++, mensaje, tipo };
    this.toasts.next([...this.toasts.value, toast]);
    setTimeout(() => this.dismissToast(toast.id), duracionMs);
  }

  dismissToast(id: number) {
    this.toasts.next(this.toasts.value.filter((t) => t.id !== id));
  }
}
