import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-add-stock',
  templateUrl: './add-stock.component.html',
  styleUrls: ['./add-stock.component.css']
})
export class AddStockComponent implements OnInit {
  stockForm: FormGroup;
  companyName: string | null = '';
  companyId: string | null = '';
  tickerSymbol: string = '';
  formErrors: { [key: string]: string[] } = {};
  companyDetailsLoaded: boolean = false;
  stockExists: boolean = false;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private toastr: ToastrService
  ) {
    this.companyId = localStorage.getItem('company_id'); // Get the company ID from local storage

    // Remove default '0' values; start with empty strings
    this.stockForm = this.fb.group({
      // Keep ticker_symbol disabled; will be auto-populated
      ticker_symbol: [{ value: '', disabled: true }, Validators.required],
      total_shares: ['', [Validators.required, Validators.min(1)]],
      current_price: ['', [Validators.required, Validators.min(0.01)]],
      available_shares: [{ value: '', disabled: true }, Validators.required],
      max_trader_buy_limit: ['', [Validators.required, Validators.min(1)]],
    });
  }

  ngOnInit(): void {
    if (this.companyId) {
      this.fetchCompanyDetails();
      this.checkIfStockExists();
    } else {
      this.toastr.error('Company ID not found in local storage.');
    }
    this.setupMaxTraderBuyLimitValidation();
  }

  fetchCompanyDetails(): void {
    this.http.get<any>(`http://127.0.0.1:8000/api/stocks/companies/${this.companyId}/`).subscribe(
      (response) => {
        this.companyName = response.company_name;
        // Generate a 4-letter ticker from the first letters of the company name
        this.tickerSymbol = this.generateTickerSymbol(response.company_name);
        this.stockForm.get('ticker_symbol')?.setValue(this.tickerSymbol);
        this.companyDetailsLoaded = true;
      },
      (error) => {
        console.error('Error fetching company details:', error);
        this.toastr.error('Failed to fetch company details. Please try again.');
      }
    );
  }

  checkIfStockExists(): void {
    this.http.get<any[]>(`http://127.0.0.1:8000/api/stocks/stocks/`).subscribe(
      (stocks) => {
        const stockForCompany = stocks.find(
          (stock) => stock.company === parseInt(this.companyId || '', 10)
        );
        if (stockForCompany) {
          this.stockExists = true;
          this.toastr.warning('A stock already exists for this company. You cannot add another one.');
        }
      },
      (error) => {
        console.error('Error checking existing stock:', error);
        this.toastr.error('Failed to verify existing stock.');
      }
    );
  }

  generateTickerSymbol(companyName: string): string {
    // Take up to 4 letters from each word's first letter (if multiple words).
    // Example: "Blue Nile Insurance" -> baseTicker = "BNI" => slice(0,4) => "BNI"
    const words = companyName.split(/\s+/);
    let baseTicker = words.map(word => word[0].toUpperCase()).join('').slice(0, 4);

    // Check uniqueness against existing stocks
    this.http.get<any[]>(`http://127.0.0.1:8000/api/stocks/stocks/`).subscribe(
      (stocks) => {
        let ticker = baseTicker;
        let counter = 1;

        // If ticker already exists, append a counter (e.g., ABC1, ABC2, ...)
        while (stocks.some(stock => stock.ticker_symbol === ticker)) {
          ticker = `${baseTicker}${counter}`;
          counter++;
        }

        // Update form and class property
        this.tickerSymbol = ticker;
        this.stockForm.get('ticker_symbol')?.setValue(this.tickerSymbol);
      },
      (error) => {
        console.error('Error checking ticker symbol uniqueness:', error);
        this.toastr.error('Failed to verify ticker symbol uniqueness.');
      }
    );
    return baseTicker;
  }

  onSubmit(): void {
    if (this.stockForm.valid) {
      const payload = {
        company: this.companyId,
        ticker_symbol: this.tickerSymbol,
        total_shares: this.stockForm.value.total_shares,
        current_price: this.stockForm.value.current_price,
        // available_shares = total_shares by default
        available_shares: this.stockForm.value.total_shares,
        max_trader_buy_limit: this.stockForm.value.max_trader_buy_limit,
      };

      this.http.post('http://127.0.0.1:8000/api/stocks/stocks/', payload).subscribe(
        (response) => {
          this.toastr.success('Stock added successfully!');
          this.resetForm();
        },
        (error) => {
          if (error.status === 400 && error.error) {
            this.formErrors = error.error;
            this.toastr.error('Failed to add stock. Please check the form for errors.');
          } else {
            this.toastr.error('An unexpected error occurred. Please try again.');
          }
        }
      );
    }
  }

  resetForm(): void {
    this.stockForm.reset();
    this.formErrors = {};
    // Keep the newly generated ticker symbol
    this.stockForm.get('ticker_symbol')?.setValue(this.tickerSymbol);
    this.stockForm.get('available_shares')?.setValue('');
  }

  onTotalSharesChange(): void {
    // If blank or non-numeric, fallback to 0
    const totalShares = +this.stockForm.get('total_shares')?.value || 0;
    // Sync available_shares to total_shares
    this.stockForm.get('available_shares')?.setValue(totalShares);
  }

  setupMaxTraderBuyLimitValidation(): void {
    // Dynamically enforce max_trader_buy_limit <= 25% of total_shares
    this.stockForm.get('total_shares')?.valueChanges.subscribe(totalShares => {
      const maxLimitControl = this.stockForm.get('max_trader_buy_limit');
      if (maxLimitControl) {
        const maxLimit = Math.floor(totalShares * 0.25);
        maxLimitControl.setValidators([
          Validators.required,
          Validators.min(1),
          Validators.max(maxLimit),
        ]);
        maxLimitControl.updateValueAndValidity();
      }
      this.onTotalSharesChange();
    });
  }

  getErrorMessage(field: string): string | null {
    // Show custom error messages
    if (field === 'max_trader_buy_limit') {
      const totalShares = +this.stockForm.get('total_shares')?.value || 0;
      const maxLimit = Math.floor(totalShares * 0.25);

      if (this.stockForm.get(field)?.hasError('max')) {
        return `Max Trader Buy Limit cannot exceed 25% of Total Shares (${maxLimit}).`;
      }
      if (this.stockForm.get(field)?.hasError('required')) {
        return 'Max Trader Buy Limit is required.';
      }
      if (this.stockForm.get(field)?.hasError('min')) {
        return 'Max Trader Buy Limit must be at least 1.';
      }
    }
    // Show field-level errors from the backend if any
    if (this.formErrors[field] && this.formErrors[field].length > 0) {
      return this.formErrors[field][0];
    }
    return null;
  }
}
