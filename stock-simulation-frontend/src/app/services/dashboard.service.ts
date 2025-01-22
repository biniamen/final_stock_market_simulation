// src/app/services/dashboard.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface DashboardResponse {
  user_info: {
    username: string;
    role: string;
    account_balance: string;
    profit_balance: string;
    date_registered: string;
    last_login: string;
  };
  timestamp: string;
  top_stocks: Array<{
    ticker_symbol: string;
    company_name: string;
    current_price: string;
    available_shares: number;
  }>;
  trader_data?: {
    total_orders: number;
    total_trades: number;
    portfolio: {
      quantity: number;
      average_purchase_price: string;
      total_investment: string;
    };
  };
  regulator_data?: {
    total_users: number;
    total_orders: number;
    total_trades: number;
    pending_suspicious_activities: number;
  };
  company_admin_data?: {
    company_name?: string;
    company_sector?: string;
    total_stocks_published?: number;
    disclosures_count?: number;
    dividends_count?: number;
    error?: string;
  };
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private apiUrl = 'http://127.0.0.1:8000/api/stocks/dashboard/';  // Adjust as needed

  constructor(private http: HttpClient) { }

  getDashboardData(): Observable<DashboardResponse> {
    return this.http.get<DashboardResponse>(this.apiUrl);
  }
}
