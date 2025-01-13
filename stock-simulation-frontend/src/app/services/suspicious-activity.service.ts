// src/app/services/suspicious-activity.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface IUserInfo {
  id: number;
  username: string;
  role?: string;
}

export interface IStockInfo {
  id: number;
  ticker_symbol: string;
}

export interface ITradeDetail {
  id: number;
  quantity: number;
  price: string;
  trade_time: string; // or Date
  user: IUserInfo; 
  stock: IStockInfo;
}

export interface ISuspiciousActivity {
  id: number;
  reason: string;
  flagged_at: string;
  reviewed: boolean;
  trade?: ITradeDetail | null; // might be null
}

@Injectable({
  providedIn: 'root'
})
export class SuspiciousActivityService {
  private activitiesUrl = 'http://localhost:8000/api/stocks/suspicious-activities/'; 
  private suspensionUrl = 'http://localhost:8000/api/regulationssuspensions/';

  constructor(private http: HttpClient) {}

  // Fetch suspicious activities
  getAllActivities(): Observable<ISuspiciousActivity[]> {
    const token = localStorage.getItem('access_token'); // Use your token storage logic
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
    return this.http.get<ISuspiciousActivity[]>(this.activitiesUrl, { headers });
  }

  // Suspend trader based on suspicious activity
  suspendTrader(payload: any): Observable<any> {
    const token = localStorage.getItem('access_token'); // Use your token storage logic
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    });
    return this.http.post(this.suspensionUrl, payload, { headers });
  }
}
