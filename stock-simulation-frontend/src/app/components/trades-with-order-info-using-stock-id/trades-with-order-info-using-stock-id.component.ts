import { Component, OnInit, ViewChild } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';
import { MatDialog } from '@angular/material/dialog';

import { AddDividendDialogComponent } from '../add-dividend-dialog/add-dividend-dialog.component';

@Component({
  selector: 'app-trades-with-order-info-using-stock-id',
  templateUrl: './trades-with-order-info-using-stock-id.component.html',
  styleUrls: ['./trades-with-order-info-using-stock-id.component.css']
})
export class TradesWithOrderInfoUsingStockIDComponent implements OnInit {
  displayedColumns: string[] = [
    'id',
    'user_id',
    'username',
    'stock_symbol',
    'order_type',
    'price',
    'quantity',
    'transaction_fee',
    'total_buying_price',
    'weighted_value',
    'dividend_eligible',
    'trade_time'
  ];

  dataSource = new MatTableDataSource<any>([]);
  isLoading = true;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private http: HttpClient,
    private toastr: ToastrService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.fetchNetHoldings();
  }

  fetchNetHoldings(): void {
    const stockId = localStorage.getItem('stock_id');
    if (!stockId) {
      this.toastr.error('No stock_id found in localStorage.', 'Error');
      this.isLoading = false;
      return;
    }

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      this.isLoading = false;
      return;
    }

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    // Example endpoint: /api/stocks/<stock_id>/fifonet_holdings/
    const endpoint = `http://127.0.0.1:8000/api/stocks/stocks/${stockId}/fifonet_holdings/`;

    this.http.get<any[]>(endpoint, { headers }).subscribe({
      next: (data) => {
        // data is an array of leftover "Buy" trades (with quantity, weighted_value, etc.)
        this.dataSource.data = data.map(row => ({
          ...row,
          // ensure numeric conversions
          total_buying_price: parseFloat(row.total_buying_price),
          weighted_value: parseFloat(row.weighted_value)
        }));
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching FIFO net holdings:', err);
        if (err.status === 401) {
          this.toastr.error('Unauthorized access. Please log in again.', 'Error');
        } else if (err.status === 404) {
          this.toastr.error('Stock not found.', 'Error');
        } else {
          this.toastr.error('Failed to fetch trade records.', 'Error');
        }
        this.isLoading = false;
      }
    });
  }

  openAddDividendModal(): void {
    // compute sum of weighted_value
    const totalWeightedValue = this.dataSource.data.reduce(
      (acc: number, curr: any) => acc + curr.weighted_value,
      0
    );
    // You can figure out the real companyId from the stock or from localStorage
    const companyId = 1; // Hard-coded for demonstration

    this.dialog.open(AddDividendDialogComponent, {
      width: '800px',
      data: {
        totalWeightedValue,
        companyId,
        holdingsData: this.dataSource.data // pass the array to the dialog
      }
    }).afterClosed().subscribe(result => {
      if (result) {
        // If we returned something truthy from the dialog, maybe reload
        this.fetchNetHoldings();
      }
    });
  }

  exportToCSV(): void {
    // your CSV logic...
  }

  printTable(): void {
    // your Print logic...
  }
}
