import { HttpInterceptorFn } from '@angular/common/http';

const MUTATING_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') {
    return null; // SSR: no cookie jar on the server
  }
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

// Angular's built-in XSRF interceptor skips absolute URLs, but this app calls
// the backend with absolute http://localhost:8000 URLs, so we attach the
// Django CSRF cookie as a header ourselves.
export const csrfInterceptor: HttpInterceptorFn = (req, next) => {
  if (!MUTATING_METHODS.includes(req.method)) {
    return next(req);
  }

  const token = readCookie('csrftoken');
  if (!token) {
    return next(req);
  }

  return next(req.clone({ setHeaders: { 'X-CSRFToken': token } }));
};
