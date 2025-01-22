import { Component, OnInit, ViewChild } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-dividend-detailed-holdings',
  templateUrl: './dividend-detailed-holdings.component.html',
  styleUrls: ['./dividend-detailed-holdings.component.css']
})
export class DividendDetailedHoldingsComponent implements OnInit {
  displayedColumns: string[] = [
    'username',
    'stock_symbol',
    'quantity',
    'total_buying_price',
    'weighted_value',
    'paid_dividend',
    'budget_year',
    'ratio_at_creation',
    'trade_time'
  ];

  dataSource = new MatTableDataSource<any>([]);
  isLoading = true;
  searchKey = '';

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private http: HttpClient,
    private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    this.fetchDetailedHoldings();
  }

  /**
   * Fetches dividend-related data filtered by company_id and budget_year.
   */
  fetchDetailedHoldings(): void {
    const companyId = localStorage.getItem('company_id') || '1';
    const budgetYear = '2025';

    const endpoint = `http://127.0.0.1:8000/api/stocks/detailed-holdings/?company_id=${companyId}&budget_year=${budgetYear}`;
    const accessToken = localStorage.getItem('access_token');

    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      this.isLoading = false;
      return;
    }

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    this.http.get<any[]>(endpoint, { headers }).subscribe({
      next: (data) => {
        this.dataSource.data = data.map(row => ({
          ...row,
          total_buying_price: parseFloat(row.total_buying_price),
          weighted_value: parseFloat(row.weighted_value),
          paid_dividend: parseFloat(row.paid_dividend),
        }));
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching dividend detailed holdings:', err);
        this.toastr.error('Failed to fetch records.', 'Error');
        this.isLoading = false;
      }
    });
  }

  /**
   * Filters the dataSource based on the search key.
   */
  applyFilter(): void {
    this.dataSource.filter = this.searchKey.trim().toLowerCase();
  }

  /**
   * Resets the search filter.
   */
  clearSearch(): void {
    this.searchKey = '';
    this.applyFilter();
  }
}
