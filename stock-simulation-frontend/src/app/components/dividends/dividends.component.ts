import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';
import { Observable } from 'rxjs';

import { DividendService, DividendDetailedHolding } from '../../services/dividend.service';

@Component({
  selector: 'app-dividends',
  templateUrl: './dividends.component.html',
  styleUrls: ['./dividends.component.css']
})
export class DividendsComponent implements OnInit {
  // Table setup
  displayedColumns: string[] = [];
  dataSource: MatTableDataSource<DividendDetailedHolding> = new MatTableDataSource();

  // UI states
  isLoading: boolean = false;
  error: string = '';

  // User info
  userRole: string = '';  // We'll get this from localStorage
  username: string = '';  // If you store the username, you can also retrieve it

  // Filters
  budgetYear: string = '';

  // Material references
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private dividendService: DividendService,
    private router: Router,
    private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    // 1) Retrieve userRole directly from localStorage (or another stored location)
    this.userRole = localStorage.getItem('role') || ''; 
    // If you store the username in localStorage as well:
    this.username = localStorage.getItem('username') || '';

    if (!this.userRole) {
      this.toastr.error('You are not logged in or role is missing.', 'Authentication Error');
      this.router.navigate(['/login']);
      return;
    }

    // 2) Configure table columns based on user role
    this.initializeColumns();

    // 3) Fetch dividends from the appropriate method
    this.fetchDividends();
  }

  /**
   * Decide which columns to show based on user role.
   */
  private initializeColumns(): void {
    if (this.userRole === 'regulator') {
      this.displayedColumns = [
        'dividend_id',
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
        'trade_time',
        'ratio_at_creation',
        'paid_dividend',
        'created_at'
      ];
    } else if (this.userRole === 'trader') {
      this.displayedColumns = [
        'dividend_id',
        'stock_symbol',
        'order_type',
        'price',
        'quantity',
        'transaction_fee',
        'total_buying_price',
        'weighted_value',
        'dividend_eligible',
        'trade_time',
        'ratio_at_creation',
        'paid_dividend',
        'created_at'
      ];
    } else {
      this.toastr.error('Unauthorized role.', 'Error');
      this.router.navigate(['/unauthorized']);
    }
  }

  /**
   * Fetch dividends based on user role and budget year filter.
   */
  private fetchDividends(): void {
    this.isLoading = true;
    this.error = '';

    let fetchObservable: Observable<DividendDetailedHolding[]>;

    if (this.userRole === 'regulator') {
      fetchObservable = this.dividendService.getRegulatorDividends(this.budgetYear);
    } else if (this.userRole === 'trader') {
      fetchObservable = this.dividendService.getTraderDividends(this.budgetYear);
    } else {
      // If the role is something else, do nothing
      this.toastr.error('Unauthorized role.', 'Error');
      this.isLoading = false;
      return;
    }

    fetchObservable.subscribe({
      next: (data: DividendDetailedHolding[]) => {
        this.dataSource = new MatTableDataSource(data);
        this.initializeTable();
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Error fetching dividends:', err);
        this.error = 'Failed to load dividends. Please try again later.';
        this.toastr.error(this.error, 'Error');
        this.isLoading = false;
      }
    });
  }

  /**
   * Initialize table pagination and sorting.
   */
  private initializeTable(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  /**
   * Applies a search filter to the data table.
   * @param event The input event from the search box
   */
  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  /**
   * Triggered when the budget year filter changes, refetch data.
   */
  onBudgetYearChange(): void {
    this.fetchDividends();
  }

  /**
   * Logs out the user by clearing localStorage items and redirecting to login.
   */
  onLogout(): void {
    // If your existing AuthService has a logout method, you can call it:
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('lastLogin');
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');

    this.toastr.success('You have been logged out.', 'Logout Successful');
    this.router.navigate(['/login']);
  }
}
