// src/app/services/user.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import { UsersPortfolio } from '../models/portfolio.model'; // Import the interface

@Injectable({
  providedIn: 'root'
})
export class UserService {

  private apiUrl = `${environment.baseUrl}/api`; // Ensure it matches your backend API path

  private userListUrl = 'http://localhost:8000/api/users/list/'; // Adjust the URL as needed
  private users = 'http://localhost:8000/api/users/';
    private userportfolio = 'http://localhost:8000/api/stocks/portfolios/user'
    private capitalizeWithraw = 'http://localhost:8000/api/stocks/'


  constructor(private http: HttpClient) { }

  // Method to get the list of users
  getUsers(): Observable<any[]> {
    const token = localStorage.getItem('access_token'); // Adjust based on how you store tokens
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
    return this.http.get<any[]>(`${this.apiUrl}/users/list/`, { headers });

    // return this.http.get<any[]>(this.userListUrl, { headers });
  }

  // Method to approve KYC
  approveKyc(userId: number): Observable<any> {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
    const body = { action: 'approve' };
    const url = `${this.users}${userId}/kyc/`; // Assuming /api/users/<id>/kyc/
    return this.http.post<any>(url, body, { headers });
  }

  // Method to reject KYC
  rejectKyc(userId: number): Observable<any> {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
    const body = { action: 'reject' };
    const url = `${this.users}${userId}/kyc/`; // Assuming /api/users/<id>/kyc/
    return this.http.post<any>(url, body, { headers });
  }

  // **New Method: Deactivate User**
  deactivateUser(userId: number): Observable<any> {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
    const url = `${this.users}${userId}/deactivate/`; // Deactivation URL
    return this.http.post<any>(url, {}, { headers }); // Empty body
  }

  /**
   * **New Method: Get User Portfolio by User ID**
   * Fetches the portfolio for a specific user.
   * @param userId The ID of the user whose portfolio is to be fetched.
   * @returns An Observable of UsersPortfolio.
   */
  getUserPortfolio(userId: number): Observable<UsersPortfolio> {
    const token = localStorage.getItem('access_token'); // Adjust based on how you store tokens
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
    const url = `${this.userportfolio}/${userId}/`; // Custom endpoint
    return this.http.get<UsersPortfolio>(url, { headers });
  }

  capitalizeProfit(): Observable<any> {
    return this.http.post(`${this.capitalizeWithraw}capitalize_profit/`, {});
  }

  withdrawProfit(): Observable<any> {
    return this.http.post(`${this.apiUrl}withdraw_profit/`, {});
  }
}
