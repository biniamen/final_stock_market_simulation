import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { StockService } from 'src/app/services/stock.service';

@Component({
  selector: 'app-publish-stock',
  templateUrl: './publish-stock.component.html',
  styleUrls: ['./publish-stock.component.css'],
})
export class PublishStockComponent implements OnInit {
  publishStockForm: FormGroup;
  publishedStock: any = null;
  companyId = 1; // Replace with the logged-in company admin's company ID

  constructor(
    private fb: FormBuilder,
    private stockService: StockService,
    private snackBar: MatSnackBar
  ) {
    this.publishStockForm = this.fb.group({
      company: [this.companyId, Validators.required],
      ticker_symbol: ['', [Validators.required, Validators.maxLength(10)]],
      total_shares: ['', [Validators.required, Validators.min(1)]],
      current_price: ['', [Validators.required, Validators.min(0.01)]],
      available_shares: ['', [Validators.required, Validators.min(1)]],
      max_trader_buy_limit: ['', [Validators.required, Validators.min(1)]],
    });
  }

  ngOnInit(): void {
    this.loadPublishedStock();
  }

  loadPublishedStock(): void {
    this.stockService.getPublishedStock(this.companyId).subscribe(
      (data) => {
        if (data.length > 0) {
          this.publishedStock = data[0];
        }
      },
      (error) => {
        console.error('Error loading published stock', error);
      }
    );
  }

  publishStock(): void {
    if (this.publishStockForm.invalid) {
      this.snackBar.open('Please fill out all required fields', 'Close', {
        duration: 3000,
      });
      return;
    }

    this.stockService.publishStock(this.publishStockForm.value).subscribe(
      (response) => {
        this.snackBar.open('Stock published successfully!', 'Close', {
          duration: 3000,
        });
        this.publishedStock = response;
        this.publishStockForm.reset();
      },
      (error) => {
        console.error('Error publishing stock', error);
        this.snackBar.open('Failed to publish stock', 'Close', {
          duration: 3000,
        });
      }
    );
  }
}
