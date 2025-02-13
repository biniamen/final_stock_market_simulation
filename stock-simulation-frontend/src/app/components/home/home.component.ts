// src/app/components/home/home.component.ts

import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subscription, interval } from 'rxjs';
import { PageEvent } from '@angular/material/paginator';
import { ITransactionAuditTrail, DetailsObject } from '../../models/transaction-audit.model'; // Adjust the path as necessary

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy {
  // Dashboard Variables
  dashboardData: any = {};
  isLoading = false;
  error = '';
  private refreshSub?: Subscription;

  // Audit Trails Variables
  auditDisplayData: ITransactionAuditTrail[] = [];
  auditRawData: ITransactionAuditTrail[] = [];
  auditIsLoading = false;
  auditError = '';
  auditTotalRecords = 0;
  auditPageSize = 5;
  auditCurrentPage = 0;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchDashboard();
    this.fetchAuditTrails();

    // Optional auto-refresh every 60s for dashboard and audit trails
    this.refreshSub = interval(60000).subscribe(() => {
      this.fetchDashboard();
      this.fetchAuditTrails();
    });
  }

  ngOnDestroy(): void {
    if (this.refreshSub) {
      this.refreshSub.unsubscribe();
    }
  }

  // ------------------ Dashboard Fetch -------------------
  fetchDashboard(): void {
    this.isLoading = true;
    this.error = '';

    // Call the final extended dashboard endpoint
    this.http.get<any>('http://localhost:8000/api/stocks/extended-dashboard/')
      .subscribe({
        next: data => {
          this.isLoading = false;
          this.dashboardData = data;
        },
        error: err => {
          this.isLoading = false;
          this.error = 'Failed to load dashboard.';
          console.error('Dashboard error:', err);
        }
      });
  }

  // ------------------ Audit Trails Fetch -------------------
  fetchAuditTrails(): void {
    this.auditIsLoading = true;
    this.auditError = '';

    this.http.get<ITransactionAuditTrail[]>('http://localhost:8000/api/stocks/audit-trails/')
      .subscribe({
        next: data => {
          this.auditRawData = data;
          this.auditTotalRecords = data.length;
          this.auditCurrentPage = 0; // Reset to first page
          this.updateAuditDisplayData();
          this.auditIsLoading = false;
        },
        error: err => {
          console.error('Error fetching audit trails:', err);
          this.auditError = 'Failed to load audit trails.';
          this.auditIsLoading = false;
        }
      });
  }

  /**
   * Updates the subset of audit data based on the current page and page size.
   */
  updateAuditDisplayData(): void {
    const startIndex = this.auditCurrentPage * this.auditPageSize;
    const endIndex = startIndex + this.auditPageSize;
    this.auditDisplayData = this.auditRawData.slice(startIndex, endIndex);
  }

  /**
   * Handles page changes for audit trails pagination.
   */
  onAuditPageChange(event: PageEvent): void {
    this.auditPageSize = event.pageSize;
    this.auditCurrentPage = event.pageIndex;
    this.updateAuditDisplayData();
  }

  /**
   * Check if 'details' is an object (so we can list each key-value pair).
   */
  isDetailsObject(details: string | DetailsObject | undefined): details is DetailsObject {
    return details !== null && typeof details === 'object';
  }

  /**
   * Convert the details object to a list of key/value pairs for easy display.
   */
  getAuditDetailKeyValuePairs(details: string | DetailsObject): { key: string; value: any }[] {
    if (typeof details === 'string') {
      return [{ key: 'Details', value: details }];
    }
    // Convert each field in the object:
    return Object.entries(details).map(([key, value]) => ({
      key: this.formatKey(key),
      value
    }));
  }

  private formatKey(key: string): string {
    // e.g., buyer_id -> Buyer Id
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }

  /**
   * Determines whether to display the "Highest Profit Traders" section.
   */
  shouldDisplayHighestProfitTraders(): boolean {
    if (!this.dashboardData || !this.dashboardData.common_data) return false;
    const traders = this.dashboardData.common_data.highest_profit_traders;
    if (!traders || traders.length === 0) return false;
    // Check if at least one trader has profit_balance_etb > 0
    return traders.some((trader: any) => parseFloat(trader.profit_balance_etb) > 0);
  }

  /**
   * Determines whether to display the sum of transaction fees.
   */
  shouldDisplayTransactionFees(): boolean {
    if (!this.dashboardData || !this.dashboardData.common_data) return false;
    const role = this.dashboardData.user_info?.role;
    return role === 'regulator' && this.dashboardData.common_data.total_transaction_fees_etb;
  }

  /**
   * Determines whether to display the "Highest Dividend Ratio Companies" section.
   */
  shouldDisplayHighestDividendRatioCompanies(): boolean {
    if (!this.dashboardData || !this.dashboardData.common_data) return false;
    const companies = this.dashboardData.common_data.highest_dividend_ratio_companies;
    return companies && companies.length > 0;
  }
}
