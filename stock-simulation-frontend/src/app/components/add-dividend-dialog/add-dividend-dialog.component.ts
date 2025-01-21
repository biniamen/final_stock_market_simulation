import { Component, OnInit, Inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { HttpClient, HttpHeaders } from '@angular/common/http';

interface Dividend {
  id: number;
  company: number;
  budget_year: number;
  dividend_ratio: string;
  total_dividend_amount: string;
  status: string;
  // ...
}

@Component({
  selector: 'app-add-dividend-dialog',
  templateUrl: './add-dividend-dialog.component.html',
  styleUrls: ['./add-dividend-dialog.component.css']
})
export class AddDividendDialogComponent implements OnInit {
  dividendForm!: FormGroup;

  totalWeightedValue: number = 0;
  currentYear: number = new Date().getFullYear();

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<AddDividendDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private toastr: ToastrService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    // Grab data passed in from the parent
    this.totalWeightedValue = this.data.totalWeightedValue || 0;

    // Build the form
    this.dividendForm = this.fb.group({
      totalDividendValue: ['', [Validators.required, Validators.min(0.01)]],
      dividendRatio: [{ value: '', disabled: true }],
      budgetYear: [{ value: this.currentYear, disabled: true }]
    });

    // Whenever the user changes totalDividendValue, compute ratio locally
    this.dividendForm.get('totalDividendValue')?.valueChanges.subscribe(val => {
      if (val && this.totalWeightedValue > 0) {
        const ratio = (+val / this.totalWeightedValue).toFixed(4);
        this.dividendForm.get('dividendRatio')?.setValue(ratio);
      } else {
        this.dividendForm.get('dividendRatio')?.setValue('');
      }
    });
  }

  // add-dividend-dialog.component.ts

onSubmit(): void {
  if (this.dividendForm.invalid) return;

  const payload = {
    company: this.data.companyId,
    budget_year: this.currentYear,
    total_dividend_amount: parseFloat(this.dividendForm.get('totalDividendValue')?.value),
    sum_weighted_value: this.data.totalWeightedValue,
    holdingsData: this.data.holdingsData
  };

  const accessToken = localStorage.getItem('access_token');
  if (!accessToken) {
    this.toastr.error('No access token found. Please log in.', 'Error');
    return;
  }

  const headers = new HttpHeaders({
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  });

  this.http
    .post('http://127.0.0.1:8000/api/stocks/dividends/', payload, { headers })
    .subscribe({
      next: (resp) => {
        this.toastr.success('Dividend created & disbursed!', 'Success');
        this.dialogRef.close(true);
      },
      error: (err) => {
        // If the error includes "already exists" we show your custom message
        if (err.error && err.error.non_field_errors) {
          const msg = err.error.non_field_errors[0];
          if (msg.includes('already exists')) {
            this.toastr.error('Already added for this budget year', 'Error');
          } else {
            this.toastr.error(msg, 'Error');
          }
        } else {
          this.toastr.error('Failed to create dividend.', 'Error');
        }
      }
    });
}


  onCancel(): void {
    this.dialogRef.close(false);
  }
}
