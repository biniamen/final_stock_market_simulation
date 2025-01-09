// src/app/components/user-portfolio/user-portfolio.component.ts

import { Component, OnInit } from '@angular/core';
import { UserService } from '../../services/user.service';
import { UsersPortfolio } from '../../models/portfolio.model';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-user-portfolio',
  templateUrl: './user-portfolio.component.html',
  styleUrls: ['./user-portfolio.component.scss']
})
export class UserPortfolioComponent implements OnInit {

  portfolio: UsersPortfolio | null = null;
  isLoading: boolean = true;
  error: string = '';

  constructor(
    private userService: UserService,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit(): void {
    this.fetchPortfolio();
  }

  /**
   * Fetches the current user's portfolio.
   * Assumes that you have a method to get the current user's ID.
   */
  fetchPortfolio(): void {
    const currentUserId = this.getCurrentUserId(); // Implement this method based on your auth logic

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
        this.error = err.error.detail || 'An error occurred while fetching the portfolio.';
        this.isLoading = false;
        this.snackBar.open(this.error, 'Close', { duration: 5000 });
      }
    });
  }

  /**
   * Retrieves the current user's ID.
   * Implement this based on how your authentication is set up.
   * For example, if using JWT, decode the token to get the user ID.
   */
  getCurrentUserId(): number | null {
    // Example implementation assuming JWT stored in localStorage
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    // Decode JWT to extract user ID
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.user_id || null; // Adjust based on your token's payload
    } catch (e) {
      console.error('Invalid token format:', e);
      return null;
    }
  }

  /**
   * Calculates the remaining investment.
   * Adjust the calculation based on your business logic.
   */
  getRemainingInvestment(): string {
    if (this.portfolio) {
      const totalInvestment = parseFloat(this.portfolio.total_investment);
      const investedAmount = parseFloat(this.portfolio.average_purchase_price) * this.portfolio.quantity;
      const remaining = totalInvestment - investedAmount;
      return remaining.toFixed(2);
    }
    return '0.00';
  }

}
