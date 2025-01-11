import { Component, OnInit } from '@angular/core';
import { UserService } from '../../services/user.service';
import { UsersPortfolio } from '../../models/portfolio.model';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-user-portfolio',
  templateUrl: './user-portfolio.component.html',
  styleUrls: ['./user-portfolio.component.css'],
})
export class UserPortfolioComponent implements OnInit {
  portfolio: UsersPortfolio | null = null;
  isLoading: boolean = true;
  error: string = '';

  constructor(
    private userService: UserService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.fetchPortfolio();
  }

  fetchPortfolio(): void {
    const currentUserId = this.getCurrentUserId(); // Implement this method based on your auth logic

    if (!currentUserId) {
      this.error = 'User not authenticated.';
      this.isLoading = false;
      return;
    }

    this.userService.getUserPortfolio(currentUserId).subscribe({
      next: (data: UsersPortfolio) => {
        // Adjust profit balance if account_balance exceeds 10,000
        if (data.account_balance > 10000) {
          data.profit_balance = data.account_balance - 10000;
        }
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

  getProfitBalance(): string {
    if (this.portfolio) {
      return this.portfolio.profit_balance.toFixed(2);
    }
    return '0.00';
  }
}
