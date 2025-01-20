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

  /**
   * Fetch net BUY holdings for the current stock
   * using the StockNetHoldingsView API (FIFO logic).
   */
  fetchNetHoldings(): void {
    const stockId = localStorage.getItem('stock_id');
    if (!stockId) {
      this.toastr.error('No stock_id found in localStorage.', 'Error');
      this.isLoading = false;
      return;
    }

    // Set up the request headers
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      this.isLoading = false;
      return;
    }

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    // API endpoint for FIFO net holdings
    const endpoint = `http://127.0.0.1:8000/api/stocks/stocks/${stockId}/fifonet_holdings/`;

    this.http.get<any[]>(endpoint, { headers }).subscribe({
      next: (data) => {
        // data is an array of final "Buy" trades with leftover quantities
        this.dataSource.data = data.map(row => ({
          ...row,
          // Ensure numeric fields are parsed to floats
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

  exportToCSV(): void {
    // ...same as your existing code...
  }

  printTable(): void {
    // ...same as your existing code...
  }

  /**
   * Opens the "Add Dividend" modal dialog.
   * Passes:
   *  1) totalWeightedValue (sum of weighted_value for all traders),
   *  2) the entire table data (so we can create distributions in the dialog).
   *  3) companyId (placeholder logic).
   */
  openAddDividendModal(): void {
    const totalWeightedValue = this.dataSource.data.reduce((acc: number, curr: any) => acc + curr.weighted_value, 0);
    const companyId = this.getCompanyIdFromStockId();

    // We also pass the entire data array for distribution creation
    const dialogRef = this.dialog.open(AddDividendDialogComponent, {
      width: '800px',
      data: {
        totalWeightedValue,
        companyId,
        holdingsData: this.dataSource.data // pass the array of holdings
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.toastr.success('Dividend added and auto-disbursed.', 'Success');
        // Optionally refetch net holdings or do other UI updates
        this.fetchNetHoldings();
      }
    });
  }

  getCompanyIdFromStockId(): number {
    // Same placeholder logic as before
    const stockId = localStorage.getItem('stock_id');
    if (!stockId) {
      this.toastr.error('No stock_id found in localStorage.', 'Error');
      return 0;
    }
    return 1; // Replace with real logic
  }
}
