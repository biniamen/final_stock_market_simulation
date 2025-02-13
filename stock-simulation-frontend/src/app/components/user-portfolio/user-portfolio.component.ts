// src/app/components/user-portfolio/user-portfolio.component.ts

import { Component, OnInit, TemplateRef } from '@angular/core';
import { UserService } from '../../services/user.service';
import { UsersPortfolio } from '../../models/portfolio.model';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import Decimal from 'decimal.js'; // Correct default import

@Component({
  selector: 'app-user-portfolio',
  templateUrl: './user-portfolio.component.html',
  styleUrls: ['./user-portfolio.component.css'], // Assuming you're using SCSS
})
export class UserPortfolioComponent implements OnInit {
  portfolio: UsersPortfolio | null = null;
  isLoading: boolean = true;
  error: string = '';
  
  constructor(
    private userService: UserService,
    private snackBar: MatSnackBar,
    public dialog: MatDialog // Inject MatDialog
  ) {}

  ngOnInit(): void {
    this.fetchPortfolio();
  }

  /**
   * Fetches the user's portfolio from the backend.
   */
  fetchPortfolio(): void {
    const currentUserId = this.getCurrentUserId(); // Implement based on your auth logic

    if (!currentUserId) {
      this.error = 'User not authenticated.';
      this.isLoading = false;
      return;
    }

    this.userService.getUserPortfolio(currentUserId).subscribe({
      next: (data: UsersPortfolio) => {
        this.portfolio = data;
        this.isLoading = false;
      },
      error: (err: any) => {
        this.error =
          err.error.detail ||
          'An error occurred while fetching the portfolio.';
        this.isLoading = false;
        this.snackBar.open(this.error, 'Close', { duration: 5000 });
      },
    });
  }

  /**
   * Retrieves the current user's ID from the JWT token.
   */
  getCurrentUserId(): number | null {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.user_id || null;
    } catch (e) {
      console.error('Invalid token format:', e);
      return null;
    }
  }

  /**
   * Formats the profit balance to two decimal places.
   */
  getProfitBalance(): string {
    if (this.portfolio) {
      return parseFloat(this.portfolio.profit_balance.toString()).toFixed(2);
    }
    return '0.00';
  }

  /**
   * Capitalizes profit by adding profit_balance to account_balance and resetting profit_balance.
   */
  capitalizeProfit(): void {
    if (!this.portfolio || this.portfolio.profit_balance <= 0) {
      this.snackBar.open('No profit available to capitalize.', 'Close', { duration: 5000 });
      return;
    }

    this.userService.capitalizeProfit().subscribe({
      next: (data) => {
        this.snackBar.open('Profit capitalized successfully.', 'Close', { duration: 5000 });

        if (this.portfolio) {
          // Add entire profit_balance to account_balance
          this.portfolio.account_balance = new Decimal(this.portfolio.account_balance)
            .plus(new Decimal(this.portfolio.profit_balance))
            .toDecimalPlaces(2)
            .toNumber();

          // Reset profit_balance to 0
          this.portfolio.profit_balance = 0;
        }

        // Optionally, refresh the portfolio data
        this.fetchPortfolio();
      },
      error: (err: any) => {
        this.error =
          err.error.detail ||
          'An error occurred while capitalizing profit.';
        this.snackBar.open(this.error, 'Close', { duration: 5000 });
      },
    });
  }

  /**
   * Opens the Withdraw Profit modal.
   */
  openWithdrawModal(withdrawModal: TemplateRef<any>): void {
    if (!this.portfolio || this.portfolio.profit_balance <= 0) {
      this.snackBar.open('No profit available to withdraw.', 'Close', { duration: 5000 });
      return;
    }

    this.dialog.open(withdrawModal, {
      width: '400px',
    });
  }

  /**
   * Confirms the withdrawal by setting profit_balance to 0.
   */
  confirmWithdraw(): void {
    this.userService.withdrawProfit().subscribe({
      next: (data) => {
        this.snackBar.open('Profit withdrawn successfully.', 'Close', { duration: 5000 });

        if (this.portfolio) {
          // Reset profit_balance to 0 after withdrawal
          this.portfolio.profit_balance = 0;
        }

        // Optionally, refresh the portfolio data
        this.fetchPortfolio();

        // Close the dialog
        this.dialog.closeAll();
      },
      error: (err: any) => {
        this.error =
          err.error.detail ||
          'An error occurred while withdrawing profit.';
        this.snackBar.open(this.error, 'Close', { duration: 5000 });
      },
    });
  }
}
