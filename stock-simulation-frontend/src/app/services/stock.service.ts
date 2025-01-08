import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class StockService {
  private baseUrl = 'http://127.0.0.1/api/stocks/stocks/';

  constructor(private http: HttpClient) {}

  publishStock(stockData: any): Observable<any> {
    return this.http.post(this.baseUrl, stockData);
  }

  getPublishedStock(companyId: number): Observable<any> {
    return this.http.get(`${this.baseUrl}?company=${companyId}`);
  }
}
