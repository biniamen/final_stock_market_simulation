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

    this.stockForm = this.fb.group({
      ticker_symbol: [{ value: '', disabled: true }, Validators.required],
      total_shares: [0, [Validators.required, Validators.min(1)]],
      current_price: [0, [Validators.required, Validators.min(0.01)]],
      available_shares: [{ value: 0, disabled: true }, Validators.required],
      max_trader_buy_limit: [0, [Validators.required, Validators.min(1)]],
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
        const stockForCompany = stocks.find(stock => stock.company === parseInt(this.companyId || '', 10));
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
    const words = companyName.split(/\s+/);
    let baseTicker = words.map(word => word[0].toUpperCase()).join('').slice(0, 3);

    this.http.get<any[]>(`http://127.0.0.1:8000/api/stocks/stocks/`).subscribe(
      (stocks) => {
        let ticker = baseTicker;
        let counter = 1;

        while (stocks.some(stock => stock.ticker_symbol === ticker)) {
          ticker = `${baseTicker}${counter}`;
          counter++;
        }

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
    this.stockForm.get('ticker_symbol')?.setValue(this.tickerSymbol);
    this.stockForm.get('available_shares')?.setValue(0);
  }

  onTotalSharesChange(): void {
    const totalShares = this.stockForm.get('total_shares')?.value || 0;
    this.stockForm.get('available_shares')?.setValue(totalShares);
  }

  setupMaxTraderBuyLimitValidation(): void {
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
    if (field === 'max_trader_buy_limit') {
      const maxLimit = Math.floor(this.stockForm.get('total_shares')?.value * 0.25 || 0);
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
    if (this.formErrors[field] && this.formErrors[field].length > 0) {
      return this.formErrors[field][0];
    }
    return null;
  }
}
