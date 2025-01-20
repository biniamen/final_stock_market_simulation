// src/app/interceptors/auth.interceptor.ts

import { Injectable } from '@angular/core';
import { 
  HttpEvent, 
  HttpInterceptor, 
  HttpHandler, 
  HttpRequest, 
  HttpErrorResponse 
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor(private authService: AuthService) {}

  intercept(
    req: HttpRequest<any>, 
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    const token = this.authService.getToken();

    // Clone the request to add the new header
    let authReq = req;
    if (token) {
      authReq = req.clone({
        headers: req.headers.set('Authorization', `Bearer ${token}`)
      });
    }

    // Send the newly created request
    return next.handle(authReq).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401 || error.status === 403) {
          // If unauthorized, logout the user
          this.authService.logout();
        }
        return throwError(error);
      })
    );
  }
}
