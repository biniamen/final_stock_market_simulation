import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr'; // <-- Import Toastr

@Component({
  selector: 'app-stock-list',
  templateUrl: './stock-list.component.html',
  styleUrls: ['./stock-list.component.css'],
})
export class StockListComponent implements OnInit {
  @ViewChild('buyModal') buyModal!: TemplateRef<any>;
  @ViewChild('disclosureModal') disclosureModal!: TemplateRef<any>;
  @ViewChild(MatPaginator, { static: false }) paginator!: MatPaginator;
  @ViewChild(MatSort, { static: false }) sort!: MatSort;

  stocks: any[] = [];
  filteredStocks: any[] = [];
  selectedStock: any = null;
  disclosures: any[] = [];
  disclosureDataSource = new MatTableDataSource<any>();
  displayedColumns: string[] = ['id', 'type', 'year', 'description', 'file'];
  token: string | null = null;
  quantity: string = '';
  searchText: string = '';

  constructor(
    private http: HttpClient,
    public dialog: MatDialog,
    private toastr: ToastrService // <-- Inject Toastr
  ) {}

  ngOnInit(): void {
    this.token = localStorage.getItem('access_token');
    if (!this.token) {
      alert('You must log in to access this page.');
      return;
    }
    this.fetchStocks();
  }

  ngAfterViewInit(): void {
    // Attach paginator & sort after the view is initialized
    this.disclosureDataSource.paginator = this.paginator;
    this.disclosureDataSource.sort = this.sort;
  }

  fetchStocks(): void {
    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
    });

    this.http.get<any[]>('http://127.0.0.1:8000/api/stocks/stocks/', { headers })
      .subscribe({
        next: (data) => {
          // Show only stocks that have shares available
          this.stocks = data.filter((stock) => stock.available_shares > 0);
          this.filteredStocks = [...this.stocks];
        },
        error: (err) => {
          console.error('Error fetching stocks:', err);
          if (err.status === 401) {
            alert('Authentication failed. Please log in again.');
          } else if (err.status === 0) {
            alert('Cannot connect to the server. Check if the backend is running & CORS is configured.');
          } else {
            alert(`Unexpected error: ${err.message}`);
          }
        },
      });
  }

  // ---- Buy Modal Logic ----
  openBuyModal(stock: any): void {
    this.selectedStock = stock;
    this.quantity = '';
    this.dialog.open(this.buyModal, { width: '500px', height: 'auto' });
  }

  // stock-list.component.ts

placeOrder(): void {
  // Validate quantity
  const quantityValue = parseInt(this.quantity, 10);
  if (isNaN(quantityValue) || quantityValue <= 0) {
    this.toastr.error('Please enter a valid quantity.', 'Validation Error');
    return;
  }

  if (!this.selectedStock) {
    this.toastr.error('No stock selected.', 'Validation Error');
    return;
  }

  // Check user login
  const userId = localStorage.getItem('user_id');
  if (!userId) {
    this.toastr.error('User not logged in. Please log in first.', 'Authentication Error');
    return;
  }

  const payload = {
    stock_id: this.selectedStock.id,
    quantity: quantityValue,
  };

  const headers = new HttpHeaders({
    Authorization: `Bearer ${this.token}`,
    'Content-Type': 'application/json',
  });

  // Call the direct_buy endpoint
  this.http.post('http://127.0.0.1:8000/api/stocks/direct_buy/', payload, { headers })
    .subscribe({
      next: (response: any) => {
        const successMessage = response.message
          ? response.message
          : 'Order placed successfully!';

        this.toastr.success(`${successMessage} Total deducted: ${response.total_deducted}`, 'Buy Order');

        if (response.updated_balance !== undefined) {
          localStorage.setItem('account_balance', response.updated_balance.toString());
        }

        if (response.profit_balance !== undefined) {
          localStorage.setItem('profit_balance', response.profit_balance.toString());
        }

        this.dialog.closeAll();
        this.fetchStocks();
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error placing order:', err);

        let errorMessage = 'Failed to place the order.';

        if (err.error && err.error.detail) {
          errorMessage = err.error.detail;
        } 
        // Optionally, handle more specific error structures
        else if (err.error && typeof err.error === 'object') {
          const fieldErrors = [];
          for (const key of Object.keys(err.error)) {
            fieldErrors.push(`${key}: ${err.error[key]}`);
          }
          if (fieldErrors.length > 0) {
            errorMessage = fieldErrors.join('\n');
          }
        }

        this.toastr.error(errorMessage, 'Buy Order Error');
      }
    });
}

  // ---- Disclosures Modal Logic ----
  openDisclosureModal(companyId: number): void {
    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
    });

    this.http
      .get<any[]>(`http://127.0.0.1:8000/api/stocks/company/${companyId}/disclosures/`, { headers })
      .subscribe({
        next: (data) => {
          this.disclosures = data;
          this.disclosureDataSource = new MatTableDataSource(this.disclosures);
          this.disclosureDataSource.paginator = this.paginator;
          this.disclosureDataSource.sort = this.sort;
          this.dialog.open(this.disclosureModal, { width: '800px', height: 'auto' });
        },
        error: (err) => {
          console.error('Error fetching disclosures:', err);
          this.toastr.error('Failed to fetch disclosures.', 'Error');
        },
      });
  }

  // ---- Search + Filtering ----
  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value.trim().toLowerCase();
    this.disclosureDataSource.filter = filterValue;

    if (this.disclosureDataSource.paginator) {
      this.disclosureDataSource.paginator.firstPage();
    }
  }

  hoverEffect(enable: boolean, stockId: number): void {
    const card = document.querySelector(`#stock-card-${stockId}`) as HTMLElement;
    if (card) {
      card.style.boxShadow = enable ? '0px 4px 10px rgba(0, 0, 0, 0.2)' : 'none';
      card.style.transform = enable ? 'scale(1.05)' : 'scale(1)';
      card.style.transition = 'transform 0.3s, box-shadow 0.3s';
    }
  }

  filterStocks(): void {
    this.filteredStocks = this.stocks.filter((stock) =>
      stock.ticker_symbol.toLowerCase().includes(this.searchText.toLowerCase())
    );
  }

  closeModal(): void {
    this.dialog.closeAll();
  }
}
