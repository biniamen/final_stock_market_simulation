// src/app/services/dividend.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

// Define interfaces for Dividend and DividendDistribution
export interface Dividend {
  id: number;
  company: number; // Assuming company ID is used; adjust if nested
  budget_year: string;
  dividend_ratio: string; // Decimal as string
  total_dividend_amount: string; // Decimal as string
  status: string;
  created_at: string;
}
// Interface for DividendDetailedHolding
export interface DividendDetailedHolding {
  id: number;
  dividend_id: number;
  user_id: number;
  username: string;
  stock_symbol: string;
  order_type: string;
  price: string;
  quantity: number;
  transaction_fee: string;
  total_buying_price: string;
  weighted_value: string;
  dividend_eligible: string;
  trade_time: string;
  ratio_at_creation: string;
  paid_dividend: string;
  company_id: number;
  budget_year: string;
  created_at: string;
}
export interface DividendDistribution {
  id: number;
  dividend: string; // Read-only string representation
  user: string; // Username
  amount: string; // Decimal as string
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class DividendService {

  private apiUrl = 'http://localhost:8000/api/stocks/'; // Adjust based on your API's base URL

  constructor(private http: HttpClient) { }

  // Fetch all dividends, optionally filtered by company
  getDividends(companyId?: number): Observable<Dividend[]> {
    let params = new HttpParams();
    if (companyId) {
      params = params.set('company', companyId.toString());
    }
    return this.http.get<Dividend[]>(`${this.apiUrl}dividends/`, { params });
  }

  // Create a new dividend
  createDividend(dividendData: Partial<Dividend>): Observable<Dividend> {
    return this.http.post<Dividend>(`${this.apiUrl}dividends/`, dividendData);
  }

  // Trigger dividend distribution
  distributeDividend(dividendId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}dividends/${dividendId}/distribute/`, {});
  }

  // Fetch dividend distributions, optionally filtered by dividend or user
  getDividendDistributions(dividendId?: number, userId?: number): Observable<DividendDistribution[]> {
    let params = new HttpParams();
    if (dividendId) {
      params = params.set('dividend_id', dividendId.toString());
    }
    if (userId) {
      params = params.set('user_id', userId.toString());
    }
    return this.http.get<DividendDistribution[]>(`${this.apiUrl}distributions/`, { params });
  }
  getDetailedHoldings(companyId: number, budgetYear: string): Observable<DividendDetailedHolding[]> {
    let params = new HttpParams()
      .set('company_id', companyId.toString())
      .set('budget_year', budgetYear);
    return this.http.get<DividendDetailedHolding[]>(`${this.apiUrl}detailed-holdings/`, { params });
  }

  // get trader dividend
  getTraderDividends(budgetYear?: string): Observable<any> {
    let params = new HttpParams();
    if (budgetYear) {
      params = params.set('budget_year', budgetYear);
    }
    return this.http.get(`${this.apiUrl}dividends/trader/`, { params });
  }
  // get regulators dividend

  getRegulatorDividends(budgetYear?: string): Observable<any> {
    let params = new HttpParams();
    if (budgetYear) {
      params = params.set('budget_year', budgetYear);
    }
    return this.http.get(`${this.apiUrl}dividends/regulator/`, { params });
  }
}
