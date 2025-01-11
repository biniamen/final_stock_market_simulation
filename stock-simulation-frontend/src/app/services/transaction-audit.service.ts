
// src/app/services/transaction-audit.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ITransactionAuditTrail } from '../models/transaction-audit.model';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TransactionAuditService {
  private baseUrl = 'http://localhost:8000/api/stocks'; // Adjust this URL to match your backend API

  constructor(private http: HttpClient) { }

  /**
   * Fetches all transaction audit trails from the backend.
   */
  getAllAuditTrails(): Observable<ITransactionAuditTrail[]> {
    const token = localStorage.getItem('access_token'); // Adjust based on how you store tokens
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
    return this.http.get<ITransactionAuditTrail[]>(`${this.baseUrl}/audit-trails/`,{headers});
  }
}
