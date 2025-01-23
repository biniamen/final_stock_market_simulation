// src/app/services/api.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Regulation {
  id?: number;
  name: string;
  value: string;
  description?: string;
  created_by?: number;
  created_at?: string;
  last_updated?: string;
}

export interface WorkingHour {
  id?: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
}

export interface Suspension {
  id?: number;
  trader: number;  // user ID
  stock?: number;  // stock ID (nullable)
  suspension_type: string;
  initiator: string;
  reason: string;
  is_active: boolean;
  created_at?: string;
  released_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api/regulations'; // Adjust as needed

  constructor(private http: HttpClient) {}

  // ============= Regulations =============

  getRegulations(): Observable<Regulation[]> {
    return this.http.get<Regulation[]>(`${this.baseUrl}regulations/`);
  }

  createRegulation(data: Regulation): Observable<Regulation> {
    return this.http.post<Regulation>(`${this.baseUrl}regulations/`, data);
  }

  updateRegulation(id: number, data: Regulation): Observable<Regulation> {
    return this.http.put<Regulation>(`${this.baseUrl}regulations/${id}/`, data);
  }

  deleteRegulation(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}regulations/${id}/`);
  }

  // ============= Working Hours =============

  getWorkingHours(): Observable<WorkingHour[]> {
    return this.http.get<WorkingHour[]>(`http://localhost:8000/api/regulationsworking-hours/`);
  }

  createWorkingHour(data: WorkingHour): Observable<WorkingHour> {
    return this.http.post<WorkingHour>(`http://localhost:8000/api/regulationsworking-hours/`, data);
  }

  updateWorkingHour(id: number, data: WorkingHour): Observable<WorkingHour> {
    return this.http.put<WorkingHour>(`http://localhost:8000/api/regulationsworking-hours/${id}/`, data);
  }

  deleteWorkingHour(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}working-hours/${id}/`);
  }

  // ============= Suspensions =============

  getSuspensions(): Observable<Suspension[]> {
    return this.http.get<Suspension[]>(`${this.baseUrl}suspensions/`);
  }

  createSuspension(data: Suspension): Observable<Suspension> {
    return this.http.post<Suspension>(`${this.baseUrl}suspensions/`, data);
  }

  updateSuspension(id: number, data: Suspension): Observable<Suspension> {
    return this.http.put<Suspension>(`${this.baseUrl}suspensions/${id}/`, data);
  }

  deleteSuspension(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}suspensions/${id}/`);
  }

  releaseSuspension(id: number): Observable<any> {
    return this.http.post(`${this.baseUrl}suspensions/${id}/release/`, {});
  }

  // Fetch traders
  getTraders(): Observable<any[]> {
    const accessToken = localStorage.getItem('access_token'); // Fetch access token from local storage
    const headers = new HttpHeaders({
      Authorization: `Bearer ${accessToken}`, // Pass token in Authorization header
    });

    return this.http.get<any[]>(`http://localhost:8000/api/users/users/`, { headers });
  }

  // Fetch stocks
  getStocks(): Observable<any[]> {
    const accessToken = localStorage.getItem('access_token'); // Fetch access token from local storage
    const headers = new HttpHeaders({
      Authorization: `Bearer ${accessToken}`, // Pass token in Authorization header
    });

    return this.http.get<any[]>(`http://localhost:8000/api/stocks/stocks/`, { headers });
  }
}
