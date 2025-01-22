// src/app/services/auth.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, Subscription, timer } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { JwtPayload, jwtDecode } from 'jwt-decode';
import { ToastrService } from 'ngx-toastr';

interface DecodedToken extends JwtPayload {
  // Define any additional properties your token includes
  username: string;
  role: string;
  // 'exp' is already part of JwtPayload
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://127.0.0.1:8000/api/users/';
  private tokenExpirationTimer: Subscription | null = null;

  constructor(private http: HttpClient, private router: Router,private toastr: ToastrService ) {
    const token = this.getToken();
    if (token && !this.isTokenExpired(token)) {
      this.startTokenExpirationTimer(token);
      this.initTokenExpirationCheck();
    } else {
      this.logout();
    }

     // **Ensure this listener is present to handle 'lastLogin' changes**
   window.addEventListener('storage', (event) => {
    if (event.key === 'lastLogin') {
      // A new login occurred elsewhere, so log out this tab/browser
      this.logout(false); // Pass 'false' to avoid notifying the backend again
    }
  });
  }

  /**
   * Stores the JWT token in localStorage and initiates the expiration timer.
   * @param token JWT token string
   */
  setToken(token: string): void {
    localStorage.setItem('access_token', token);
    this.startTokenExpirationTimer(token);
  }

  /**
   * Retrieves the JWT token from localStorage.
   * @returns JWT token string or null
   */
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Removes the JWT token from localStorage and clears the expiration timer.
   */
  clearToken(): void {
    localStorage.removeItem('access_token');
    this.clearTokenExpirationTimer();
  }

  /**
   * Decodes the JWT token to extract payload.
   * @param token JWT token string
   * @returns DecodedToken object
   */
  decodeToken(token: string): DecodedToken {
    return jwtDecode<DecodedToken>(token);
  }

  /**
   * Checks if the token is expired based on the 'exp' claim.
   * @param token JWT token string
   * @returns boolean indicating if token is expired
   */
  isTokenExpired(token: string): boolean {
    const decoded = this.decodeToken(token);
    if (!decoded.exp) {
      return true; // If no expiration, consider it expired
    }
    const expirationDate = new Date(decoded.exp * 1000);
    return expirationDate < new Date();
  }

  /**
   * Starts a timer that logs out the user when the token expires.
   * @param token JWT token string
   */
  startTokenExpirationTimer(token: string): void {
    const decoded = this.decodeToken(token);
    if (!decoded.exp) {
      this.logout(); // If no expiration, log out immediately
      return;
    }

    const expirationDate = new Date(decoded.exp * 1000);
    const currentTime = new Date();
    const timeRemaining = expirationDate.getTime() - currentTime.getTime();

    if (timeRemaining <= 0) {
      this.logout(); // Token already expired
      return;
    }

    // Clear any existing timer
    this.clearTokenExpirationTimer();

    // Set up a new timer
    this.tokenExpirationTimer = timer(timeRemaining).subscribe(() => {
      this.logout();
    });
  }

  /**
   * Clears the token expiration timer.
   */
  clearTokenExpirationTimer(): void {
    if (this.tokenExpirationTimer) {
      this.tokenExpirationTimer.unsubscribe();
      this.tokenExpirationTimer = null;
    }
  }

  /**
   * Logs out the user by clearing the token and redirecting to login.
   */
  logout(notifyBackend: boolean = true): void {
    if (notifyBackend) {
      this.clearToken();
      localStorage.removeItem('refresh_token'); // Clear refresh token if stored
      // Optionally, inform the backend to invalidate the token
      const token = this.getToken();
      if (token) {
        const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
        this.http.post(this.apiUrl + 'logout/', {}, { headers })
          .subscribe(
            () => {
              console.log('Logged out from backend.');
            },
            error => {
              console.error('Error during logout:', error);
            }
          );
      }
    } else {
      // Logout without notifying the backend (used when 'lastLogin' changes)
      this.clearToken();
      localStorage.removeItem('refresh_token');
    }
    
    this.router.navigate(['/login']);
    
    // Show toastr notification
    this.toastr.warning('You have been logged out from another device/browser.', 'Logged Out');
  }

  /**
   * Initializes periodic token expiration checks every 30 minutes.
   */
  initTokenExpirationCheck(): void {
    // Check every 30 minutes (1800000 milliseconds)
    timer(1800000, 1800000).subscribe(() => {
      const token = this.getToken();
      if (token && this.isTokenExpired(token)) {
        this.logout();
      }
    });
  }

  /**
   * Refreshes the access token using the refresh token.
   * Assumes you have a refresh token endpoint.
   * If not using refresh tokens, you can omit this method.
   */
  refreshToken(): Observable<any> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      this.logout();
      throw new Error('No refresh token available');
    }

    return this.http.post<any>(this.apiUrl + 'token/refresh/', { refresh: refreshToken })
      .pipe(
        tap(response => {
          if (response.access) {
            this.setToken(response.access);
            if (response.refresh) {
              localStorage.setItem('refresh_token', response.refresh);
            }
            this.initTokenExpirationCheck();
          } else {
            this.logout();
          }
        })
      );
  }

  // Handle user registration
  register(user: FormData): Observable<any> {
    return this.http.post(this.apiUrl + 'register/', user);
  }

  // Handle user login
  login(credentials: any): Observable<any> {
    // POST to your /login/ endpoint
    return this.http.post<any>(this.apiUrl + 'login/', credentials)
      .pipe(
        tap((response) => {
          // If the backend returns { access: "...", refresh: "..." }
          if (response.access_token) {
            // Store the access token
            this.setToken(response.access_token);
  
            // If refresh token is present, store it as well
            if (response.refresh) {
              localStorage.setItem('refresh_token', response.refresh);
            }
  
            // Optionally set up expiration checks, etc.
            this.initTokenExpirationCheck();
  
            // Mark lastLogin to detect multi-login
            localStorage.setItem('lastLogin', Date.now().toString());
          }
        })
      );
  }
  

  // List all registered users (Regulator only)
  listUsers(): Observable<any> {
    return this.http.get(this.apiUrl);
  }

  // Approve or reject KYC status (Regulator only)
  updateKycStatus(userId: number, action: string): Observable<any> {
    return this.http.post(`${this.apiUrl}${userId}/kyc/`, { action });
  }

  getTraderOrders(): Observable<any> {
    const token = this.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get(`${this.apiUrl}trader/orders/`, { headers });
  }
 
  
}
